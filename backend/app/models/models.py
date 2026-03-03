from app.core.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    JSON,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum


class SourceTypeEnum(str, enum.Enum):
    """来源类型"""

    news = "news"
    rss = "rss"
    wechat = "wechat"
    social = "social"


class ArticleStatusEnum(str, enum.Enum):
    """文章处理状态"""

    pending = "pending"
    processed = "processed"
    archived = "archived"


class LeadEventTypeEnum(str, enum.Enum):
    """线索事件类型"""

    financing = "financing"
    acquisition = "acquisition"
    product = "product"
    expansion = "expansion"
    procurement = "procurement"
    executive = "executive"
    policy = "policy"
    other = "other"


class LeadStatusEnum(str, enum.Enum):
    """线索状态"""

    new = "new"
    contacted = "contacted"
    converted = "converted"
    invalid = "invalid"


class UserRoleEnum(str, enum.Enum):
    """用户角色"""

    admin = "admin"
    user = "user"
    sales = "sales"
    viewer = "viewer"


class Article(Base):
    """新闻文章表"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text)
    summary = Column(String(1000))
    author = Column(String(100))
    source_name = Column(String(100), nullable=False, index=True)
    source_url = Column(String(1000), nullable=False)
    source_type = Column(
        Enum(SourceTypeEnum), nullable=False, default=SourceTypeEnum.news
    )
    category = Column(String(50))
    keywords = Column(JSON)
    published_at = Column(DateTime, index=True)
    crawled_at = Column(DateTime, default=func.now(), index=True)
    is_duplicate = Column(Boolean, default=False)
    is_filtered = Column(Boolean, default=False)
    status = Column(Enum(ArticleStatusEnum), default=ArticleStatusEnum.pending)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    leads = relationship("Lead", back_populates="article")


class Lead(Base):
    """销售线索表"""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=False, index=True)
    event_type = Column(Enum(LeadEventTypeEnum), nullable=False, index=True)
    event_detail = Column(String(500))
    event_amount = Column(String(100))
    source_article_id = Column(Integer, ForeignKey("articles.id"))
    source_title = Column(String(500))
    source_url = Column(String(1000))
    source_name = Column(String(100))
    published_at = Column(DateTime, index=True)
    confidence = Column(Integer, default=50)
    status = Column(Enum(LeadStatusEnum), default=LeadStatusEnum.new, index=True)
    assigned_to = Column(String(100))
    sales_notes = Column(Text)
    enrichment_data = Column(JSON)

    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    article = relationship("Article", back_populates="leads")


class DataSource(Base):
    """数据源配置表"""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(Enum(SourceTypeEnum), nullable=False)
    url = Column(String(1000), nullable=False)
    config = Column(JSON)
    crawl_interval = Column(Integer, default=60)
    enabled = Column(Boolean, default=True, index=True)
    last_crawl_at = Column(DateTime)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100))
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.viewer)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Keyword(Base):
    """关键词配置表"""

    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50))
    weight = Column(Integer, default=1)
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())


class LeadRule(Base):
    """线索识别规则表"""

    __tablename__ = "lead_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    event_type = Column(Enum(LeadEventTypeEnum), nullable=False)
    patterns = Column(JSON, nullable=False)
    priority = Column(Integer, default=5)
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
