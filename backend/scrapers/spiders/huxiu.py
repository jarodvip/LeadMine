"""
虎嗅爬虫
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class HuxiuSpider:
    """虎嗅爬虫"""

    BASE_URL = "https://www.huxiu.com"
    API_URL = "https://www.huxiu.com/api/v3_2/article/getArticleList"

    def __init__(self):
        self.source_name = "虎嗅"
        self.source_type = "news"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """获取文章列表"""
        articles = []

        try:
            # 尝试API
            articles = self._fetch_by_api(limit)

            # 备用HTML解析
            if not articles:
                articles = self._fetch_by_html(limit)

        except Exception as e:
            logger.error(f"虎嗅爬取失败: {e}")

        return articles

    def _fetch_by_api(self, limit: int) -> List[Dict]:
        """通过API获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.huxiu.com/",
            }

            params = {"platform": "pc", "page": 1, "size": limit}

            response = requests.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=settings.crawl_timeout,
            )

            if response.status_code != 200:
                return []

            data = response.json()
            articles = []

            for item in data.get("data", {}).get("list", []):
                article = self._parse_api_item(item)
                if article:
                    articles.append(article)

            logger.info(f"虎嗅API获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.warning(f"虎嗅API失败: {e}")
            return []

    def _parse_api_item(self, item: Dict) -> Optional[Dict]:
        """解析API返回的条目"""
        try:
            return {
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "summary": item.get("description", "")[:500]
                if item.get("description")
                else "",
                "author": item.get("author", {}).get("username", "")
                if isinstance(item.get("author"), dict)
                else "",
                "source_name": self.source_name,
                "source_url": f"{self.BASE_URL}{item.get('url', '')}",
                "published_at": self._parse_timestamp(item.get("publish_time")),
                "source_type": self.source_type,
            }
        except Exception:
            return None

    def _fetch_by_html(self, limit: int) -> List[Dict]:
        """通过HTML解析获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(
                self.BASE_URL, headers=headers, timeout=settings.crawl_timeout
            )

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            articles = []

            article_items = soup.select(
                ".article-item, .mod-article, .huxiu-article-item"
            )

            for item in article_items[:limit]:
                article = self._parse_html_item(item)
                if article:
                    articles.append(article)

            logger.info(f"虎嗅HTML获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"虎嗅HTML解析失败: {e}")
            return []

    def _parse_html_item(self, item) -> Optional[Dict]:
        """解析HTML条目"""
        try:
            title_elem = item.select_one("a.title, h3 a, .article-title a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            if not url.startswith("http"):
                url = f"{self.BASE_URL}{url}"

            return {
                "title": title,
                "content": "",
                "summary": "",
                "author": "",
                "source_name": self.source_name,
                "source_url": url,
                "published_at": None,
                "source_type": self.source_type,
            }

        except Exception:
            return None

    def _parse_timestamp(self, timestamp: int) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return None


def crawl_huxiu() -> List[Dict]:
    """爬取虎嗅文章"""
    spider = HuxiuSpider()
    return spider.fetch_articles()
