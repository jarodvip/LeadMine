"""
pytest 配置和通用 fixtures
"""

import os

# 设置测试环境变量（必须在导入 app 之前）
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-do-not-use-in-production"
os.environ["DEBUG"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 导入应用
import sys

sys.path.insert(0, "/Users/jarod/Dev/new/backend")

from app.models.models import Base
from app.core.database import get_db
from app.main import app

# 使用 SQLite 内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    创建测试数据库会话
    每个测试函数执行前创建表，执行后删除表
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """
    创建测试客户端
    使用测试数据库覆盖生产数据库
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    """创建测试用户并返回用户信息"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证请求头"""
    response = client.post(
        "/api/v1/auth/login", data={"username": "testuser", "password": "TestPass123!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(client):
    """创建管理员用户"""
    # 直接创建管理员（绕过 API 的角色限制）
    from app.models.models import User
    from app.core.security import get_password_hash
    from sqlalchemy.orm import Session

    db = TestingSessionLocal()
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()

    return {"username": "admin", "password": "AdminPass123!"}


@pytest.fixture
def admin_headers(client, admin_user):
    """获取管理员认证头"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_lead(client, auth_headers):
    """创建示例线索"""
    response = client.post(
        "/api/v1/leads",
        json={
            "company_name": "测试公司",
            "event_type": "financing",
            "event_detail": "完成1亿元A轮融资",
            "event_amount": "1亿元",
            "source_name": "36氪",
            "confidence": 85,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()
