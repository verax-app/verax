import time
import threading
import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

CACHE_TTL       = 120
HALF_LIFE_HOURS = 36      # news stays relevant ~36 h; 24 h was cutting off quality day-old content
MAX_ARTICLES    = 500
TREND_THRESHOLD = 0.25    # slightly more inclusive than 0.30 — catches story clusters better
TREND_WINDOW_H  = 24
REBUILD_GROWTH  = 1.20
TEXT_CHARS      = 2000
MMR_LAMBDA      = 0.70    # 70% relevance, 30% novelty — MMR tuning knob

# Partial credit for topically adjacent categories — avoids hard 0/1 binary penalty.
_CATEGORY_AFFINITY: dict[frozenset, float] = {
    frozenset({"tech",        "science"}):      0.6,
    frozenset({"tech",        "gaming"}):       0.5,
    frozenset({"tech",        "business"}):     0.4,
    frozenset({"tech",        "crypto"}):       0.5,
    frozenset({"science",     "health"}):       0.5,
    frozenset({"science",     "environment"}):  0.4,
    frozenset({"health",      "environment"}):  0.3,
    frozenset({"business",    "politics"}):     0.4,
    frozenset({"business",    "crypto"}):       0.5,
    frozenset({"sports",      "entertainment"}):0.3,
    frozenset({"gaming",      "entertainment"}):0.4,
    frozenset({"politics",    "environment"}):  0.3,
}


def _cat_score(cat: str, preferred: list[str]) -> float:
    if not preferred:
        return 0.0
    if cat in preferred:
        return 1.0
    return max(
        (_CATEGORY_AFFINITY.get(frozenset({cat, p}), 0.0) for p in preferred),
        default=0.0,
    )


def _corpus(row: pd.Series) -> str:
    title = row.get("title", "") or ""
    parts = [
        title, title, title,   # 3× repetition raises TF-IDF weight for the most signal-dense field
        row.get("rss_summary", "") or "",
        (row.get("text", "") or "")[:TEXT_CHARS],
        row.get("source_tags", "") or "",
        row.get("tags", "") or "",
        row.get("category", "") or "",
        row.get("region", "") or "",
    ]
    return " ".join(p for p in parts if p)


