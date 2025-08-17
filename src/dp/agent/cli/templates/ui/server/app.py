"""
FastAPI application creation and configuration
"""
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.middleware import RequestLoggingMiddleware, HostValidationMiddleware
from config.agent_config import agentconfig

# Import all API endpoints
from api import websocket, files, sessions, config as config_api, projects


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI instance
    app = FastAPI(title="Agent WebSocket Server")
    
    # Get server config
    server_config = agentconfig.get_server_config()
    allowed_hosts = server_config.get("allowedHosts", ["localhost", "127.0.0.1", "0.0.0.0"])
    
    # Build allowed CORS origins
    allowed_origins = []
    for host in allowed_hosts:
        allowed_origins.extend([
            f"http://{host}:*",
            f"https://{host}:*",
            f"http://{host}",
            f"https://{host}"
        ])
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    # Note: middleware executes in reverse order, last added executes first
    # So add HostValidation first, then RequestLogging
    app.add_middleware(HostValidationMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Register routes
    # WebSocket endpoint
    app.add_websocket_route("/ws", websocket.websocket_endpoint)
    
    # API routes
    app.get("/api/status")(config_api.status)
    app.get("/api/config")(config_api.get_config)
    app.get("/api/files/tree")(files.get_file_tree)
    app.get("/api/files{file_path:path}")(files.get_file_content)
    app.delete("/api/sessions/clear")(sessions.clear_user_sessions)
    app.get("/api/sessions/export")(sessions.export_user_sessions)
    app.get("/api/projects")(projects.get_projects)
    
    # Mount static file service
    # Get UI static file directory
    ui_template_dir = Path(os.environ.get('UI_TEMPLATE_DIR', Path(__file__).parent.parent))
    static_dir = ui_template_dir / "frontend" / "ui-static"
    
    # Check if static file directory exists
    if static_dir.exists():
        # Define all other routes first, then mount static files last
        # This ensures API and WebSocket routes are matched first
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        print(f"📁 静态文件目录: {static_dir}")
    else:
        print(f"⚠️  静态文件目录不存在: {static_dir}")
    
    # Print Agent config info
    print(f"📂 Agent 配置: {agentconfig.config['agent']['module']}")
    print("🛠️  Agent 将在用户连接时根据其 AK 动态创建")
    
    return app