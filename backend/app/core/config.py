from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # 数据库配置 - 默认使用SQLite本地测试
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./leadmine.db")

    # Redis配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Elasticsearch配置
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # JWT配置
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # RSSHub配置
    rsshub_url: str = os.getenv("RSSHUB_URL", "http://localhost:1200")

    # 应用配置
    app_name: str = "LeadMine"
    app_version: str = "1.0.0"
    debug: bool = True

    # CORS配置 - 允许所有来源
    cors_origins: list = ["*"]

    # 爬虫配置
    crawl_timeout: int = 30
    max_concurrent_crawls: int = 5

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
