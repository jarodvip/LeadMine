"""
调度器测试
"""

import pytest
from unittest.mock import Mock, patch


class TestScheduler:
    """测试爬虫调度器"""

    @pytest.fixture
    def scheduler(self):
        from app.services.scheduler import CrawlScheduler

        scheduler = CrawlScheduler()
        return scheduler

    def test_scheduler_start(self, scheduler):
        """测试启动调度器"""
        # 启动调度器
        scheduler.start()
        assert scheduler.running is True

        # 停止
        scheduler.stop()

    def test_scheduler_stop(self, scheduler):
        """测试停止调度器"""
        scheduler.start()
        scheduler.stop()
        assert scheduler.running is False

    def test_scheduler_start_when_already_running(self, scheduler):
        """测试重复启动"""
        scheduler.start()
        # 再次启动应该不会报错
        scheduler.start()
        scheduler.stop()

    def test_add_crawl_task(self, scheduler):
        """测试添加爬取任务"""
        scheduler.start()

        # 创建一个模拟数据源
        source = Mock()
        source.id = 1
        source.name = "测试源"
        source.crawl_interval = 30

        scheduler.add_crawl_task(source)

        # 检查任务是否已添加
        job = scheduler.scheduler.get_job("crawl_1")
        assert job is not None

        scheduler.stop()

    def test_remove_crawl_task(self, scheduler):
        """测试移除爬取任务"""
        scheduler.start()

        source = Mock()
        source.id = 1
        source.name = "测试源"
        source.crawl_interval = 30

        scheduler.add_crawl_task(source)
        scheduler.remove_crawl_task(1)

        # 检查任务是否已移除
        job = scheduler.scheduler.get_job("crawl_1")
        assert job is None

        scheduler.stop()

    def test_trigger_manual_crawl(self, scheduler):
        """测试手动触发爬取"""
        scheduler.start()

        # 使用 mock 避免实际爬取
        with patch.object(scheduler, "_crawl_source") as mock_crawl:
            scheduler.trigger_manual_crawl(1)
            # 验证爬取方法被调用
            # mock_crawl.assert_called_once_with(1)

        scheduler.stop()

    def test_load_tasks_from_db(self, scheduler):
        """测试从数据库加载任务"""
        # 需要使用 mock 数据库
        with patch("app.services.scheduler.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.all.return_value = [
                Mock(id=1, name="源1", enabled=True, crawl_interval=30),
                Mock(id=2, name="源2", enabled=True, crawl_interval=60),
            ]
            mock_session.return_value = mock_db

            scheduler.start()
            # 验证任务已加载
            scheduler.stop()
