"""
文件相关 API
"""
import os
import json
import logging
import uuid
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from bohrium_open_sdk import OpenSDK

from config.agent_config import agentconfig
from server.utils import get_ak_info_from_request
from server.user_files import UserFileManager

logger = logging.getLogger(__name__)

# 创建全局的用户文件管理器
user_working_dir = os.environ.get('USER_WORKING_DIR', Path.cwd())
# 从配置中获取 sessions 目录路径
files_config = agentconfig.get_files_config()
sessions_dir = files_config.get('sessionsDir', '.agent_sessions')
user_file_manager = UserFileManager(user_working_dir, sessions_dir)

# 导入 SessionManager 实例
from api.websocket import manager


def get_user_identifier(access_key: str = None, app_key: str = None, session_id: str = None) -> str:
    """获取用户唯一标识符"""
    # 先尝试从已连接的上下文获取
    if access_key:
        cached_user_id = manager.get_user_identifier_from_request(access_key, app_key)
        if cached_user_id:
            logger.debug(f"从已连接上下文获取用户ID: {cached_user_id}")
            return cached_user_id
        else:
            logger.debug(f"未找到缓存的用户信息，将调用 OpenSDK")
    
    # 如果没有缓存，才调用OpenSDK
    if access_key and app_key:
        try:
            # 使用OpenSDK获取用户信息
            client = OpenSDK(
                access_key=access_key,
                app_key=app_key
            )
            user_info = client.user.get_info()
            if user_info and user_info.get('code') == 0:
                data = user_info.get('data', {})
                bohrium_user_id = data.get('user_id')
                if bohrium_user_id:
                    logger.info(f"调用OpenSDK获取Bohrium用户ID: {bohrium_user_id}")
                    return bohrium_user_id
        except Exception as e:
            logger.error(f"调用OpenSDK获取用户信息失败: {e}")
    
    # 如果有session_id，使用它
    if session_id:
        return session_id
    
    # 都没有的话，生成一个临时ID
    return f"user_{uuid.uuid4().hex[:8]}"


async def get_file_tree(request: Request, path: str = None):
    """获取文件树结构"""
    try:
        # 获取用户身份
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # 获取 session_id（从 cookie 中）
        session_id = None
        cookie_header = request.headers.get("cookie", "")
        if cookie_header:
            from http.cookies import SimpleCookie
            simple_cookie = SimpleCookie()
            simple_cookie.load(cookie_header)
            if "session_id" in simple_cookie:
                session_id = simple_cookie["session_id"].value
        
        # 获取用户唯一标识符
        user_identifier = get_user_identifier(access_key, app_key, session_id)
        
        # 获取用户特定的文件目录
        user_files_dir = user_file_manager.get_user_files_dir(user_identifier)
        
        def build_tree(directory: Path):
            items = []
            try:
                for item in sorted(directory.iterdir()):
                    if item.name.startswith('.'):
                        continue
                        
                    node = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file"
                    }
                    
                    if item.is_dir():
                        node["children"] = build_tree(item)
                    else:
                        node["size"] = item.stat().st_size
                        
                    items.append(node)
            except PermissionError:
                pass
            return items
        
        if path is None:
            # 返回用户文件目录的树结构
            tree = []
            
            # 用户文件根目录
            if user_files_dir.exists():
                # 构建根目录节点
                root_node = {
                    "name": "工作空间",
                    "path": str(user_files_dir),
                    "type": "directory",
                    "isExpanded": True,
                    "children": build_tree(user_files_dir)
                }
                tree.append(root_node)
            
            logger.info(f"返回用户 {user_identifier} 的文件树")
            return JSONResponse(content=tree)
        else:
            # 处理特定路径请求
            # 确保路径在用户目录内
            if os.path.isabs(path):
                request_path = Path(path)
            else:
                request_path = user_files_dir / path
            
            # 安全检查：确保请求的路径在用户目录内
            try:
                request_path = request_path.resolve()
                user_files_dir_resolved = user_files_dir.resolve()
                if not str(request_path).startswith(str(user_files_dir_resolved)):
                    logger.warning(f"尝试访问用户目录外的路径: {request_path}")
                    return JSONResponse(content=[], status_code=403)
            except:
                return JSONResponse(content=[], status_code=400)
            
            if not request_path.exists():
                request_path.mkdir(parents=True, exist_ok=True)
            
            return JSONResponse(content=build_tree(request_path))
        
    except Exception as e:
        logger.error(f"获取文件树错误: {e}")
        return JSONResponse(content=[], status_code=500)


async def get_file_content(request: Request, file_path: str):
    """获取文件内容"""
    try:
        # 获取用户身份
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # 获取 session_id（从 cookie 中）
        session_id = None
        cookie_header = request.headers.get("cookie", "")
        if cookie_header:
            from http.cookies import SimpleCookie
            simple_cookie = SimpleCookie()
            simple_cookie.load(cookie_header)
            if "session_id" in simple_cookie:
                session_id = simple_cookie["session_id"].value
        
        # 获取用户唯一标识符
        user_identifier = get_user_identifier(access_key, app_key, session_id)
        
        # 获取用户特定的文件目录
        user_files_dir = user_file_manager.get_user_files_dir(user_identifier)
        
        # 处理文件路径
        if file_path.startswith('/'):
            file = Path(file_path)
        else:
            # 相对路径，基于用户目录
            file = user_files_dir / file_path
        
        # 安全检查：确保文件在用户目录内
        try:
            file_resolved = file.resolve()
            user_files_dir_resolved = user_files_dir.resolve()
            if not str(file_resolved).startswith(str(user_files_dir_resolved)):
                logger.warning(f"尝试访问用户目录外的文件: {file_resolved}")
                return JSONResponse(
                    content={"error": "访问被拒绝"},
                    status_code=403
                )
        except:
            return JSONResponse(
                content={"error": "无效的文件路径"},
                status_code=400
            )
            
        if not file.exists() or not file.is_file():
            return JSONResponse(
                content={"error": "文件未找到"},
                status_code=404
            )
        
        # 判断文件类型
        suffix = file.suffix.lower()
        
        # 文本文件
        if suffix in ['.json', '.md', '.txt', '.csv', '.py', '.js', '.ts', '.log', '.xml', '.yaml', '.yml']:
            try:
                content = file.read_text(encoding='utf-8')
                return PlainTextResponse(content)
            except UnicodeDecodeError:
                return JSONResponse(
                    content={"error": "无法解码文件内容"},
                    status_code=400
                )
        else:
            # 二进制文件
            return FileResponse(file)
            
    except Exception as e:
        logger.error(f"读取文件错误: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )