"""
虎嗅爬虫
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)


class HuxiuSpider:
    """虎嗅爬虫"""

    BASE_URL = "https://www.huxiu.com"

    def __init__(self):
        self.source_name = "虎嗅"
        self.source_type = "news"

    def fetch_articles(self, limit: int = 20) -> List[Dict]:
        """获取文章列表"""
        articles = []

        try:
            articles = self._fetch_by_html(limit)
        except Exception as e:
            logger.error(f"虎嗅爬取失败: {e}")

        return articles

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
                logger.warning(f"虎嗅返回 {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            articles = []
            seen_urls = set()

            # 查找所有文章链接
            links = soup.select('a[href*="/article/"]')

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

            logger.info(f"虎嗅获取到 {len(articles)} 篇文章")
            return articles

        except Exception as e:
            logger.error(f"虎嗅HTML解析失败: {e}")
            return []


def crawl_huxiu() -> List[Dict]:
    """爬取虎嗅文章"""
    spider = HuxiuSpider()
    return spider.fetch_articles()
