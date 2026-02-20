"""
数据清洗服务 - HTML清洗、文本提取、XSS过滤
"""

import re
from bs4 import BeautifulSoup

# 使用 BeautifulSoup 进行简单处理
import requests
from typing import Dict, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# XSS 危险标签和属性模式
XSS_DANGEROUS_TAGS = [
    "script",
    "iframe",
    "object",
    "embed",
    "form",
    "input",
    "textarea",
    "button",
    "link",
    "style",
    "meta",
    "base",
    "noscript",
    "frameset",
    "frame",
]

XSS_DANGEROUS_ATTRIBUTES = [
    "onabort",
    "onblur",
    "onchange",
    "onclick",
    "ondblclick",
    "onerror",
    "onfocus",
    "onkeydown",
    "onkeypress",
    "onkeyup",
    "onload",
    "onmousedown",
    "onmousemove",
    "onmouseout",
    "onmouseover",
    "onmouseup",
    "onreset",
    "onresize",
    "onselect",
    "onsubmit",
    "onunload",
    "javascript:",
    "data:",
    "vbscript:",
    "expression(",
    "mocha:",
    "livescript:",
]

XSS_EVENT_PATTERN = re.compile(r"on\w+\s*=", re.IGNORECASE)
XSS_SCRIPT_PATTERN = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
XSS_IFRAME_PATTERN = re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL)


