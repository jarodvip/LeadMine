from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 根据数据库类型选择配置
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    # 导入所有模型以确保 SQLAlchemy 知道要创建哪些表
    from app.models.models import Article  # noqa: F401
    from app.models.models import Lead  # noqa: F401
    from app.models.models import DataSource  # noqa: F401
    from app.models.models import User  # noqa: F401
    from app.models.models import Keyword  # noqa: F401
    from app.models.models import LeadRule  # noqa: F401

    Base.metadata.create_all(bind=engine)
