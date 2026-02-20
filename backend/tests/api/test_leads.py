"""
线索管理接口测试
"""

import pytest


class TestLeadsList:
    """测试线索列表接口"""

    def test_get_leads_list_success(self, client, auth_headers, sample_lead):
        """测试获取线索列表"""
        response = client.get("/api/v1/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert len(data["data"]) > 0

    def test_get_leads_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/leads")
        assert response.status_code == 401

    def test_get_leads_pagination(self, client, auth_headers):
        """测试分页功能"""
        # 创建多个线索
        for i in range(5):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )

        # 测试第一页
        response = client.get("/api/v1/leads?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["page"] == 1

        # 测试第二页
        response = client.get("/api/v1/leads?page=2&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2

    def test_get_leads_filter_by_company(self, client, auth_headers, sample_lead):
        """测试按公司名称筛选"""
        response = client.get("/api/v1/leads?keyword=测试", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        assert "测试" in data["data"][0]["company_name"]

    def test_get_leads_filter_by_type(self, client, auth_headers, sample_lead):
        """测试按事件类型筛选"""
        response = client.get(
            "/api/v1/leads?event_type=financing", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]:
            assert item["event_type"] == "financing"

    def test_get_leads_filter_by_status(self, client, auth_headers, sample_lead):
        """测试按状态筛选"""
        response = client.get("/api/v1/leads?status=new", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]:
            assert item["status"] == "new"

    def test_get_leads_sorting(self, client, auth_headers):
        """测试排序功能"""
        # 按创建时间倒序
        response = client.get(
            "/api/v1/leads?sort_by=created_at&sort_order=desc", headers=auth_headers
        )
        assert response.status_code == 200

        # 按置信度排序
        response = client.get(
            "/api/v1/leads?sort_by=confidence&sort_order=desc", headers=auth_headers
        )
        assert response.status_code == 200


class TestLeadDetail:
    """测试线索详情接口"""

    def test_get_lead_detail_success(self, client, auth_headers, sample_lead):
        """测试获取线索详情"""
        lead_id = sample_lead["id"]
        response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["company_name"] == "测试公司"

    def test_get_lead_detail_not_found(self, client, auth_headers):
        """测试获取不存在的线索"""
        response = client.get("/api/v1/leads/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_lead_detail_invalid_id(self, client, auth_headers):
        """测试无效的线索 ID"""
        response = client.get("/api/v1/leads/invalid", headers=auth_headers)
        assert response.status_code == 422

    def test_get_lead_detail_unauthorized(self, client, sample_lead):
        """测试未授权访问"""
        response = client.get(f"/api/v1/leads/{sample_lead['id']}")
        assert response.status_code == 401


class TestLeadCreate:
    """测试创建线索接口"""

    def test_create_lead_success(self, client, auth_headers):
        """测试正常创建线索"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "新公司",
                "event_type": "financing",
                "event_detail": "完成2亿元B轮融资",
                "event_amount": "2亿元",
                "source_name": "36氪",
                "confidence": 90,
                "status": "new",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "新公司"
        assert data["event_type"] == "financing"
        assert data["id"] is not None

    def test_create_lead_minimal_data(self, client, auth_headers):
        """测试最小数据创建线索"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "简化公司",
                "event_type": "financing",
                "confidence": 80,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_create_lead_missing_required(self, client, auth_headers):
        """测试缺少必填字段"""
        response = client.post(
            "/api/v1/leads",
            json={
                "event_type": "financing"
                # 缺少 company_name
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_lead_invalid_confidence(self, client, auth_headers):
        """测试无效的置信度"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "测试公司",
                "event_type": "financing",
                "confidence": 150,  # 超过100
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_lead_invalid_event_type(self, client, auth_headers):
        """测试无效的事件类型"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "测试公司",
                "event_type": "invalid_type",
                "confidence": 80,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_lead_unauthorized(self, client):
        """测试未授权创建"""
        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "测试公司",
                "event_type": "financing",
                "confidence": 80,
            },
        )
        assert response.status_code == 401


class TestLeadUpdate:
    """测试更新线索接口"""

    def test_update_lead_success(self, client, auth_headers, sample_lead):
        """测试正常更新线索"""
        lead_id = sample_lead["id"]
        response = client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"status": "contacted", "assigned_to": "销售员A"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "contacted"
        assert data["assigned_to"] == "销售员A"

    def test_update_lead_partial(self, client, auth_headers, sample_lead):
        """测试部分更新"""
        lead_id = sample_lead["id"]
        original_name = sample_lead["company_name"]
        response = client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"status": "converted"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == original_name  # 未修改
        assert data["status"] == "converted"

    def test_update_lead_not_found(self, client, auth_headers):
        """测试更新不存在的线索"""
        response = client.patch(
            "/api/v1/leads/99999",
            json={"status": "contacted"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_lead_invalid_status(self, client, auth_headers, sample_lead):
        """测试无效的状态"""
        response = client.patch(
            f"/api/v1/leads/{sample_lead['id']}",
            json={"status": "invalid_status"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestLeadDelete:
    """测试删除线索接口"""

    def test_delete_lead_success(self, client, auth_headers, sample_lead):
        """测试正常删除线索"""
        lead_id = sample_lead["id"]
        response = client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 204

        # 验证已删除
        response = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_lead_not_found(self, client, auth_headers):
        """测试删除不存在的线索"""
        response = client.delete("/api/v1/leads/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_lead_unauthorized(self, client, sample_lead):
        """测试未授权删除"""
        response = client.delete(f"/api/v1/leads/{sample_lead['id']}")
        assert response.status_code == 401


class TestDashboardStats:
    """测试仪表盘统计接口"""

    def test_get_dashboard_stats(self, client, auth_headers, sample_lead):
        """测试获取仪表盘统计"""
        response = client.get("/api/v1/leads/stats/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "today_leads" in data
        assert "week_leads" in data
        assert "month_leads" in data
        assert "leads_by_type" in data
        assert "recent_leads" in data

    def test_get_dashboard_stats_empty(self, client, auth_headers):
        """测试无数据时的统计"""
        response = client.get("/api/v1/leads/stats/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 0


class TestBatchOperations:
    """测试批量操作"""

    def test_batch_update_status(self, client, auth_headers):
        """测试批量更新状态"""
        # 创建多个线索
        leads = []
        for i in range(3):
            resp = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"批量公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            leads.append(resp.json()["id"])

        # 批量更新状态
        response = client.post(
            "/api/v1/leads/batch/update-status",
            json={"lead_ids": leads, "status": "contacted"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # 验证更新
        for lead_id in leads:
            resp = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
            assert resp.json()["status"] == "contacted"

    def test_batch_assign(self, client, auth_headers):
        """测试批量分配"""
        leads = []
        for i in range(2):
            resp = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"分配公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            leads.append(resp.json()["id"])

        response = client.post(
            "/api/v1/leads/batch/assign",
            json={"lead_ids": leads, "assigned_to": "销售员A"},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_batch_delete(self, client, auth_headers):
        """测试批量删除"""
        leads = []
        for i in range(3):
            resp = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"删除公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            leads.append(resp.json()["id"])

        response = client.post(
            "/api/v1/leads/batch/delete", json={"lead_ids": leads}, headers=auth_headers
        )
        assert response.status_code == 200

        # 验证已删除
        for lead_id in leads:
            resp = client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
            assert resp.status_code == 404