class ArticleCleaner:
    """文章清洗器"""

    def __init__(self):
        self.html_tags_pattern = re.compile(r"<[^>]+>")
        self.extra_spaces_pattern = re.compile(r"\s+")

    def clean_html(self, html: str) -> str:
        """
        清洗HTML标签
        Args:
            html: 原始HTML
        Returns:
            纯文本
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, "html.parser")

            # 移除脚本和样式
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            # 获取文本
            text = soup.get_text(separator=" ")

            return self._clean_text(text)

        except Exception as e:
            logger.warning(f"HTML清洗失败: {e}")
            return self._simple_strip_tags(html)

    def _simple_strip_tags(self, html: str) -> str:
        """简单移除HTML标签"""
        text = self.html_tags_pattern.sub(" ", html)
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""

        # 移除多余空格
        text = self.extra_spaces_pattern.sub(" ", text)

        # 移除首尾空白
        text = text.strip()

        return text

    def sanitize_xss(self, html: str) -> str:
        """
        过滤 XSS 攻击内容
        Args:
            html: 可能包含 XSS 的 HTML 内容
        Returns:
            安全的纯文本
        """
        if not html:
            return ""

        try:
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(html, "html.parser")

            # 移除所有危险标签
            for tag in soup.find_all(XSS_DANGEROUS_TAGS):
                tag.decompose()

            # 移除危险属性
            for tag in soup.find_all(True):
                for attr in list(tag.attrs.keys()):
                    # 移除事件处理器
                    if attr.lower().startswith("on"):
                        del tag.attrs[attr]
                    # 移除危险的 URL 协议
                    elif attr in ["href", "src", "action", "formaction"]:
                        value = tag.attrs[attr]
                        if value and isinstance(value, str):
                            value_lower = value.lower().strip()
                            if any(
                                value_lower.startswith(d)
                                for d in ["javascript:", "data:", "vbscript:"]
                            ):
                                del tag.attrs[attr]

            # 获取纯文本
            text = soup.get_text(separator=" ")

            # 再次过滤可能的脚本残留
            text = XSS_SCRIPT_PATTERN.sub("", text)
            text = XSS_IFRAME_PATTERN.sub("", text)
            text = XSS_EVENT_PATTERN.sub("", text)

            return self._clean_text(text)

        except Exception as e:
            logger.warning(f"XSS 过滤失败: {e}")
            # 如果解析失败，使用简单过滤
            return self._simple_sanitize_xss(html)

    def _simple_sanitize_xss(self, text: str) -> str:
        """简单 XSS 过滤（备用方案）"""
        if not text:
            return ""

        # 移除 script 标签
        text = XSS_SCRIPT_PATTERN.sub("", text)
        # 移除 iframe
        text = XSS_IFRAME_PATTERN.sub("", text)
        # 移除事件处理器
        text = XSS_EVENT_PATTERN.sub("", text)
        # 移除 HTML 标签
        text = self.html_tags_pattern.sub(" ", text)
        # 清理空格
        text = self._clean_text(text)

        return text

    def extract_content(self, url: str) -> Optional[Dict]:
        """
        提取正文内容
        Args:
            url: 文章URL
        Returns:
            提取的内容字典
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(
                url,
                timeout=settings.crawl_timeout,
                headers=headers,
                allow_redirects=True,
            )

            if response.status_code != 200:
                logger.warning(f"获取文章失败: {url}, 状态码: {response.status_code}")
                return None

            return self.extract_content_from_html(response.text, url)

        except requests.RequestException as e:
            logger.error(f"提取文章内容失败 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"解析失败 {url}: {e}")
            return None

    def extract_content_from_html(self, html: str, url: str = "") -> Dict:
        """
        从HTML中提取内容
        Args:
            html: HTML内容
            url: 文章URL
        Returns:
            提取的内容字典
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            title = ""
            title_elem = soup.find("title") or soup.find("h1")
            if title_elem:
                title = title_elem.get_text(strip=True)

            content = self.clean_html(html)

            text = ""
            article = (
                soup.find("article")
                or soup.find("main")
                or soup.find(
                    "div", class_=lambda x: x and "content" in x.lower() if x else False
                )
            )
            if article:
                text = article.get_text(separator=" ", strip=True)

            return {
                "title": title,
                "content": content,
                "text": text[:500] if text else "",
            }

        except Exception as e:
            logger.warning(f"从HTML提取失败: {e}")
            return {"title": "", "content": self.clean_html(html), "text": ""}

    def extract_author(self, html: str) -> str:
        """提取作者信息"""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # 尝试多种选择器
            author_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                ".author",
                ".author-name",
                '[rel="author"]',
            ]

            for selector in author_selectors:
                elem = soup.select_one(selector)
                if elem:
                    content = elem.get("content") or elem.get_text(strip=True)
                    if content:
                        return content

            return ""

        except Exception:
            return ""

    def extract_published_time(self, html: str) -> Optional[str]:
        """提取发布时间"""
        try:
            soup = BeautifulSoup(html, "html.parser")

            time_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publishdate"]',
                "time[datetime]",
                ".publish-time",
                ".date",
            ]

            for selector in time_selectors:
                elem = soup.select_one(selector)
                if elem:
                    datetime_val = (
                        elem.get("datetime")
                        or elem.get("content")
                        or elem.get_text(strip=True)
                    )
                    if datetime_val:
                        return datetime_val

            return None

        except Exception:
            return None


def clean_article(article_data: Dict) -> Dict:
    """
    清洗单篇文章
    Args:
        article_data: 原始文章数据
    Returns:
        清洗后的文章数据
    """
    cleaner = ArticleCleaner()

    # 清洗标题（同时进行 XSS 过滤）
    if article_data.get("title"):
        article_data["title"] = cleaner.sanitize_xss(article_data["title"])

    # 清洗内容（同时进行 XSS 过滤）
    if article_data.get("content"):
        article_data["content"] = cleaner.sanitize_xss(article_data["content"])

    # 清洗摘要
    if article_data.get("summary"):
        article_data["summary"] = cleaner.sanitize_xss(article_data["summary"])

    return article_data


def sanitize_input(text: str) -> str:
    """
    通用输入净化函数
    Args:
        text: 用户输入文本
    Returns:
        净化后的安全文本
    """
    if not text:
        return ""

    cleaner = ArticleCleaner()
    return cleaner.sanitize_xss(text)
