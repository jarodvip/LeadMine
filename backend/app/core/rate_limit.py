"""
API 限流服务 - 基于 Redis 令牌桶算法
"""

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """令牌桶限流器"""

    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.enabled = True

    def check_rate_limit(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        检查请求是否超过限流
        Returns: (is_allowed, remaining_requests)
        """
        if not self.enabled:
            return True, max_requests

        try:
            current = self.redis_client.get(key)
            if current is None:
                self.redis_client.setex(key, window_seconds, 1)
                return True, max_requests - 1

            current = int(current)
            if current >= max_requests:
                return False, 0

            self.redis_client.incr(key)
            return True, max_requests - current - 1

        except Exception as e:
            logger.warning(f"限流检查失败: {e}")
            return True, max_requests  # 失败时允许请求

    def reset(self, key: str):
        """重置限流"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"重置限流失败: {e}")


# 全局限流器
rate_limiter = RateLimiter(settings.redis_url)


def check_rate_limit(
    key: str,
    max_requests: int = 100,
    window_seconds: int = 60,
) -> tuple[bool, int]:
    """检查限流"""
    return rate_limiter.check_rate_limit(key, max_requests, window_seconds)
