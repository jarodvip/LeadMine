"""
主题过滤器
"""

from typing import List, Optional

from app.models import TopicMatchModeEnum


def matches_topic(
    title: Optional[str],
    content: Optional[str],
    keywords: Optional[List[str]],
    mode: TopicMatchModeEnum = TopicMatchModeEnum.any,
) -> bool:
    """判断文章是否匹配主题关键词"""
    if not keywords:
        return True

    text = f"{title or ''} {content or ''}"
    normalized_keywords = [kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()]

    if not normalized_keywords:
        return True

    if mode == TopicMatchModeEnum.all:
        return all(keyword in text for keyword in normalized_keywords)

    return any(keyword in text for keyword in normalized_keywords)
