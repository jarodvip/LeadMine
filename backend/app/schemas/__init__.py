from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from app.models import (
    LeadEventTypeEnum,
    LeadStatusEnum,
    LeadGradeEnum,
    SourceTypeEnum,
    TopicMatchModeEnum,
    UserRoleEnum,
)
from app.processors.cleaner import sanitize_input


# 用户相关
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: UserRoleEnum = UserRoleEnum.viewer


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少为8位")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# 数据源相关
class DataSourceBase(BaseModel):
    name: str
    type: SourceTypeEnum
    url: str
    config: Optional[dict] = None
    crawl_interval: int = 60
    enabled: bool = True
    topic_keywords: Optional[List[str]] = None
    topic_match_mode: TopicMatchModeEnum = TopicMatchModeEnum.any


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[SourceTypeEnum] = None
    url: Optional[str] = None
    config: Optional[dict] = None
    crawl_interval: Optional[int] = None
    enabled: Optional[bool] = None
    topic_keywords: Optional[List[str]] = None
    topic_match_mode: Optional[TopicMatchModeEnum] = None


class DataSourceResponse(DataSourceBase):
    id: int
    last_crawl_at: Optional[datetime]
    today_count: int = 0
    success_rate: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# 文章相关
class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    source_name: str
    source_url: str
    source_type: SourceTypeEnum = SourceTypeEnum.news
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    published_at: Optional[datetime] = None


class ArticleResponse(ArticleBase):
    id: int
    crawled_at: datetime
    is_duplicate: bool
    is_filtered: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# 线索相关
class LeadBase(BaseModel):
    company_name: str
    event_type: LeadEventTypeEnum
    event_detail: Optional[str] = None
    event_amount: Optional[str] = None
    source_article_id: Optional[int] = None
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    published_at: Optional[datetime] = None
    confidence: int = 50


class LeadCreate(LeadBase):
    @field_validator("confidence")
    def validate_confidence(cls, v):
        if v < 0 or v > 100:
            raise ValueError("置信度必须在 0-100 之间")
        return v

    @field_validator("company_name", "event_detail", "event_amount")
    @classmethod
    def sanitize_xss_fields(cls, v):
        """XSS 过滤"""
        if v is not None:
            return sanitize_input(v)
        return v


class LeadUpdate(BaseModel):
    status: Optional[LeadStatusEnum] = None
    assigned_to: Optional[str] = None
    sales_notes: Optional[str] = None
    enrichment_data: Optional[dict] = None


class LeadResponse(LeadBase):
    id: int
    status: LeadStatusEnum
    assigned_to: Optional[str]
    sales_notes: Optional[str]
    enrichment_data: Optional[dict]
    score: int = 0
    grade: LeadGradeEnum = LeadGradeEnum.D
    follow_up_hint: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# 关键词相关
class KeywordBase(BaseModel):
    keyword: str
    category: Optional[str] = None
    weight: int = 1
    enabled: bool = True


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    category: Optional[str] = None
    weight: Optional[int] = None
    enabled: Optional[bool] = None


class KeywordResponse(KeywordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# 线索规则相关
class LeadRuleBase(BaseModel):
    name: str
    event_type: LeadEventTypeEnum
    patterns: List[str]
    priority: int = 5
    enabled: bool = True


class LeadRuleCreate(LeadRuleBase):
    pass


class LeadRuleUpdate(BaseModel):
    name: Optional[str] = None
    patterns: Optional[List[str]] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class LeadRuleResponse(LeadRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# 分页响应
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[LeadResponse]


class UserPaginatedResponse(BaseModel):
    """用户分页响应"""

    total: int
    page: int
    page_size: int
    data: List[UserResponse]


class ArticlePaginatedResponse(BaseModel):
    """文章分页响应"""

    total: int
    page: int
    page_size: int
    data: List[ArticleResponse]


# 批量操作请求
class BatchUpdateStatusRequest(BaseModel):
    lead_ids: List[int]
    status: LeadStatusEnum


class BatchAssignRequest(BaseModel):
    lead_ids: List[int]
    assigned_to: str


class BatchDeleteRequest(BaseModel):
    lead_ids: List[int]


class BatchOperationResponse(BaseModel):
    message: str
    updated_count: int = 0
    deleted_count: int = 0


# 统计相关
class DashboardStats(BaseModel):
    today_leads: int = 0
    week_leads: int = 0
    month_leads: int = 0
    total_leads: int = 0


class LeadsByType(BaseModel):
    financing: int = 0
    acquisition: int = 0
    product: int = 0
    expansion: int = 0
    procurement: int = 0
    executive: int = 0
    policy: int = 0
    other: int = 0


class DashboardResponse(DashboardStats):
    leads_by_type: LeadsByType = {}
    leads_by_source: dict = {}
    recent_leads: List[LeadResponse] = []
