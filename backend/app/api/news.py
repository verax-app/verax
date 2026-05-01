from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut
from app.services.recommender import recommender, MAX_ARTICLES

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/recommended", response_model=list[ArticleOut])
def recommended_news(
    filter_region:   str = Query("", description="Exact region to restrict results to"),
    filter_category: str = Query("", description="Exact category to restrict results to"),
    categories:      str = Query("", description="Comma-separated preferred categories"),
    regions:         str = Query("global", description="Comma-separated preferred regions"),
    viewed_ids:      str = Query("", description="Comma-separated article IDs the user has read"),
    viewed_authors:  str = Query("", description="Pipe-delimited author names the user has read"),
    limit:           int = Query(20, le=50),
    offset:          int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    preferred_categories = [c.strip() for c in categories.split(",")       if c.strip()]
    preferred_regions    = [r.strip() for r in regions.split(",")          if r.strip()]
    viewed_id_list       = [int(i)    for i in viewed_ids.split(",")       if i.strip().isdigit()]
    viewed_author_list   = [a.strip() for a in viewed_authors.split("|||") if a.strip()]

    sort_ts = func.coalesce(Article.published_at, Article.created_at)
    q = db.query(Article).order_by(sort_ts.desc(), Article.id.desc())

    has_region_filter = bool(filter_region) and filter_region != 'global'

    if has_region_filter:
        q = q.filter(or_(Article.region == filter_region, Article.region == 'global'))

    if filter_category and not has_region_filter:
        q = q.filter(Article.category == filter_category)

    articles = q.limit(MAX_ARTICLES).all()

    eff_categories = [filter_category] if filter_category else preferred_categories
    eff_regions    = [filter_region]   if filter_region   else preferred_regions

    return recommender.recommend(
        articles=articles,
        preferred_categories=eff_categories,
        preferred_regions=eff_regions,
        viewed_ids=viewed_id_list,
        viewed_authors=viewed_author_list,
        limit=limit,
        offset=offset,
    )


@router.get("/", response_model=list[ArticleOut])
def list_news(
    language:   str = Query("en"),
    region:     str = Query("global"),
    regions:    Optional[str] = Query(None),
    category:   Optional[str] = Query(None),
    categories: Optional[str] = Query(None),
    before_ts:  Optional[datetime] = Query(None),
    before_id:  Optional[int] = Query(None),
    limit:      int = Query(15, le=50),
    db: Session = Depends(get_db),
):
    q = db.query(Article)

    region_list = [r.strip() for r in regions.split(",")] if regions else None
    if region_list and "global" not in region_list:
        q = q.filter(Article.region.in_(region_list))
    elif not region_list and region != "global":
        q = q.filter(Article.region == region)

    category_list = [c.strip() for c in categories.split(",")] if categories else None
    if category_list:
        q = q.filter(Article.category.in_(category_list))
    elif category:
        q = q.filter(Article.category == category)

    sort_ts = func.coalesce(Article.published_at, Article.created_at)

    if before_ts is not None and before_id is not None:
        q = q.filter(
            or_(
                sort_ts < before_ts,
                and_(sort_ts == before_ts, Article.id < before_id),
            )
        )

    return q.order_by(sort_ts.desc(), Article.id.desc()).limit(limit).all()


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
