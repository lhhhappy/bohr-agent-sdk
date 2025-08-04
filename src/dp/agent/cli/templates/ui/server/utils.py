"""
工具函数
"""
import os
from typing import Tuple
from http.cookies import SimpleCookie
import socket

def get_ak_info_from_request(headers) -> Tuple[str, str]:
    """从请求头中提取AK信息
    
    优先级：
    1. 从 Cookie 中获取（生产环境）
    2. 从环境变量获取（开发调试）
    3. 返回空字符串允许用户自定义填写（注释掉限制）
    """
    # 首先尝试从 cookie 获取
    cookie_header = headers.get("cookie", "")
    if cookie_header:
        simple_cookie = SimpleCookie()
        simple_cookie.load(cookie_header)
        
        access_key = ""
        app_key = ""
        
        if "appAccessKey" in simple_cookie:
            access_key = simple_cookie["appAccessKey"].value
        if "clientName" in simple_cookie:
            app_key = simple_cookie["clientName"].value
            
        # 如果从 cookie 获取到了有效值，直接返回
        if access_key or app_key:
            return access_key, app_key
    
    # 如果 cookie 中没有，尝试从环境变量获取（用于开发调试）
    access_key = os.environ.get("BOHR_ACCESS_KEY", "")
    app_key = os.environ.get("BOHR_APP_KEY", "")
    
    if access_key or app_key:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"从环境变量获取 AK 信息: AK={access_key[:8] if access_key else 'None'}..., APP_KEY={app_key}")
    
    # 注释掉限制，允许用户在没有 AK 的情况下自定义填写
    # 返回空字符串，让用户可以在前端自行填写 AccessKey
    return access_key, app_key


def check_port_available(port: int) -> bool:
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except OSError:
        return False