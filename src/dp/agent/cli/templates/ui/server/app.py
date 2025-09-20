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
from api import websocket, files, sessions, config as config_api, projects, debug
from api.files_upload import upload_files
from api.files_user import get_user_file


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
    app.get("/api/files/{user_id}/output/{filename}")(get_user_file)
    app.get("/api/files{file_path:path}")(files.get_file_content)
    app.get("/api/download/file{file_path:path}")(files.download_file)
    app.get("/api/download/folder{folder_path:path}")(files.download_folder)
    app.post("/api/upload")(upload_files)
    app.delete("/api/files{file_path:path}")(files.delete_file)
    app.delete("/api/sessions/clear")(sessions.clear_user_sessions)
    app.get("/api/sessions/export")(sessions.export_user_sessions)
    app.get("/api/projects")(projects.get_projects)
    
    # Debug routes (only in development)
    if os.environ.get('DEBUG', '').lower() in ['true', '1', 'yes']:
        app.get("/api/debug/runners")(debug.get_runner_status)
        app.get("/api/debug/config")(debug.get_config_status)
        app.get("/api/debug/sessions")(debug.get_session_status)
        app.get("/api/debug/test-agent")(debug.test_agent_creation)
    
    # Mount static file service
    # Get UI static file directory
    ui_template_dir = Path(os.environ.get('UI_TEMPLATE_DIR', Path(__file__).parent.parent))
    static_dir = ui_template_dir / "frontend" / "ui-static"
    
    # Check if static file directory exists
    if static_dir.exists():
        # Define all other routes first, then mount static files last
        # This ensures API and WebSocket routes are matched first
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        print(f"📁 Static files directory: {static_dir}")
    else:
        print(f"⚠️  Static files directory does not exist: {static_dir}")
    
    # Print Agent config info
    print(f"📂 Agent configuration: {agentconfig.config['agent']['module']}")
    print("🛠️  Agent will be dynamically created based on user AK when connecting")
    
    return app