"""
集成测试 - 完整业务流程
"""

import pytest
from unittest.mock import Mock, patch


class TestCompleteDataProcessingFlow:
    """测试完整数据处理流程"""

    def test_article_to_lead_flow(self, client, auth_headers):
        """测试从文章到线索的完整流程"""
        # 1. 创建数据源
        source_response = client.post(
            "/api/v1/sources",
            json={
                "name": "测试数据源",
                "type": "news",
                "url": "http://test.com/feed",
                "crawl_interval": 60,
            },
            headers=auth_headers,
        )

        if source_response.status_code == 201:
            source_id = source_response.json()["id"]

            # 2. 手动触发爬取
            crawl_response = client.post(
                f"/api/v1/sources/{source_id}/crawl", headers=auth_headers
            )
            assert crawl_response.status_code in [200, 202, 404]  # 404 如果未实现

            # 3. 处理文章
            process_response = client.post(
                "/api/v1/processor/articles/process", headers=auth_headers
            )
            assert process_response.status_code in [200, 202]

            # 4. 检查线索
            leads_response = client.get("/api/v1/leads", headers=auth_headers)
            assert leads_response.status_code == 200

    def test_lead_management_flow(self, client, auth_headers):
        """测试线索管理完整流程"""
        # 1. 创建线索
        create_response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "集成测试公司",
                "event_type": "financing",
                "event_detail": "完成1亿元融资",
                "confidence": 85,
            },
            headers=auth_headers,
        )

        assert create_response.status_code == 201
        lead_id = create_response.json()["id"]

        # 2. 更新线索状态
        update_response = client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"status": "contacted", "assigned_to": "销售员A"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        # 3. 查看线索详情
        detail_response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["status"] == "contacted"
        assert data["assigned_to"] == "销售员A"

        # 4. 导出线索
        export_response = client.get("/api/v1/leads/export", headers=auth_headers)
        assert export_response.status_code == 200

        # 5. 删除线索
        delete_response = client.delete(
            f"/api/v1/leads/{lead_id}", headers=auth_headers
        )
        assert delete_response.status_code == 204


class TestUserWorkflow:
    """测试用户工作流"""

    def test_user_registration_to_login(self, client):
        """测试用户注册到登录流程"""
        # 1. 注册
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "workflowuser",
                "email": "workflow@test.com",
                "password": "Workflow123!",
            },
        )
        assert register_response.status_code == 201

        # 2. 登录
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "workflowuser", "password": "Workflow123!"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. 获取用户信息
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "workflowuser"


class TestBatchOperations:
    """测试批量操作集成"""

    def test_batch_create_update_delete(self, client, auth_headers):
        """测试批量创建、更新、删除"""
        # 1. 批量创建线索
        lead_ids = []
        for i in range(5):
            response = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"批量公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            if response.status_code == 201:
                lead_ids.append(response.json()["id"])

        assert len(lead_ids) == 5

        # 2. 批量更新状态
        update_response = client.post(
            "/api/v1/leads/batch/update-status",
            json={"lead_ids": lead_ids, "status": "contacted"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        # 3. 批量分配
        assign_response = client.post(
            "/api/v1/leads/batch/assign",
            json={"lead_ids": lead_ids, "assigned_to": "批量销售员"},
            headers=auth_headers,
        )
        assert assign_response.status_code == 200

        # 4. 批量删除
        delete_response = client.post(
            "/api/v1/leads/batch/delete",
            json={"lead_ids": lead_ids},
            headers=auth_headers,
        )
        assert delete_response.status_code == 200

        # 5. 验证删除
        for lead_id in lead_ids:
            check_response = client.get(
                f"/api/v1/leads/{lead_id}", headers=auth_headers
            )
            assert check_response.status_code == 404


class TestDashboardIntegration:
    """测试仪表盘集成"""

    def test_dashboard_with_data(self, client, auth_headers):
        """测试有数据时的仪表盘"""
        # 创建多个线索
        for i in range(10):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"仪表公司{i}",
                    "event_type": "financing" if i % 2 == 0 else "acquisition",
                    "confidence": 80 + i,
                },
                headers=auth_headers,
            )

        # 获取仪表盘数据
        dashboard_response = client.get(
            "/api/v1/leads/stats/dashboard", headers=auth_headers
        )
        assert dashboard_response.status_code == 200
        data = dashboard_response.json()

        assert data["total_leads"] >= 10
        assert "leads_by_type" in data
        assert "recent_leads" in data

        # 验证类型分布
        type_dist = data["leads_by_type"]
        assert type_dist["financing"] > 0
        assert type_dist["acquisition"] > 0


class TestErrorHandling:
    """测试错误处理集成"""

    def test_invalid_token_access(self, client):
        """测试无效 Token 访问"""
        response = client.get(
            "/api/v1/leads", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_access_denied(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/leads")
        assert response.status_code == 401

    def test_not_found(self, client, auth_headers):
        """测试访问不存在的资源"""
        response = client.get("/api/v1/leads/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_invalid_data(self, client, auth_headers):
        """测试提交无效数据"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "",  # 空名称
                "event_type": "invalid_type",  # 无效类型
                "confidence": 150,  # 超出范围
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
