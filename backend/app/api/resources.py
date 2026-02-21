from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Article, DataSource, SourceTypeEnum, ArticleStatusEnum, User
from app.schemas import (
    ArticleResponse,
    ArticlePaginatedResponse,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
)

router_article = APIRouter(prefix="/articles", tags=["文章"])
router_source = APIRouter(prefix="/sources", tags=["数据源"])


# 文章相关接口
@router_article.get("", response_model=ArticlePaginatedResponse)
def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文章列表"""
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
        query.order_by(desc(Article.crawled_at)).offset(offset).limit(page_size).all()
    )

    return {"total": total, "page": page, "page_size": page_size, "data": articles}


@router_article.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文章详情"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    return article


# 数据源相关接口
@router_source.get("", response_model=List[DataSourceResponse])
def get_sources(
    source_type: Optional[SourceTypeEnum] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取数据源列表"""
    from datetime import datetime, date

    query = db.query(DataSource)

    if source_type:
        query = query.filter(DataSource.type == source_type)
    if enabled is not None:
        query = query.filter(DataSource.enabled == enabled)

    sources = query.order_by(DataSource.name).all()

    # 添加统计信息
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    result = []
    for source in sources:
        # 统计今日抓取数量
        today_count = (
            db.query(Article)
            .filter(
                Article.source_name == source.name, Article.crawled_at >= today_start
            )
            .count()
        )

        # 计算成功率（简化：基于今日是否有数据）
        success_rate = 100 if today_count > 0 else (0 if source.last_crawl_at else 0)

        source_dict = {
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "url": source.url,
            "config": source.config,
            "crawl_interval": source.crawl_interval,
            "enabled": source.enabled,
            "last_crawl_at": source.last_crawl_at,
            "today_count": today_count,
            "success_rate": success_rate,
            "created_at": source.created_at,
        }
        result.append(source_dict)

    return result


@router_source.get("/{source_id}", response_model=DataSourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取数据源详情"""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    return source


@router_source.post("", response_model=DataSourceResponse, status_code=201)
def create_source(
    source_data: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建数据源"""
    # 检查名称是否已存在
    existing = db.query(DataSource).filter(DataSource.name == source_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="数据源名称已存在")

    source = DataSource(**source_data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)

    # 添加到调度器
    if source.enabled:
        from app.services.scheduler import scheduler

        scheduler.add_crawl_task(source)

    return source


@router_source.patch("/{source_id}", response_model=DataSourceResponse)
def update_source(
    source_id: int,
    source_data: DataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新数据源"""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    db.commit()
    db.refresh(source)

    # 更新调度器任务
    from app.services.scheduler import scheduler

    if source.enabled:
        scheduler.add_crawl_task(source)
    else:
        scheduler.remove_crawl_task(source_id)

    return source


@router_source.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除数据源"""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    # 从调度器移除
    from app.services.scheduler import scheduler

    scheduler.remove_crawl_task(source_id)

    db.delete(source)
    db.commit()

    return None


@router_source.post("/{source_id}/crawl")
def trigger_crawl(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发数据源抓取"""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    if not source.enabled:
        raise HTTPException(status_code=400, detail="数据源已禁用")

    # 触发爬虫任务
    from app.services.scheduler import scheduler

    scheduler.trigger_manual_crawl(source_id)

    return {"message": "抓取任务已触发", "source_id": source_id}
