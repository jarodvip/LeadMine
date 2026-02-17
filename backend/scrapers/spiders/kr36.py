"""
36氪爬虫
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Kr36Spider:
    """36氪爬虫"""

    BASE_URL = "https://www.36kr.com"
    API_URL = "https://www.36kr.com/pf/api/v1/post/feed"

    def __init__(self):
        self.source_name = "36氪"
        self.source_type = "news"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """获取文章列表"""
        articles = []

        try:
            # 方法1: 使用API接口
            articles = self._fetch_by_api(limit)

            # 备用: 如果API失败，使用网页解析
            if not articles:
                articles = self._fetch_by_html(limit)

        except Exception as e:
            logger.error(f"36氪爬取失败: {e}")

        return articles

    def _fetch_by_api(self, limit: int) -> List[Dict]:
        """通过API获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.36kr.com/",
            }

            params = {"type": 1, "per_page": limit, "page": 1}

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

            for item in data.get("data", {}).get("items", []):
                article = self._parse_api_item(item)
                if article:
                    articles.append(article)

            logger.info(f"36氪API获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.warning(f"36氪API失败: {e}")
            return []

    def _parse_api_item(self, item: Dict) -> Optional[Dict]:
        """解析API返回的条目"""
        try:
            return {
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "summary": item.get("summary", "")[:500] if item.get("summary") else "",
                "author": item.get("author_name", ""),
                "source_name": self.source_name,
                "source_url": f"{self.BASE_URL}{item.get('url', '')}",
                "published_at": self._parse_timestamp(item.get("published_at")),
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

            # 解析文章列表
            article_items = soup.select(".article-item") or soup.select(".kr-list-item")

            for item in article_items[:limit]:
                article = self._parse_html_item(item)
                if article:
                    articles.append(article)

            logger.info(f"36氪HTML获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"36氪HTML解析失败: {e}")
            return []

    def _parse_html_item(self, item) -> Optional[Dict]:
        """解析HTML条目"""
        try:
            title_elem = item.select_one("a.title, .article-title a, h2 a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            if not url.startswith("http"):
                url = f"{self.BASE_URL}{url}"

            # 尝试获取时间
            time_elem = item.select_one("time, .time, .date")
            published_at = None
            if time_elem:
                datetime_str = time_elem.get("datetime") or time_elem.get_text(
                    strip=True
                )
                published_at = self._parse_datetime_string(datetime_str)

            return {
                "title": title,
                "content": "",
                "summary": "",
                "author": "",
                "source_name": self.source_name,
                "source_url": url,
                "published_at": published_at,
                "source_type": self.source_type,
            }

        except Exception:
            return None

    def _parse_timestamp(self, timestamp: int) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp / 1000)
        except Exception:
            return None

    def _parse_datetime_string(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            from dateutil import parser

            return parser.parse(date_str)
        except Exception:
            return None


def crawl_kr36() -> List[Dict]:
    """爬取36氪文章"""
    spider = Kr36Spider()
    return spider.fetch_articles()
