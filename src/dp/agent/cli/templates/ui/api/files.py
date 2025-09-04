# File API
import os
import json
import uuid
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List
from fastapi import Request, Response, File, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse, StreamingResponse
from bohrium_open_sdk import OpenSDK

from config.agent_config import agentconfig
from server.utils import get_ak_info_from_request
from server.user_files import UserFileManager




# Get sessions directory path from config
files_config = agentconfig.get_files_config()
user_working_dir = os.environ.get('USER_WORKING_DIR', os.getcwd()) 
sessions_dir = files_config.get('sessionsDir', '.agent_sessions')
user_file_manager = UserFileManager(user_working_dir, sessions_dir)

# Import SessionManager instance
from api.websocket import manager


def get_user_identifier(access_key: str = None, app_key: str = None, session_id: str = None) -> str:
    """Get user unique identifier"""
    # First try to get from connected context
    if access_key:
        cached_user_id = manager.get_user_identifier_from_request(access_key, app_key)
        if cached_user_id:
            return cached_user_id
    
    # If no cache, call OpenSDK
    if access_key and app_key:
        try:
            # Use OpenSDK to get user info
            client = OpenSDK(
                access_key=access_key,
                app_key=app_key
            )
            user_info = client.user.get_info()
            if user_info and user_info.get('code') == 0:
                data = user_info.get('data', {})
                bohrium_user_id = data.get('user_id')
                if bohrium_user_id:
                    return bohrium_user_id
        except Exception as e:
            pass
    
    # If has session_id, use it
    if session_id:
        return session_id
    
    # Generate temporary ID if none available
    return f"user_{uuid.uuid4().hex[:8]}"


async def get_file_tree(request: Request, path: str = None):
    """Get file tree structure"""
    try:
        # Get user identity
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # Get session_id (from cookie)
        session_id = None
        cookie_header = request.headers.get("cookie", "")
        if cookie_header:
            from http.cookies import SimpleCookie
            simple_cookie = SimpleCookie()
            simple_cookie.load(cookie_header)
            if "session_id" in simple_cookie:
                session_id = simple_cookie["session_id"].value
        
        # Get user unique identifier
        user_identifier = get_user_identifier(access_key, app_key, session_id)
        
        # Get user-specific file directory
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
            # Return file tree structure for user directory
            tree = []
            
            # User file root directory
            if user_files_dir.exists():
                # Build root directory node
                root_node = {
                    "name": "工作空间",
                    "path": str(user_files_dir),
                    "type": "directory",
                    "isExpanded": True,
                    "children": build_tree(user_files_dir)
                }
                tree.append(root_node)
            
            return JSONResponse(content=tree)
        else:
            # Handle specific path request
            # Ensure path is within user directory
            if os.path.isabs(path):
                request_path = Path(path)
            else:
                request_path = user_files_dir / path
            
            # Security check: ensure requested path is within user directory
            try:
                request_path = request_path.resolve()
                user_files_dir_resolved = user_files_dir.resolve()
                if not str(request_path).startswith(str(user_files_dir_resolved)):
                    return JSONResponse(content=[], status_code=403)
            except:
                return JSONResponse(content=[], status_code=400)
            
            if not request_path.exists():
                request_path.mkdir(parents=True, exist_ok=True)
            
            return JSONResponse(content=build_tree(request_path))
        
    except Exception as e:
        return JSONResponse(content=[], status_code=500)


async def get_file_content(request: Request, file_path: str):
    """Get file content"""
    try:
        # Get user identity
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # Get session_id (from cookie)
        session_id = None
        cookie_header = request.headers.get("cookie", "")
        if cookie_header:
            from http.cookies import SimpleCookie
            simple_cookie = SimpleCookie()
            simple_cookie.load(cookie_header)
            if "session_id" in simple_cookie:
                session_id = simple_cookie["session_id"].value
        
        # Get user unique identifier
        user_identifier = get_user_identifier(access_key, app_key, session_id)
        
        # Get user-specific file directory
        user_files_dir = user_file_manager.get_user_files_dir(user_identifier)
        
        # Handle file path
        if file_path.startswith('/'):
            file = Path(file_path)
        else:
            # Relative path, based on user directory
            file = user_files_dir / file_path
        
        # Security check: ensure file is within user directory
        try:
            file_resolved = file.resolve()
            user_files_dir_resolved = user_files_dir.resolve()
            if not str(file_resolved).startswith(str(user_files_dir_resolved)):
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
        
        # Determine file type
        suffix = file.suffix.lower()
        
        # Text files
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
            # Binary files
            return FileResponse(file)
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


