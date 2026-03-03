from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Article, User
from app.services.processor import data_processor

router = APIRouter(prefix="/processor", tags=["数据处理"])


@router.post("/articles/{article_id}/process")
def process_single_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理单篇文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    result = data_processor.process_article(article_id)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/articles/process")
def process_pending_articles(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量处理待处理文章"""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit必须介于1-200之间")

    result = data_processor.process_pending_articles(limit)

    return result


@router.post("/leads/{lead_id}/enrich")
def enrich_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """丰富线索企业信息"""
    result = data_processor.enrich_lead(lead_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/stats/pending")
def get_pending_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取待处理文章统计"""
    pending_count = db.query(Article).filter(Article.status == "pending").count()
    processed_count = db.query(Article).filter(Article.status == "processed").count()
    total_count = db.query(Article).count()

    return {
        "pending": pending_count,
        "processed": processed_count,
        "total": total_count,
    }
