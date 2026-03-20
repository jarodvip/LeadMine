"""
文章存储服务
"""

from typing import List, Dict
from datetime import datetime
import logging

from app.core.database import SessionLocal
from app.models import Article, DataSource, SourceTypeEnum
from app.processors.topic_filter import matches_topic

logger = logging.getLogger(__name__)


def save_articles(articles: List[Dict], source_name: str, source: DataSource = None) -> int:
    """
    保存文章到数据库
    Args:
        articles: 文章列表
        source_name: 来源名称
    Returns:
        保存的文章数量
    """
    if not articles:
        return 0

    db = SessionLocal()
    saved_count = 0

    try:
        # 获取来源类型与主题配置
        if source is None:
            source = db.query(DataSource).filter(DataSource.name == source_name).first()
        source_type = source.type if source else SourceTypeEnum.news
        topic_keywords = source.topic_keywords if source else None
        topic_match_mode = source.topic_match_mode if source else None

        for article_data in articles:
            # 检查是否已存在（根据URL）
            existing = (
                db.query(Article)
                .filter(Article.source_url == article_data.get("source_url"))
                .first()
            )

            if existing:
                continue

            if not matches_topic(
                article_data.get("title"),
                article_data.get("content"),
                topic_keywords,
                topic_match_mode,
            ):
                continue

            # 创建新文章
            article = Article(
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                summary=article_data.get("summary", ""),
                author=article_data.get("author", ""),
                source_name=source_name,
                source_url=article_data.get("source_url", ""),
                source_type=source_type,
                category=article_data.get("category"),
                keywords=article_data.get("keywords"),
                published_at=article_data.get("published_at"),
                crawled_at=datetime.now(),
            )

            db.add(article)
            saved_count += 1

        db.commit()
        logger.info(f"保存 {saved_count} 篇新文章 from {source_name}")

    except Exception as e:
        logger.error(f"保存文章失败: {e}")
        db.rollback()
    finally:
        db.close()

    return saved_count


def get_articles(
    source_name: str = None,
    category: str = None,
    keyword: str = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict:
    """
    获取文章列表
    """
    db = SessionLocal()

    try:
        query = db.query(Article)

        if source_name:
            query = query.filter(Article.source_name == source_name)
        if category:
            query = query.filter(Article.category == category)
        if keyword:
            query = query.filter(Article.title.contains(keyword))

        total = query.count()

        offset = (page - 1) * page_size
        articles = (
            query.order_by(Article.crawled_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {"total": total, "page": page, "page_size": page_size, "data": articles}

    finally:
        db.close()
