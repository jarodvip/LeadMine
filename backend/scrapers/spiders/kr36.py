"""
36氪爬虫
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Kr36Spider:
    """36氪爬虫"""

    BASE_URL = "https://www.36kr.com"
    # 使用快讯API
    NEWS_API = "https://www.36kr.com/api/newsflash"

    def __init__(self):
        self.source_name = "36氪"
        self.source_type = "news"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """获取文章列表"""
        articles = []

        try:
            articles = self._fetch_newsflash(limit)
        except Exception as e:
            logger.error(f"36氪爬取失败: {e}")

        return articles

    def _fetch_newsflash(self, limit: int) -> List[Dict]:
        """通过快讯API获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.36kr.com/",
            }

            params = {"per_page": limit}

            response = requests.get(
                self.NEWS_API,
                params=params,
                headers=headers,
                timeout=settings.crawl_timeout,
            )

            if response.status_code != 200:
                logger.warning(f"36氪API返回 {response.status_code}")
                return []

            data = response.json()
            items = data.get("data", {}).get("items", [])
            articles = []

            for item in items[:limit]:
                article = self._parse_newsflash_item(item)
                if article:
                    articles.append(article)

            logger.info(f"36氪获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"36氪API失败: {e}")
            return []

    def _parse_newsflash_item(self, item: Dict) -> Optional[Dict]:
        """解析快讯条目"""
        try:
            news_id = item.get("id", "")
            return {
                "title": item.get("title", "") or item.get("description", "")[:100],
                "content": item.get("description", "") or item.get("content", ""),
                "summary": (item.get("description", "") or "")[:500],
                "author": "",
                "source_name": self.source_name,
                "source_url": f"{self.BASE_URL}/news/{news_id}",
                "published_at": self._parse_timestamp(
                    item.get("published_at") or item.get("created_at")
                ),
                "source_type": self.source_type,
            }
        except Exception as e:
            logger.warning(f"解析快讯失败: {e}")
            return None

    def _parse_timestamp(self, timestamp) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp:
            return None
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(
                    timestamp / 1000 if timestamp > 1e10 else timestamp
                )
            return None
        except Exception:
            return None


def crawl_kr36() -> List[Dict]:
    """爬取36氪文章"""
    spider = Kr36Spider()
    return spider.fetch_articles()
