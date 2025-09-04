"""
Utility functions
"""
import os
from typing import Tuple
from http.cookies import SimpleCookie
import socket

def get_ak_info_from_request(headers) -> Tuple[str, str]:
    """Extract AK info from request headers
    
    Priority:
    1. Get from Cookie (production environment)
    2. Get from environment variables (development debugging)
    3. Return empty string to allow user custom input (commented out restriction)
    """
    # First try to get from cookie
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
            
        # If got valid values from cookie, return directly
        if access_key or app_key:
            return access_key, app_key
    
    # If not in cookie, try to get from environment variables (for development debugging)
    access_key = os.environ.get("BOHR_ACCESS_KEY", "")
    app_key = os.environ.get("BOHR_APP_KEY", "")
    
    return access_key, app_key


def check_port_available(port: int) -> bool:
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except OSError:
        return False