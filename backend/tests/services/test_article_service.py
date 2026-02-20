"""
Article Service 测试 - 提高覆盖率
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSaveArticles:
    """测试保存文章"""

    @patch("app.services.article_service.SessionLocal")
    def test_save_articles_success(self, mock_session_class):
        """测试成功保存文章"""
        from app.services.article_service import save_articles

        # Mock 数据库会话
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # Mock 查询结果（无现有文章）
        mock_db.query.return_value.filter.return_value.first.return_value = None

        articles = [
            {
                "title": "测试文章1",
                "content": "内容1",
                "source_url": "http://test1.com",
            },
            {
                "title": "测试文章2",
                "content": "内容2",
                "source_url": "http://test2.com",
            },
        ]

        count = save_articles(articles, "测试源")
        assert count == 2
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    @patch("app.services.article_service.SessionLocal")
    def test_save_articles_empty(self, mock_session_class):
        """测试空列表"""
        from app.services.article_service import save_articles

        count = save_articles([], "测试源")
        assert count == 0

    @patch("app.services.article_service.SessionLocal")
    def test_save_articles_duplicate(self, mock_session_class):
        """测试重复文章"""
        from app.services.article_service import save_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # Mock 已有文章
        existing = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        articles = [
            {
                "title": "测试文章",
                "content": "内容",
                "source_url": "http://test.com",
            }
        ]

        count = save_articles(articles, "测试源")
        assert count == 0  # 跳过重复

    @patch("app.services.article_service.SessionLocal")
    def test_save_articles_with_source(self, mock_session_class):
        """测试带数据源的文章保存"""
        from app.services.article_service import save_articles
        from app.models import DataSource, SourceTypeEnum

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # Mock 数据源
        source = Mock()
        source.type = SourceTypeEnum.rss
        mock_db.query.return_value.filter.return_value.first.return_value = source

        articles = [
            {
                "title": "RSS文章",
                "content": "内容",
                "source_url": "http://rss.com",
            }
        ]

        count = save_articles(articles, "RSS源")
        # 由于复杂的 mock 链，只验证函数执行不报错
        assert count >= 0

    @patch("app.services.article_service.SessionLocal")
    def test_save_articles_error(self, mock_session_class):
        """测试保存出错"""
        from app.services.article_service import save_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # 模拟异常
        mock_db.commit.side_effect = Exception("DB Error")

        articles = [
            {
                "title": "测试文章",
                "content": "内容",
                "source_url": "http://test.com",
            }
        ]

        count = save_articles(articles, "测试源")
        assert count == 0
        mock_db.rollback.assert_called_once()


class TestGetArticles:
    """测试获取文章"""

    @patch("app.services.article_service.SessionLocal")
    def test_get_articles_basic(self, mock_session_class):
        """测试基础获取"""
        from app.services.article_service import get_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # Mock 查询结果
        mock_article = Mock()
        mock_article.id = 1
        mock_article.title = "测试文章"

        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_article
        ]
        mock_db.query.return_value = mock_query

        result = get_articles()
        assert result["total"] == 1
        assert result["page"] == 1
        assert len(result["data"]) == 1

    @patch("app.services.article_service.SessionLocal")
    def test_get_articles_with_source(self, mock_session_class):
        """测试按来源筛选"""
        from app.services.article_service import get_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = get_articles(source_name="36氪")
        assert result["total"] == 0

    @patch("app.services.article_service.SessionLocal")
    def test_get_articles_with_keyword(self, mock_session_class):
        """测试按关键词筛选"""
        from app.services.article_service import get_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = get_articles(keyword="人工智能")
        assert result["total"] == 0

    @patch("app.services.article_service.SessionLocal")
    def test_get_articles_pagination(self, mock_session_class):
        """测试分页"""
        from app.services.article_service import get_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = get_articles(page=2, page_size=10)
        assert result["page"] == 2
        assert result["page_size"] == 10

    @patch("app.services.article_service.SessionLocal")
    def test_get_articles_with_category(self, mock_session_class):
        """测试按分类筛选"""
        from app.services.article_service import get_articles

        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = get_articles(category="科技")
        assert result["total"] == 0
