"""
FastAPI middleware definitions
"""
from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from server.utils import get_ak_info_from_request


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request middleware - for debugging"""
    async def dispatch(self, request: Request, call_next):
        try:
            # Process request info and AK
            access_key, _ = get_ak_info_from_request(request.headers)
        except:
            # Ignore any processing errors
            pass
        
        response = await call_next(request)
        return response


class HostValidationMiddleware(BaseHTTPMiddleware):
    """Host validation middleware"""
    def __init__(self, app, allowed_hosts):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts
    
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        # If allowed list contains "*", allow all hosts
        if "*" in self.allowed_hosts:
            response = await call_next(request)
            return response
        # Otherwise check if host is in allowed list
        if host and host not in self.allowed_hosts:
            return PlainTextResponse(
                content=f"Host '{host}' is not allowed",
                status_code=403
            )
        response = await call_next(request)
        return response