async def download_file(request: Request, file_path: str):
    """下载单个文件"""
    try:
        # 获取用户身份
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # 获取 session_id (从 cookie)
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
        
        # 获取文件名
        filename = file.name
        
        # 返回文件响应，设置下载头
        return FileResponse(
            path=file,
            filename=filename,
            media_type='application/octet-stream'
        )
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


async def download_folder(request: Request, folder_path: str):
    """下载文件夹（打包为 zip）"""
    try:
        # 获取用户身份
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # 获取 session_id (从 cookie)
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
        
        # 处理文件夹路径
        if folder_path.startswith('/'):
            folder = Path(folder_path)
        else:
            # 相对路径，基于用户目录
            folder = user_files_dir / folder_path
        
        # 安全检查：确保文件夹在用户目录内
        try:
            folder_resolved = folder.resolve()
            user_files_dir_resolved = user_files_dir.resolve()
            if not str(folder_resolved).startswith(str(user_files_dir_resolved)):
                return JSONResponse(
                    content={"error": "访问被拒绝"},
                    status_code=403
                )
        except:
            return JSONResponse(
                content={"error": "无效的文件夹路径"},
                status_code=400
            )
            
        if not folder.exists() or not folder.is_dir():
            return JSONResponse(
                content={"error": "文件夹未找到"},
                status_code=404
            )
        
        # 创建临时 zip 文件
        temp_dir = Path(tempfile.gettempdir())
        zip_filename = f"{folder.name}_{uuid.uuid4().hex[:8]}.zip"
        zip_path = temp_dir / zip_filename
        
        try:
            # 创建 zip 文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder):
                    # 跳过隐藏文件和目录
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file in files:
                        if file.startswith('.'):
                            continue
                            
                        file_path = Path(root) / file
                        # 计算相对路径
                        arcname = file_path.relative_to(folder)
                        zipf.write(file_path, arcname=str(arcname))
            
            # 返回 zip 文件
            def cleanup():
                """清理临时文件"""
                try:
                    if zip_path.exists():
                        zip_path.unlink()
                except:
                    pass
            
            # 读取文件内容
            with open(zip_path, 'rb') as f:
                content = f.read()
            
            # 清理临时文件
            cleanup()
            
            # 返回响应
            return Response(
                content=content,
                media_type='application/zip',
                headers={
                    'Content-Disposition': f'attachment; filename="{folder.name}.zip"'
                }
            )
            
        except Exception as e:
            # 确保清理临时文件
            if zip_path.exists():
                zip_path.unlink()
            raise e
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


async def delete_file(request: Request, file_path: str):
    """删除文件或文件夹"""
    try:
        # 获取用户身份
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # 获取 session_id (从 cookie)
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
            target_path = Path(file_path)
        else:
            # 相对路径，基于用户目录
            target_path = user_files_dir / file_path
        
        # 安全检查：确保文件在用户目录内
        try:
            target_path_resolved = target_path.resolve()
            user_files_dir_resolved = user_files_dir.resolve()
            if not str(target_path_resolved).startswith(str(user_files_dir_resolved)):
                return JSONResponse(
                    content={"error": "访问被拒绝"},
                    status_code=403
                )
        except:
            return JSONResponse(
                content={"error": "无效的文件路径"},
                status_code=400
            )
        
        # 检查文件是否存在
        if not target_path.exists():
            return JSONResponse(
                content={"error": "文件或文件夹不存在"},
                status_code=404
            )
        
        # 删除文件或文件夹
        if target_path.is_file():
            target_path.unlink()
        else:
            # 递归删除文件夹
            shutil.rmtree(target_path)
        
        return JSONResponse({
            "success": True,
            "message": f"成功删除: {target_path.name}"
        })
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )