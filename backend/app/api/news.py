from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/news", tags=["news"])


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
