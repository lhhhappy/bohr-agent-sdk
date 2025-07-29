"""
工具函数
"""
from typing import Tuple
from http.cookies import SimpleCookie
import socket


def get_ak_info_from_request(headers) -> Tuple[str, str]:
    """从请求头中提取AK信息"""
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
            
        return access_key, app_key
    return "", ""


def check_port_available(port: int) -> bool:
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except OSError:
        return False