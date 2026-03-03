"""
API 响应缓存中间件
"""

import hashlib
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.cache import cache_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """API 响应缓存中间件"""

    # 缓存配置: 路径 -> (ttl秒, 是否缓存)
    CACHE_CONFIG = {
        "/api/v1/leads/stats/dashboard": (300, True),  # 仪表盘 5分钟
        "/api/v1/leads": (60, True),  # 线索列表 1分钟
        "/api/v1/articles": (120, True),  # 文章列表 2分钟
        "/api/v1/sources": (300, True),  # 数据源 5分钟
    }

    # 不缓存的路径
    EXCLUDE_PATHS = [
        "/auth/login",
        "/auth/register",
        "/processor",
        "/export",
        "/crawl",
    ]

    async def dispatch(self, request: Request, call_next):
        # 只处理 GET 请求
        if request.method != "GET":
            return await call_next(request)

        # 检查是否需要缓存
        path = request.url.path
        should_cache = False
        ttl = 60

        for cached_path, (_, cache_enabled) in self.CACHE_CONFIG.items():
            if path.startswith(cached_path):
                if cache_enabled:
                    should_cache = True
                    ttl = self.CACHE_CONFIG[cached_path][0]
                break

        # 检查排除路径
        for exclude in self.EXCLUDE_PATHS:
            if exclude in path:
                should_cache = False
                break

        if not should_cache:
            return await call_next(request)

        # 生成缓存 key
        cache_key = self._generate_cache_key(request)

        # 尝试从缓存获取
        cached_response = cache_service.get(cache_key)
        if cached_response:
            logger.debug(f"API 缓存命中: {path}")
            from starlette.responses import JSONResponse

            return JSONResponse(content=cached_response)

        # 执行请求
        response = await call_next(request)

        # 如果成功，缓存响应
        if response.status_code == 200:
            try:
                # 读取响应内容
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # 解析 JSON
                content = json.loads(body)

                # 缓存
                cache_service.set(cache_key, content, ttl)
                logger.debug(f"API 响应缓存: {path}, TTL: {ttl}s")

                # 返回响应
                from starlette.responses import JSONResponse

                return JSONResponse(content=content)

            except Exception as e:
                logger.warning(f"缓存响应失败: {path}, {e}")

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存 key"""
        # 使用路径 + 查询参数 hash
        key_parts = [request.url.path]
        if request.query_params:
            key_parts.append(str(request.query_params))

        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"api_cache:{key_hash}"


def invalidate_cache(pattern: str):
    """清除缓存"""
    cache_service.delete_pattern("api_cache:*")
    cache_service.delete_pattern("cache:*")
    logger.info(f"缓存已清除: {pattern}")
