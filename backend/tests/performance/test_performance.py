"""
性能测试 - API 响应时间和并发处理
"""

import pytest
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


class TestAPIResponseTime:
    """测试 API 响应时间"""

    def test_auth_login_response_time(self, client, test_user):
        """测试登录接口响应时间"""
        start_time = time.time()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "TestPass123!"},
        )

        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 2.0  # 响应时间应小于2秒

    def test_get_leads_response_time(self, client, auth_headers):
        """测试获取线索列表响应时间"""
        # 先创建一些数据
        for i in range(10):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"性能测试公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )

        start_time = time.time()
        response = client.get("/api/v1/leads", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 1.0  # 响应时间应小于1秒

    def test_create_lead_response_time(self, client, auth_headers):
        """测试创建线索响应时间"""
        start_time = time.time()

        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "响应时间测试",
                "event_type": "financing",
                "confidence": 85,
            },
            headers=auth_headers,
        )

        elapsed_time = time.time() - start_time

        assert response.status_code == 201
        assert elapsed_time < 1.0

    def test_dashboard_response_time(self, client, auth_headers):
        """测试仪表盘响应时间"""
        start_time = time.time()

        response = client.get("/api/v1/leads/stats/dashboard", headers=auth_headers)

        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 0.5  # 仪表盘应该很快


class TestConcurrentAccess:
    """测试并发访问"""

    def test_concurrent_leads_read(self, client, auth_headers):
        """测试并发读取线索"""
        # 先创建一些数据
        for i in range(20):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"并发公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )

        def fetch_leads():
            response = client.get("/api/v1/leads?page_size=10", headers=auth_headers)
            return response.status_code == 200

        # 并发10个请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_leads) for _ in range(10)]
            results = [f.result() for f in futures]

        assert all(results), "所有并发请求都应该成功"

    def test_concurrent_login(self, client, test_user):
        """测试并发登录"""

        def login():
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "TestPass123!"},
            )
            return response.status_code == 200

        # 并发5个登录请求
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login) for _ in range(5)]
            results = [f.result() for f in futures]

        assert all(results), "所有并发登录都应该成功"

    def test_concurrent_create_lead(self, client, auth_headers):
        """测试并发创建线索"""
        success_count = [0]

        def create_lead(index):
            response = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"并发创建{index}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            if response.status_code == 201:
                success_count[0] += 1
            return response.status_code

        # 并发创建10个线索
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_lead, i) for i in range(10)]
            results = [f.result() for f in futures]

        # 至少应该有部分成功
        assert success_count[0] >= 8, f"至少8个应该成功，实际{success_count[0]}"


class TestLoadTesting:
    """负载测试"""

    @pytest.mark.slow
    def test_batch_create_performance(self, client, auth_headers):
        """测试批量创建性能"""
        start_time = time.time()

        # 批量创建50个线索
        for i in range(50):
            response = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"批量性能{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            assert response.status_code == 201

        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / 50

        assert avg_time < 0.5, f"平均创建时间应小于0.5秒，实际{avg_time}秒"

    @pytest.mark.slow
    def test_large_list_pagination(self, client, auth_headers):
        """测试大量数据分页性能"""
        # 创建100个线索
        for i in range(100):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"大量数据{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )

        # 测试不同分页大小
        for page_size in [10, 20, 50]:
            start_time = time.time()
            response = client.get(
                f"/api/v1/leads?page_size={page_size}", headers=auth_headers
            )
            elapsed_time = time.time() - start_time

            assert response.status_code == 200
            assert elapsed_time < 1.0, f"分页大小{page_size}响应时间应小于1秒"


class TestMemoryUsage:
    """测试内存使用"""

    def test_large_content_handling(self, client, auth_headers):
        """测试处理大内容"""
        large_content = "这是内容。" * 1000  # 大内容

        response = client.post(
            "/api/v1/leads",
            json={
                "company_name": "大内容测试",
                "event_type": "financing",
                "event_detail": large_content,
                "confidence": 80,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201

    def test_batch_operations_performance(self, client, auth_headers):
        """测试批量操作性能"""
        # 创建20个线索用于批量操作
        lead_ids = []
        for i in range(20):
            resp = client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"批量操作{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )
            if resp.status_code == 201:
                lead_ids.append(resp.json()["id"])

        # 测试批量更新性能
        start_time = time.time()
        response = client.post(
            "/api/v1/leads/batch/update-status",
            json={"lead_ids": lead_ids, "status": "contacted"},
            headers=auth_headers,
        )
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 2.0  # 20个线索的批量更新应小于2秒


class TestDatabaseQueryPerformance:
    """测试数据库查询性能"""

    def test_filtered_query_performance(self, client, auth_headers):
        """测试带筛选的查询性能"""
        # 创建混合类型的线索
        types = ["financing", "acquisition", "product"]
        for i in range(30):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"筛选测试{i}",
                    "event_type": types[i % 3],
                    "confidence": 80,
                },
                headers=auth_headers,
            )

        # 测试筛选查询性能
        for event_type in types:
            start_time = time.time()
            response = client.get(
                f"/api/v1/leads?event_type={event_type}", headers=auth_headers
            )
            elapsed_time = time.time() - start_time

            assert response.status_code == 200
            assert elapsed_time < 1.0, f"{event_type}筛选查询应小于1秒"

    def test_search_performance(self, client, auth_headers):
        """测试搜索性能"""
        # 创建数据
        for i in range(50):
            client.post(
                "/api/v1/leads",
                json={
                    "company_name": f"搜索性能公司{i}",
                    "event_type": "financing",
                    "confidence": 80,
                },
                headers=auth_headers,
            )

        start_time = time.time()
        response = client.get("/api/v1/leads?keyword=搜索性能", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 1.0
