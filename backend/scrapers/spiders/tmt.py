"""
钛媒体爬虫
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TMTSpider:
    """钛媒体爬虫"""

    BASE_URL = "https://www.tmtpost.com"
    API_URL = "https://www.tmtpost.com/api/1/article/lists"

    def __init__(self):
        self.source_name = "钛媒体"
        self.source_type = "news"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """获取文章列表"""
        articles = []

        try:
            articles = self._fetch_by_api(limit)
        except Exception as e:
            logger.error(f"钛媒体爬取失败: {e}")

        return articles

    def _fetch_by_api(self, limit: int) -> List[Dict]:
        """通过API获取"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.tmtpost.com/",
            }

            params = {"limit": limit}

            response = requests.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=settings.crawl_timeout,
            )

            if response.status_code != 200:
                logger.warning(f"钛媒体API返回 {response.status_code}")
                return self._fetch_by_html(limit)

            data = response.json()
            items = data.get("data", []) if isinstance(data, dict) else []
            articles = []

            for item in items[:limit]:
                article = self._parse_item(item)
                if article:
                    articles.append(article)

            logger.info(f"钛媒体获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"钛媒体API失败: {e}")
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
                logger.warning(f"钛媒体返回 {response.status_code}")
                return []

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")
            articles = []
            seen_urls = set()

            links = soup.select('a[href*="/articles/"]')

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

            logger.info(f"钛媒体(HTML)获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"钛媒体HTML解析失败: {e}")
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
                "author": item.get("author", {}).get("nickname", "")
                if isinstance(item.get("author"), dict)
                else "",
                "source_name": self.source_name,
                "source_url": f"{self.BASE_URL}/articles/{item.get('id', '')}",
                "published_at": self._parse_timestamp(
                    item.get("published_at") or item.get("created_at")
                ),
                "source_type": self.source_type,
            }
        except Exception as e:
            logger.warning(f"解析钛媒体文章失败: {e}")
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
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return None
        except Exception:
            return None


def crawl_tmt() -> List[Dict]:
    """爬取钛媒体文章"""
    spider = TMTSpider()
    return spider.fetch_articles()
