# Configuration API
from fastapi import Request
from fastapi.responses import JSONResponse

from server.utils import get_ak_info_from_request
from config.agent_config import agentconfig


async def get_config(request: Request):
    """Get frontend configuration"""
    access_key, _ = get_ak_info_from_request(request.headers)
    return JSONResponse(content={
        "agent": agentconfig.config.get("agent", {}),
        "ui": agentconfig.get_ui_config(),
        "files": agentconfig.get_files_config(),
        "websocket": agentconfig.get_websocket_config(),
        "user_type": "registered" if access_key else "temporary"
    })


async def status():
    """API status"""
    return {
        "message": f"{agentconfig.config.get('agent', {}).get('name', 'Agent')} WebSocket 服务器正在运行",
        "mode": "session",
        "endpoints": {
            "websocket": "/ws",
            "files": "/api/files",
            "file_tree": "/api/files/tree",
            "config": "/api/config"
        }
    }