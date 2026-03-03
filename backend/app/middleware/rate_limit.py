"""
限流中间件
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limit import check_rate_limit
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 限流中间件"""

    # 限流配置: (max_requests, window_seconds)
    RATE_LIMITS = {
        "default": (100, 60),  # 默认: 100请求/分钟
        "auth": (10, 60),  # 认证: 10请求/分钟
        "crawl": (5, 60),  # 爬虫: 5请求/分钟
        "export": (3, 60),  # 导出: 3请求/分钟
    }

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查和文档
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # 确定限流级别
        rate_limit_key = "default"
        if "/auth/login" in request.url.path:
            rate_limit_key = "auth"
        elif "/crawl" in request.url.path or "/sources" in request.url.path:
            rate_limit_key = "crawl"
        elif "/export" in request.url.path:
            rate_limit_key = "export"

        # 获取用户标识（IP 或用户ID）
        client_ip = request.client.host if request.client else "unknown"

        # 检查限流
        max_requests, window = self.RATE_LIMITS.get(
            rate_limit_key, self.RATE_LIMITS["default"]
        )
        key = f"rate_limit:{rate_limit_key}:{client_ip}"

        is_allowed, remaining = check_rate_limit(key, max_requests, window)

        if not is_allowed:
            logger.warning(f"限流触发: {client_ip}, {rate_limit_key}")
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试",
                headers={"X-RateLimit-Remaining": "0"},
            )

        # 添加限流头信息
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
