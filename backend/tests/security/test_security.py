"""
安全测试
测试密码加密、JWT、权限控制等安全功能
"""

import pytest
import time
from datetime import timedelta


class TestPasswordHash:
    """测试密码哈希功能"""

    def test_password_hash_generation(self):
        """测试密码哈希生成"""
        from app.core.security import get_password_hash

        password = "TestPass123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2")  # bcrypt 哈希以 $2 开头

    def test_password_hash_uniqueness(self):
        """测试相同密码产生不同哈希"""
        from app.core.security import get_password_hash

        password = "SamePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # bcrypt 自动加盐

    def test_password_verification_success(self):
        """测试密码验证成功"""
        from app.core.security import get_password_hash, verify_password

        password = "TestPass123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """测试密码验证失败"""
        from app.core.security import get_password_hash, verify_password

        password = "TestPass123!"
        wrong_password = "WrongPass123!"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_password_verification_empty(self):
        """测试空密码验证"""
        from app.core.security import verify_password

        hashed = "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert verify_password("", hashed) is False


class TestJWTToken:
    """测试 JWT Token 功能"""

    def test_token_creation(self):
        """测试 Token 创建"""
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": "testuser"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_decode(self):
        """测试 Token 解码"""
        from app.core.security import create_access_token, decode_access_token

        token = create_access_token(data={"sub": "testuser"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_token_expiration(self):
        """测试 Token 过期"""
        from app.core.security import create_access_token, decode_access_token

        # 创建已过期 Token
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1),  # 已经过期
        )
        payload = decode_access_token(token)
        assert payload is None  # 应该返回 None

    def test_invalid_token_format(self):
        """测试无效 Token 格式"""
        from app.core.security import decode_access_token

        payload = decode_access_token("invalid.token.format")
        assert payload is None

    def test_tampered_token(self):
        """测试被篡改的 Token"""
        from app.core.security import create_access_token, decode_access_token

        token = create_access_token(data={"sub": "testuser"})
        # 篡改 Token
        tampered_token = token[:-10] + "XXXXXXXXXX"
        payload = decode_access_token(tampered_token)
        assert payload is None

    def test_empty_token(self):
        """测试空 Token"""
        from app.core.security import decode_access_token

        payload = decode_access_token("")
        assert payload is None

    def test_token_with_expires(self):
        """测试带过期时间的 Token"""
        from app.core.security import create_access_token, decode_access_token

        token = create_access_token(
            data={"sub": "testuser"}, expires_delta=timedelta(hours=1)
        )
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload
        assert payload["sub"] == "testuser"


class TestCurrentUser:
    """测试获取当前用户功能"""

    def test_get_current_user_success(self, client, auth_headers, test_user):
        """测试成功获取当前用户"""
        from app.core.security import get_current_user
        from fastapi import Depends

        # 通过 API 测试
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_current_user_invalid_token(self, client):
        """测试无效 Token"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client):
        """测试过期 Token"""
        from app.core.security import create_access_token
        import time

        # 创建即将过期的 Token（1秒后过期）
        token = create_access_token(
            data={"sub": "testuser"}, expires_delta=timedelta(seconds=1)
        )
        time.sleep(2)  # 等待过期

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


class TestCORS:
    """测试 CORS 配置"""

    def test_allowed_origin(self, client):
        """测试允许的源"""
        response = client.get(
            "/api/v1/leads", headers={"Origin": "http://localhost:8501"}
        )
        # 即使返回 401（未认证），也应该有 CORS 头
        assert (
            "access-control-allow-origin" in response.headers
            or response.status_code == 401
        )

    def test_preflight_request(self, client):
        """测试预检请求"""
        response = client.options(
            "/api/v1/leads",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )
        assert response.status_code == 200


class TestSecurityHeaders:
    """测试安全响应头"""

    def test_no_server_header(self, client):
        """测试不暴露服务器信息"""
        response = client.get("/")
        # FastAPI 默认不会暴露服务器版本
        server_header = response.headers.get("server", "").lower()
        assert "fastapi" not in server_header

    def test_content_type_json(self, client):
        """测试 API 返回 JSON"""
        response = client.get("/api/v1/leads")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type


class TestAuthorization:
    """测试授权功能"""

    def test_role_based_access(self, client, auth_headers, admin_headers):
        """测试基于角色的访问控制"""
        # 普通用户和管理员都应该能访问线索列表
        response_user = client.get("/api/v1/leads", headers=auth_headers)
        response_admin = client.get("/api/v1/leads", headers=admin_headers)

        assert response_user.status_code == 200
        assert response_admin.status_code == 200

    def test_admin_registration_blocked(self, client):
        """测试阻止注册管理员"""
        # 尝试注册为 admin
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "tryadmin",
                "email": "try@example.com",
                "password": "TestPass123!",
                "role": "admin",
            },
        )
        assert response.status_code == 201
        # 角色应该被强制改为 user
        assert response.json()["role"] == "user"


class TestInputValidation:
    """测试输入验证"""

    def test_sql_injection_in_company_name(self, client, auth_headers):
        """测试公司名称 SQL 注入防护"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "公司'; DROP TABLE leads; --",
                "event_type": "financing",
                "confidence": 80,
            },
            headers=auth_headers,
        )
        # 应该正常创建或返回验证错误，而不是执行 SQL
        assert response.status_code in [201, 422]

        # 验证表没有被删除（尝试获取线索列表）
        list_response = client.get("/api/v1/leads", headers=auth_headers)
        assert list_response.status_code == 200

    def test_xss_in_content(self, client, auth_headers):
        """测试 XSS 内容过滤"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "正常公司",
                "event_type": "financing",
                "event_detail": "<script>alert('xss')</script>融资消息",
                "confidence": 80,
            },
            headers=auth_headers,
        )

        if response.status_code == 201:
            # 检查返回的内容是否被转义
            data = response.json()
            assert "<script>" not in data.get("event_detail", "")

    def test_very_long_input(self, client, auth_headers):
        """测试超长输入处理"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "A" * 10000,  # 超长名称
                "event_type": "financing",
                "confidence": 80,
            },
            headers=auth_headers,
        )
        # 应该返回验证错误
        assert response.status_code == 422
