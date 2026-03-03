"""
Redis 缓存服务 - Cache-Aside 模式
"""

import json
import redis
from typing import Any, Optional, Callable
from functools import wraps

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Redis 缓存服务"""

    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            self.enabled = True
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis 缓存服务已连接")
        except Exception as e:
            logger.warning(f"Redis 连接失败，缓存功能禁用: {e}")
            self.enabled = False
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"缓存获取失败: {key}, {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        if not self.enabled:
            return False

        try:
            self.redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"缓存设置失败: {key}, {e}")
            return False

    def delete(self, key: str):
        """删除缓存"""
        if not self.enabled:
            return

        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"缓存删除失败: {key}, {e}")

    def delete_pattern(self, pattern: str):
        """按模式删除缓存"""
        if not self.enabled:
            return

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"批量删除缓存: {pattern}, 数量: {len(keys)}")
        except Exception as e:
            logger.warning(f"批量删除缓存失败: {pattern}, {e}")

    def get_or_set(self, key: str, factory: Callable, ttl: int = 3600) -> Any:
        """获取或设置缓存 (Cache-Aside)"""
        # 先尝试获取缓存
        cached = self.get(key)
        if cached is not None:
            return cached

        # 缓存未命中，执行 factory 获取数据
        value = factory()

        # 设置缓存
        self.set(key, value, ttl)

        return value

    def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self.enabled:
            return 0

        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.warning(f"计数器递增失败: {key}, {e}")
            return 0

    def get_ttl(self, key: str) -> int:
        """获取剩余 TTL"""
        if not self.enabled:
            return 0

        try:
            return self.redis_client.ttl(key)
        except Exception:
            return 0


# 全局缓存服务
cache_service = CacheService()


def cache(ttl: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存 key
            cache_key = f"cache:{key_prefix or func.__name__}"
            if args:
                cache_key += (
                    f":{':'.join(str(a) for a in args if not isinstance(a, dict))}"
                )
            if kwargs:
                cache_key += (
                    f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
                )

            # 尝试从缓存获取
            cached = cache_service.get(cache_key)
            if cached is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached

            # 执行函数
            result = func(*args, **kwargs)

            # 设置缓存
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}, TTL: {ttl}s")

            return result

        return wrapper

    return decorator


# 缓存 key 常量
CACHE_KEYS = {
    "dashboard_stats": "cache:dashboard:stats",
    "leads_stats": "cache:leads:stats",
    "sources_list": "cache:sources:list",
    "article_detail": "cache:article:{id}",
    "lead_detail": "cache:lead:{id}",
}
