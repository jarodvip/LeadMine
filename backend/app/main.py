from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import get_logger
from app.api import api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("应用启动中...")

    # 启动时
    init_db()
    create_default_admin()

    # 初始化默认数据源
    create_default_sources()

    # 启动爬虫调度器（可选）
    try:
        from app.services.scheduler import scheduler

        scheduler.start()
    except Exception as e:
        logger.warning(f"调度器启动失败（可选服务）: {e}")

    # 启动告警服务（生产环境）
    if not settings.debug:
        try:
            from app.services.alert import alert_service

            alert_service.start()
        except Exception as e:
            logger.warning(f"告警服务启动失败: {e}")

    logger.info("应用启动完成")

    yield

    # 关闭时
    logger.info("应用关闭中...")
    try:
        from app.services.scheduler import scheduler

        scheduler.stop()
    except Exception:
        pass
    logger.info("应用已关闭")


def create_default_admin():
    """创建默认管理员账户"""
    import secrets
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash
    from app.models import User

    db = SessionLocal()
    try:
        # 检查是否已存在管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # 从环境变量读取或使用随机生成的强密码
            admin_password = settings.admin_password or secrets.token_urlsafe(16)
            if not settings.admin_password:
                logger.warning("ADMIN_PASSWORD 未设置，已生成临时密码")
                logger.warning(f"临时密码: {admin_password}")
                logger.warning("请立即登录并修改密码！")

            admin = User(
                username="admin",
                password_hash=get_password_hash(admin_password),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("默认管理员账户已创建")
    finally:
        db.close()


def create_default_sources():
    """创建默认数据源"""
    from app.core.database import SessionLocal
    from app.models import DataSource, SourceTypeEnum

    db = SessionLocal()
    try:
        default_sources = [
            {
                "name": "36氪",
                "type": SourceTypeEnum.news,
                "url": "https://www.36kr.com/",
                "crawl_interval": 30,
            },
            {
                "name": "虎嗅",
                "type": SourceTypeEnum.news,
                "url": "https://www.huxiu.com/",
                "crawl_interval": 30,
            },
        ]

        for source_data in default_sources:
            existing = (
                db.query(DataSource)
                .filter(DataSource.name == source_data["name"])
                .first()
            )
            if not existing:
                source = DataSource(**source_data, enabled=True)
                db.add(source)

        db.commit()
        logger.info("默认数据源已创建")
    except Exception as e:
        logger.error(f"创建默认数据源失败: {e}")
    finally:
        db.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="热点新闻采集与销售线索挖掘系统",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流中间件（生产环境启用）
if not settings.debug:
    from app.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

# 缓存中间件（生产环境启用）
if not settings.debug:
    from app.middleware.cache import CacheMiddleware

    app.add_middleware(CacheMiddleware)

# 设置监控指标
from app.services.metrics import setup_metrics_routes, setup_metrics_middleware

setup_metrics_routes(app)
setup_metrics_middleware(app)

# 挂载API路由
app.include_router(api_router)


@app.get("/")
def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}
