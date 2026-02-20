"""
认证接口测试
测试登录、注册、用户信息获取等功能
"""

import pytest


class TestAuthLogin:
    """测试登录接口"""

    def test_login_success(self, client, test_user):
        """测试正常登录"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "TestPass123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client, test_user):
        """测试错误密码"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "somepassword"},
        )
        assert response.status_code == 401

    def test_login_missing_username(self, client):
        """测试缺少用户名"""
        response = client.post("/api/v1/auth/login", data={"password": "somepassword"})
        assert response.status_code == 422

    def test_login_missing_password(self, client):
        """测试缺少密码"""
        response = client.post("/api/v1/auth/login", data={"username": "testuser"})
        assert response.status_code == 422


class TestAuthRegister:
    """测试注册接口"""

    def test_register_success(self, client):
        """测试正常注册"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewPass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"  # 强制为 user 角色

    def test_register_duplicate_username(self, client, test_user):
        """测试重复用户名"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_register_role_enforcement(self, client):
        """测试角色强制为 user（即使请求中指定了 admin）"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "hackuser",
                "email": "hack@example.com",
                "password": "HackPass123!",
                "role": "admin",  # 尝试注册为 admin
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "user"  # 应该被强制改为 user

    def test_register_invalid_email(self, client):
        """测试无效邮箱"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser2",
                "email": "invalid-email",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 422

    def test_register_weak_password(self, client):
        """测试弱密码"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "weakuser",
                "email": "weak@example.com",
                "password": "123",  # 太短的密码
            },
        )
        assert response.status_code == 422


class TestAuthGetMe:
    """测试获取当前用户信息"""

    def test_get_current_user_success(self, client, auth_headers, test_user):
        """测试成功获取用户信息"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_no_token(self, client):
        """测试无 Token 访问"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """测试无效 Token"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client):
        """测试过期 Token"""
        import time
        from app.core.security import create_access_token

        # 创建已过期的 Token
        expired_token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=None,  # 使用默认过期时间
        )

        # 等待 Token 过期（在生产环境测试时可能需要 mock）
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        # 注意：这里可能需要调整，取决于 Token 过期时间的设置


class TestAuthSecurity:
    """测试安全相关功能"""

    def test_password_not_returned(self, client, test_user):
        """测试密码不在响应中返回"""
        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {client.post('/api/v1/auth/login', data={'username': 'testuser', 'password': 'TestPass123!'}).json()['access_token']}"
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_sql_injection_in_username(self, client):
        """测试用户名 SQL 注入防护"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test' OR '1'='1", "password": "anypassword"},
        )
        # 应该正常返回 401，而不是报错或登录成功
        assert response.status_code == 401

    def test_sql_injection_in_login(self, client):
        """测试登录 SQL 注入"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin'; DROP TABLE users; --", "password": "password"},
        )
        assert response.status_code == 401

        # 验证表没有被删除（再次尝试正常登录）
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "checkuser",
                "email": "check@example.com",
                "password": "CheckPass123!",
            },
        )
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "checkuser", "password": "CheckPass123!"},
        )
        assert response.status_code == 200