class ArticleRecommender:
    def __init__(self) -> None:
        self._lock        = threading.Lock()
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix      = None
        self._df: pd.DataFrame | None = None
        self._built_at    = 0.0

    def _needs_rebuild(self, n: int) -> bool:
        if self._df is None or self._matrix is None:
            return True
        if time.monotonic() - self._built_at > CACHE_TTL:
            return True
        if n > len(self._df) * REBUILD_GROWTH:
            return True
        return False

    def _rebuild(self, articles: list) -> None:
        if not articles:
            return
        rows = [
            {
                "id":           a.id,
                "title":        a.title                          or "",
                "rss_summary":  getattr(a, "rss_summary", None) or "",
                "text":         a.text                          or "",
                "source_tags":  getattr(a, "source_tags", None) or "",
                "tags":         a.tags                          or "",
                "category":     a.category                      or "general",
                "region":       a.region                        or "global",
                "author":       getattr(a, "author", None)      or "",
                "source_name":  a.source_name                   or "",
                "published_at": a.published_at or a.created_at,
            }
            for a in articles
        ]
        df = pd.DataFrame(rows)
        df["corpus"] = df.apply(_corpus, axis=1)

        vectorizer = TfidfVectorizer(
            max_features=10_000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
            min_df=1,
        )
        matrix = vectorizer.fit_transform(df["corpus"].fillna(""))

        with self._lock:
            self._vectorizer = vectorizer
            self._matrix     = matrix
            self._df         = df
            self._built_at   = time.monotonic()

        logger.info("Recommender: rebuilt — %d articles, %d features", len(df), matrix.shape[1])

    @staticmethod
    def _recency(dt: datetime) -> float:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hours = max((datetime.now(timezone.utc) - dt).total_seconds() / 3600, 0)
        # Flat window for the first 6 h: all breaking news is equally fresh.
        # Linear decay 6–48 h so quality day-old content isn't buried.
        # Exponential tail beyond 48 h.
        if hours <= 6:
            return 1.0
        if hours <= 48:
            return 1.0 - 0.70 * (hours - 6) / 42
        return float(0.30 * np.exp(-0.693 * (hours - 48) / HALF_LIFE_HOURS))

    @staticmethod
    def _trending_scores(matrix, df: pd.DataFrame) -> np.ndarray:
        now = datetime.now(timezone.utc)

        def is_recent(dt: datetime) -> bool:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (now - dt).total_seconds() < TREND_WINDOW_H * 3600

        recent_mask = df["published_at"].apply(is_recent).values
        n_recent = recent_mask.sum()
        if n_recent < 2:
            return np.zeros(len(df))

        recent_matrix = matrix[recent_mask]
        sim = cosine_similarity(matrix, recent_matrix)
        above = (sim > TREND_THRESHOLD).sum(axis=1) - recent_mask.astype(int)
        return np.maximum(above / n_recent, 0)

    def _user_vector(
        self,
        matrix,
        df: pd.DataFrame,
        categories:     list[str],
        viewed_ids:     list[int],
        viewed_authors: list[str],
    ):
        parts: list[tuple[float, np.ndarray]] = []

        if categories:
            mask = df["category"].isin(categories)
            if mask.any():
                parts.append((0.50, np.asarray(matrix[mask.values].mean(axis=0))))

        # Positional decay: viewed_ids is ordered most-recent-first (maintained by
        # preferences.ts recordView). Recent reads are 5–10× more predictive of
        # current interest than articles read days ago.
        if viewed_ids:
            recent = viewed_ids[:30]
            mask = df["id"].isin(recent)
            if mask.any():
                idx_map = {aid: i for i, aid in enumerate(recent)}
                positions = df[mask]["id"].map(idx_map).values.astype(float)
                decay = np.exp(-0.15 * positions)
                decay /= decay.sum()
                vecs = matrix[mask.values]
                weighted = np.asarray(vecs.multiply(decay[:, None]).sum(axis=0))
                parts.append((0.30, weighted))

        if viewed_authors:
            mask = df["author"].isin(viewed_authors)
            if mask.any():
                parts.append((0.20, np.asarray(matrix[mask.values].mean(axis=0))))

        if not parts:
            return None

        user_vec = sum(w * v for w, v in parts)
        norm = np.linalg.norm(user_vec)
        return user_vec / norm if norm > 0 else None

    @staticmethod
    def _mmr_select(scores: np.ndarray, matrix, n: int) -> list[int]:
        """
        Maximal Marginal Relevance (Carbonell & Goldstein 1998).
        Greedily selects articles that maximise relevance while minimising
        redundancy with already-selected articles. Prevents the feed from
        flooding with 5 sources covering the same story.
        """
        n_items = len(scores)
        if n_items == 0:
            return []
        n = min(n, n_items)

        # Precompute pairwise similarities once — avoids repeated sparse ops per iteration.
        all_sims = cosine_similarity(matrix)   # (n_items × n_items) dense

        remaining = list(range(n_items))
        selected: list[int] = []

        while remaining and len(selected) < n:
            if not selected:
                best = remaining[int(np.argmax([scores[i] for i in remaining]))]
            else:
                sel = np.array(selected)
                mmr = [
                    MMR_LAMBDA * scores[i] - (1 - MMR_LAMBDA) * all_sims[i, sel].max()
                    for i in remaining
                ]
                best = remaining[int(np.argmax(mmr))]
            selected.append(best)
            remaining.remove(best)

        return selected

    def recommend(
        self,
        articles:             list,
        preferred_categories: list[str],
        preferred_regions:    list[str],
        viewed_ids:           list[int],
        viewed_authors:       list[str] | None = None,
        limit:  int = 20,
        offset: int = 0,
    ) -> list:
        if not articles:
            return []

        if self._needs_rebuild(len(articles)):
            try:
                self._rebuild(articles)
            except Exception:
                logger.exception("Recommender rebuild failed; falling back to recency")
                return articles[offset : offset + limit]

        with self._lock:
            if self._df is None or self._matrix is None:
                return articles[offset : offset + limit]
            df_full     = self._df.copy()
            matrix_full = self._matrix

        # Build user profile from the FULL pool — viewed articles contribute to the
        # interest vector even though they'll be excluded from the output pool below.
        user_vec = self._user_vector(
            matrix_full, df_full,
            preferred_categories,
            viewed_ids,
            viewed_authors or [],
        )
        has_signal = user_vec is not None

        # Exclude already-opened articles — users shouldn't see what they've read.
        viewed_set  = set(viewed_ids)
        unread_mask = ~df_full["id"].isin(viewed_set)
        df     = df_full[unread_mask].reset_index(drop=True)
        matrix = matrix_full[unread_mask.values]

        if len(df) == 0:
            return []

        sim = (cosine_similarity(user_vec, matrix).flatten()
               if has_signal else np.zeros(len(df)))

        recency = df["published_at"].apply(self._recency).values

        cat_match = (
            np.array([_cat_score(c, preferred_categories) for c in df["category"]])
            if preferred_categories else np.zeros(len(df))
        )

        reg_match = df["region"].apply(
            lambda r: 1.0 if preferred_regions and (r in preferred_regions or "global" in preferred_regions)
                      else 0.3 if preferred_regions and r == "global"
                      else 0.0
        ).values

        trending = self._trending_scores(matrix, df)

        # Cold-start: lean on trending + recency; with history: semantic similarity dominates.
        if has_signal:
            scores = (
                0.35 * sim
              + 0.20 * recency
              + 0.20 * cat_match
              + 0.15 * reg_match
              + 0.10 * trending
            )
        else:
            scores = (
                0.10 * sim
              + 0.30 * recency
              + 0.05 * cat_match
              + 0.20 * reg_match
              + 0.35 * trending
            )

        # MMR selects offset+limit articles with diversity; slice for the requested page.
        need          = offset + limit
        ranked_idx    = self._mmr_select(scores, matrix, min(need, len(df)))
        ranked_ids    = df.iloc[ranked_idx]["id"].tolist()
        id_to_obj     = {a.id: a for a in articles}
        ranked        = [id_to_obj[aid] for aid in ranked_ids if aid in id_to_obj]

        return ranked[offset : offset + limit]


recommender = ArticleRecommender()
