"""
创业邦爬虫
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CyzoneSpider:
    """创业邦爬虫"""

    BASE_URL = "https://www.cyzone.cn"
    API_URL = "https://www.cyzone.cn/api/index.php"

    def __init__(self):
        self.source_name = "创业邦"
        self.source_type = "news"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """获取文章列表"""
        articles = []

        try:
            articles = self._fetch_by_api(limit)
        except Exception as e:
            logger.error(f"创业邦爬取失败: {e}")

        return articles

    def _fetch_by_api(self, limit: int) -> List[Dict]:
        """通过API获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.cyzone.cn/",
            }

            params = {
                "m": "index",
                "c": "ajax",
                "a": "get_news_list",
                "type": 0,
                "page": 1,
                "size": limit,
            }

            response = requests.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=settings.crawl_timeout,
            )

            if response.status_code != 200:
                logger.warning(f"创业邦API返回 {response.status_code}")
                return self._fetch_by_html(limit)

            data = response.json()
            items = data.get("list", []) if isinstance(data, dict) else []
            articles = []

            for item in items[:limit]:
                article = self._parse_item(item)
                if article:
                    articles.append(article)

            logger.info(f"创业邦获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"创业邦API失败: {e}")
            return self._fetch_by_html(limit)

    def _fetch_by_html(self, limit: int) -> List[Dict]:
        """通过HTML解析获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }

            response = requests.get(
                self.BASE_URL, headers=headers, timeout=settings.crawl_timeout
            )

            if response.status_code != 200:
                logger.warning(f"创业邦返回 {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            articles = []
            seen_urls = set()

            links = soup.select('a[href*="/event/"]')
            links += soup.select('a[href*="/article/"]')

            for link in links:
                if len(articles) >= limit:
                    break

                title = link.get_text(strip=True)
                url = link.get("href", "")

                if not title or len(title) < 5:
                    continue

                if not url.startswith("http"):
                    url = f"{self.BASE_URL}{url}"

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                articles.append(
                    {
                        "title": title[:200],
                        "content": "",
                        "summary": "",
                        "author": "",
                        "source_name": self.source_name,
                        "source_url": url,
                        "published_at": datetime.now(),
                        "source_type": self.source_type,
                    }
                )

            logger.info(f"创业邦(HTML)获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"创业邦HTML解析失败: {e}")
            return []

    def _parse_item(self, item: Dict) -> Optional[Dict]:
        """解析文章条目"""
        try:
            return {
                "title": item.get("title", "")[:200],
                "content": item.get("content", "") or item.get("description", ""),
                "summary": item.get("description", "")[:500]
                if item.get("description")
                else "",
                "author": item.get("author", ""),
                "source_name": self.source_name,
                "source_url": f"{self.BASE_URL}{item.get('url', '')}",
                "published_at": self._parse_timestamp(
                    item.get("add_time") or item.get("created_at")
                ),
                "source_type": self.source_type,
            }
        except Exception as e:
            logger.warning(f"解析创业邦文章失败: {e}")
            return None

    def _parse_timestamp(self, timestamp) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp:
            return None
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return None
        except Exception:
            return None


def crawl_cyzone() -> List[Dict]:
    """爬取创业邦文章"""
    spider = CyzoneSpider()
    return spider.fetch_articles()
