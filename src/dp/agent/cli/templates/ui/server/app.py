"""
FastAPI 应用创建和配置
"""
import os
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.middleware import RequestLoggingMiddleware, HostValidationMiddleware
from config.agent_config import agentconfig

# 导入所有 API 端点
from api import websocket, files, sessions, config as config_api

logger = logging.getLogger(__name__)


def setup_logging():
    """配置日志"""
    # 检查是否已经有 handler，避免重复添加
    if not logger.handlers:
        # 创建文件 handler，使用覆盖模式
        file_handler = logging.FileHandler('websocket.log', mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加 handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        
        # 在日志文件中添加会话分隔符
        logger.info("="*80)
        logger.info(f"新的 WebSocket 服务器会话开始于 {datetime.now()}")
        logger.info("="*80)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    # 设置日志
    setup_logging()
    
    # 创建 FastAPI 实例
    app = FastAPI(title="Agent WebSocket Server")
    
    # 获取服务器配置
    server_config = agentconfig.get_server_config()
    allowed_hosts = server_config.get("allowedHosts", ["localhost", "127.0.0.1", "0.0.0.0"])
    
    # 记录允许的主机列表
    logger.info(f"允许的主机列表: {allowed_hosts}")
    
    # 构建允许的 CORS origins
    allowed_origins = []
    for host in allowed_hosts:
        allowed_origins.extend([
            f"http://{host}:*",
            f"https://{host}:*",
            f"http://{host}",
            f"https://{host}"
        ])
    
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加自定义中间件
    # 注意：中间件按相反顺序执行，最后添加的最先执行
    # 所以先添加 HostValidation，再添加 RequestLogging
    app.add_middleware(HostValidationMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 注册路由
    # WebSocket 端点
    app.add_websocket_route("/ws", websocket.websocket_endpoint)
    
    # API 路由
    app.get("/api/status")(config_api.status)
    app.get("/api/config")(config_api.get_config)
    app.get("/api/files/tree")(files.get_file_tree)
    app.get("/api/files{file_path:path}")(files.get_file_content)
    app.delete("/api/sessions/clear")(sessions.clear_user_sessions)
    app.get("/api/sessions/export")(sessions.export_user_sessions)
    
    # 挂载静态文件服务
    # 获取 UI 静态文件目录
    ui_template_dir = Path(os.environ.get('UI_TEMPLATE_DIR', Path(__file__).parent.parent))
    static_dir = ui_template_dir / "frontend" / "ui-static"
    
    # 检查静态文件目录是否存在
    if static_dir.exists():
        # 先定义其他所有路由，最后挂载静态文件
        # 这样可以确保 API 和 WebSocket 路由优先匹配
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        print(f"📁 静态文件目录: {static_dir}")
    else:
        print(f"⚠️  静态文件目录不存在: {static_dir}")
    
    # 打印 Agent 配置信息
    print(f"📂 Agent 配置: {agentconfig.config['agent']['module']}")
    print("🛠️  Agent 将在用户连接时根据其 AK 动态创建")
    
    return app