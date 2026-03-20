from sqlalchemy import create_engine, inspect, text
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


def _ensure_data_source_topic_columns():
    """兼容已有数据库：为 data_sources 表补充主题过滤字段"""
    inspector = inspect(engine)
    if "data_sources" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("data_sources")}

    with engine.begin() as conn:
        if "topic_keywords" not in existing_columns:
            if engine.dialect.name == "mysql":
                conn.execute(
                    text("ALTER TABLE data_sources ADD COLUMN topic_keywords JSON NULL")
                )
            else:
                conn.execute(
                    text("ALTER TABLE data_sources ADD COLUMN topic_keywords TEXT")
                )

        if "topic_match_mode" not in existing_columns:
            if engine.dialect.name == "mysql":
                conn.execute(
                    text(
                        "ALTER TABLE data_sources ADD COLUMN topic_match_mode "
                        "ENUM('any','all') NOT NULL DEFAULT 'any'"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE data_sources ADD COLUMN topic_match_mode "
                        "VARCHAR(10) NOT NULL DEFAULT 'any'"
                    )
                )


def _ensure_lead_scoring_columns():
    """兼容已有数据库：为 leads 表补充分级评分字段"""
    inspector = inspect(engine)
    if "leads" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("leads")}

    with engine.begin() as conn:
        if "score" not in existing_columns:
            conn.execute(text("ALTER TABLE leads ADD COLUMN score INTEGER NOT NULL DEFAULT 0"))

        if "grade" not in existing_columns:
            if engine.dialect.name == "mysql":
                conn.execute(
                    text(
                        "ALTER TABLE leads ADD COLUMN grade "
                        "ENUM('A','B','C','D') NOT NULL DEFAULT 'D'"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE leads ADD COLUMN grade "
                        "VARCHAR(1) NOT NULL DEFAULT 'D'"
                    )
                )

        if "follow_up_hint" not in existing_columns:
            conn.execute(text("ALTER TABLE leads ADD COLUMN follow_up_hint TEXT"))

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
    _ensure_data_source_topic_columns()
    _ensure_lead_scoring_columns()
