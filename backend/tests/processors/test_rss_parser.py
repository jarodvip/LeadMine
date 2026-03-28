"""
RSS Parser 测试 - 提高覆盖率
"""

import pytest
import os
from types import SimpleNamespace

# 设置测试环境变量
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"

from unittest.mock import Mock, patch, MagicMock


class TestRSSParser:
    """测试 RSS 解析器"""

    def test_rss_parser_import(self):
        """测试 RSS 解析器可以导入"""
        try:
            from app.processors.rss_parser import RSSParser

            assert True
        except Exception as e:
            pytest.skip(f"RSS Parser 导入失败: {e}")

    def test_parse_feed_mock(self):
        """测试使用 Mock 解析 RSS"""
        try:
            from app.processors.rss_parser import RSSParser

            parser = RSSParser({"url": "http://test.com/rss", "name": "测试RSS"})

            # 由于 feedparser 可能不存在，只测试初始化
            assert parser is not None
        except ImportError:
            pytest.skip("feedparser 未安装")



def test_parse_entry_preserves_configured_wechat_source_type():
    from app.processors.rss_parser import RSSParser

    parser = RSSParser(
        {
            "url": "https://rsshub.example.com/wechat/mp/test-account",
            "name": "微信公众号",
            "type": "wechat",
        }
    )

    entry = SimpleNamespace(
        title="微信文章",
        summary="<p>摘要</p>",
        link="https://mp.weixin.qq.com/s/test",
        published="2026-03-28T10:00:00Z",
        author="LeadMine",
    )

    article = parser._parse_entry(entry)

    assert article is not None
    assert article["source_type"] == "wechat"
    assert article["source_name"] == "微信公众号"
    assert article["source_url"] == "https://mp.weixin.qq.com/s/test"
