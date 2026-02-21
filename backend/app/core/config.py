"""
应用配置
"""

import os
import warnings
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """应用配置类"""

    # 应用配置
    app_name: str = "LeadMine API"
    debug: bool = Field(default=False, env="DEBUG")
    version: str = "1.0.0"

    @property
    def app_version(self) -> str:
        return self.version

    # 数据库配置
    database_url: str = Field(default="sqlite:///./leadmine.db", env="DATABASE_URL")

    # Redis 配置
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Elasticsearch 配置
    elasticsearch_url: str = Field(
        default="http://localhost:9200", env="ELASTICSEARCH_URL"
    )

    # JWT 配置 - 强制从环境变量读取
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # RSSHub 配置
    rsshub_url: str = Field(default="http://localhost:1200", env="RSSHUB_URL")

    # CORS 配置 - 支持逗号分隔的字符串或JSON数组
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:8501,http://localhost:8502,http://localhost:3000",
        env="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS配置，支持逗号分隔的字符串"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # 管理员初始密码
    admin_password: str = Field(default="", env="ADMIN_PASSWORD")

    # 爬虫配置
    crawl_timeout: int = 30
    max_concurrent_crawls: int = 5

    class Config:
        env_file = ".env"
        extra = "allow"


# 全局配置实例
settings = Settings()

# 验证 JWT 密钥
if (
    not settings.jwt_secret
    or settings.jwt_secret == "your-secret-key-change-in-production"
):
    warnings.warn(
        "WARNING: JWT_SECRET 未设置或使用默认弱密钥！"
        "请设置强密钥: export JWT_SECRET=\$(openssl rand -base64 64)",
        RuntimeWarning,
    )
