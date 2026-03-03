"""
监控指标服务 - Prometheus 指标导出
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Request, Response
from datetime import datetime, timedelta

from app.core.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# 自定义业务指标
# ============================================================================

# API 请求计数器
api_requests_total = Counter(
    "leadmine_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

# API 请求延迟
api_request_duration = Histogram(
    "leadmine_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# 爬虫指标
crawl_articles_total = Counter(
    "leadmine_crawl_articles_total",
    "Total articles crawled",
    ["source_name", "status"],  # status: success, failed
)

crawl_duration = Histogram(
    "leadmine_crawl_duration_seconds",
    "Crawl duration in seconds",
    ["source_name"],
    buckets=[1, 5, 10, 30, 60, 300],
)

# 线索指标
leads_extracted_total = Counter(
    "leadmine_leads_extracted_total",
    "Total leads extracted",
    ["event_type", "source"],
)

lead_confidence_histogram = Histogram(
    "leadmine_lead_confidence",
    "Lead confidence distribution",
    buckets=[0, 25, 50, 75, 90, 100],
)

# 处理指标
articles_processed_total = Counter(
    "leadmine_articles_processed_total",
    "Total articles processed",
    ["status"],  # success, failed, duplicate
)

# 活跃用户 gauge
active_users = Gauge(
    "leadmine_active_users",
    "Number of active users in last hour",
)

# 数据库连接 gauge
db_connection_pool = Gauge(
    "leadmine_db_connection_pool",
    "Database connection pool status",
    ["state"],  # idle, active
)

# Redis 缓存指标
redis_cache_hits = Counter(
    "leadmine_redis_cache_hits_total",
    "Total Redis cache hits",
)

redis_cache_misses = Counter(
    "leadmine_redis_cache_misses_total",
    "Total Redis cache misses",
)


# ============================================================================
# 指标记录函数
# ============================================================================


def record_api_request(method: str, endpoint: str, status: int, duration: float):
    """记录 API 请求"""
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)


def record_crawl(
    source_name: str, article_count: int, duration: float, success: bool = True
):
    """记录爬虫执行"""
    status = "success" if success else "failed"
    crawl_articles_total.labels(source_name=source_name, status=status).inc(
        article_count
    )
    crawl_duration.labels(source_name=source_name).observe(duration)


def record_lead_extracted(event_type: str, source: str, confidence: int):
    """记录线索提取"""
    leads_extracted_total.labels(event_type=event_type, source=source).inc()
    lead_confidence_histogram.observe(confidence)


def record_article_processed(status: str):
    """记录文章处理"""
    articles_processed_total.labels(status=status).inc()


def record_cache_hit():
    """记录缓存命中"""
    redis_cache_hits.inc()


def record_cache_miss():
    """记录缓存未命中"""
    redis_cache_misses.inc()


# ============================================================================
# Prometheus 指标端点
# ============================================================================


def setup_metrics_routes(app):
    """设置指标端点"""

    @app.get("/metrics")
    async def metrics():
        """Prometheus 指标端点"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/metrics/business")
    async def business_metrics():
        """自定义业务指标"""
        from app.core.database import SessionLocal
        from app.models import Lead, Article, DataSource

        db = SessionLocal()
        try:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=now.weekday())
            month_start = today_start.replace(day=1)

            # 线索统计
            leads_today = db.query(Lead).filter(Lead.created_at >= today_start).count()
            leads_week = db.query(Lead).filter(Lead.created_at >= week_start).count()
            leads_month = db.query(Lead).filter(Lead.created_at >= month_start).count()
            leads_total = db.query(Lead).count()

            # 文章统计
            articles_today = (
                db.query(Article).filter(Article.crawled_at >= today_start).count()
            )
            articles_total = db.query(Article).count()

            # 数据源统计
            sources_enabled = (
                db.query(DataSource).filter(DataSource.enabled == True).count()  # noqa: E712
            )
            sources_total = db.query(DataSource).count()

            # 线索状态分布
            leads_by_status = {}
            for status in ["new", "contacted", "converted", "invalid"]:
                count = db.query(Lead).filter(Lead.status == status).count()
                leads_by_status[status] = count

            return {
                "leads": {
                    "today": leads_today,
                    "week": leads_week,
                    "month": leads_month,
                    "total": leads_total,
                    "by_status": leads_by_status,
                },
                "articles": {
                    "today": articles_today,
                    "total": articles_total,
                },
                "sources": {
                    "enabled": sources_enabled,
                    "total": sources_total,
                },
                "cache": {
                    "hits": redis_cache_hits._value.get(),
                    "misses": redis_cache_misses._value.get(),
                },
                "timestamp": now.isoformat(),
            }
        finally:
            db.close()


def setup_metrics_middleware(app):
    """设置指标中间件"""

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        import time

        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # 记录请求
        if request.url.path not in [
            "/",
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        ]:
            record_api_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration,
            )

        return response
