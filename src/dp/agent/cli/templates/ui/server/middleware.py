"""
FastAPI 中间件定义
"""
import logging
from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from server.utils import get_ak_info_from_request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 用于调试"""
    async def dispatch(self, request: Request, call_next):
        try:
            # 记录请求信息和 AK
            access_key, _ = get_ak_info_from_request(request.headers)
            if access_key:
                logger.info(f"收到请求: {request.method} {request.url.path} [AK: {access_key[:8]}...]")
            else:
                logger.info(f"收到请求: {request.method} {request.url.path} [临时用户]")
        except:
            # 忽略任何日志错误
            pass
        
        response = await call_next(request)
        return response


class HostValidationMiddleware(BaseHTTPMiddleware):
    """Host 验证中间件"""
    def __init__(self, app, allowed_hosts):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts
    
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        # 如果允许列表中包含 "*"，则允许所有主机
        if "*" in self.allowed_hosts:
            response = await call_next(request)
            return response
        # 否则检查主机是否在允许列表中
        if host and host not in self.allowed_hosts:
            logger.warning(f"拒绝访问: Host '{host}' 不在允许列表中")
            return PlainTextResponse(
                content=f"Host '{host}' is not allowed",
                status_code=403
            )
        response = await call_next(request)
        return response