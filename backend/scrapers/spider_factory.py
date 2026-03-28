"""
爬虫工厂 - 统一爬虫入口
"""

from typing import Dict, List
from .spiders.kr36 import Kr36Spider
from .spiders.huxiu import HuxiuSpider
from .spiders.tmt import TMTSpider
from .spiders.cyzone import CyzoneSpider
from app.processors.rss_parser import RSSParser
import logging

logger = logging.getLogger(__name__)


class SpiderFactory:
    """爬虫工厂类"""

    SPIDERS = {
        "36kr": Kr36Spider,
        "36氪": Kr36Spider,
        "huxiu": HuxiuSpider,
        "虎嗅": HuxiuSpider,
        "tmt": TMTSpider,
        "钛媒体": TMTSpider,
        "cyzone": CyzoneSpider,
        "创业邦": CyzoneSpider,
    }

    @classmethod
    def get_spider(cls, source_name: str):
        """获取爬虫实例"""
        source_key = source_name.lower()
        spider_class = cls.SPIDERS.get(source_key)

        if spider_class:
            return spider_class()

        # 如果没有专用爬虫，尝试RSS
        return None

    @classmethod
    def crawl_source(cls, source_config: Dict) -> List[Dict]:
        """
        根据数据源配置爬取
        Args:
            source_config: 数据源配置，包含type, url, name等
        Returns:
            文章列表
        """
        source_type = source_config.get("type")
        if hasattr(source_type, "value"):
            source_type = source_type.value
        source_name = source_config.get("name", "")

        try:
            # 新闻网站爬虫
            if source_type == "news":
                spider = cls.get_spider(source_name)
                if spider:
                    return spider.fetch_articles()

            # RSS订阅 / 微信RSSHub
            elif source_type in {"rss", "wechat"}:
                parser = RSSParser(source_config)
                return parser.fetch()

            # 其他类型返回空列表
            logger.warning(f"不支持的数据源类型: {source_type}")
            return []

        except Exception as e:
            logger.error(f"爬取失败 {source_name}: {e}")
            return []


def crawl_all_sources(sources: List[Dict]) -> List[Dict]:
    """
    爬取所有启用的数据源
    Args:
        sources: 数据源配置列表
    Returns:
        所有文章
    """
    all_articles = []

    for source in sources:
        if not source.get("enabled", True):
            continue

        articles = SpiderFactory.crawl_source(source)
        all_articles.extend(articles)
        logger.info(f"从 {source.get('name')} 获取 {len(articles)} 篇文章")

    return all_articles
