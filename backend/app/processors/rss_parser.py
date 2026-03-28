"""
RSS解析器 - 支持RSS和Atom feed
"""

import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dateutil import parser as date_parser
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RSSParser:
    """RSS/Atom解析器"""

    def __init__(self, source_config: Dict):
        self.config = source_config
        self.url = source_config.get("url")
        self.source_name = source_config.get("name", "RSS")
        source_type = source_config.get("type", "rss")
        if hasattr(source_type, "value"):
            source_type = source_type.value
        self.source_type = source_type or "rss"

    def fetch(self) -> List[Dict]:
        """获取RSS订阅内容"""
        if not self.url:
            logger.warning(f"RSS URL未配置: {self.source_name}")
            return []

        try:
            headers = {
                "User-Agent": "LeadMine RSS Parser/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml",
            }
            response = requests.get(
                self.url, timeout=settings.crawl_timeout, headers=headers
            )
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            articles = []

            for entry in feed.entries:
                article = self._parse_entry(entry)
                if article:
                    articles.append(article)

            logger.info(f"从 {self.source_name} 获取到 {len(articles)} 篇文章")
            return articles

        except requests.RequestException as e:
            logger.error(f"获取RSS失败 {self.source_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"解析RSS失败 {self.source_name}: {e}")
            return []

    def _parse_entry(self, entry) -> Optional[Dict]:
        """解析单条条目"""
        try:
            published_at = None
            if hasattr(entry, "published"):
                published_at = self._parse_date(entry.published)
            elif hasattr(entry, "updated"):
                published_at = self._parse_date(entry.updated)

            content = ""
            if hasattr(entry, "content"):
                content = entry.content[0].value if entry.content else ""
            elif hasattr(entry, "summary"):
                content = entry.summary

            link = ""
            if hasattr(entry, "link"):
                link = entry.link
            elif hasattr(entry, "links") and entry.links:
                link = entry.links[0].href

            author = ""
            if hasattr(entry, "author"):
                author = entry.author

            return {
                "title": self._clean_text(getattr(entry, "title", "无标题")),
                "content": self._clean_html(content),
                "summary": self._clean_text(getattr(entry, "summary", ""))[:500],
                "author": author,
                "source_name": self.source_name,
                "source_url": link,
                "published_at": published_at,
                "source_type": self.source_type,
            }

        except Exception as e:
            logger.warning(f"解析条目失败: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    def _clean_html(self, html: str) -> str:
        if not html:
            return ""
        import re

        text = re.sub(r"<[^>]+>", "", html)
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = " ".join(text.split())
        return text.strip()
