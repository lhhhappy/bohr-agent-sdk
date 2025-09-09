# File Upload API Extension
from typing import List
from pathlib import Path
from fastapi import Request, File, UploadFile
from fastapi.responses import JSONResponse
import uuid

from server.utils import get_ak_info_from_request
from server.user_files import UserFileManager
from config.agent_config import agentconfig

# 从 files.py 导入需要的函数和变量
from .files import user_file_manager, get_user_identifier


async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    """上传文件到用户目录"""
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
        
        # 检查用户是否已设置 project_id
        from api.websocket import manager
        import os
        
        # 首先检查环境变量
        has_project_id = bool(os.environ.get('BOHR_PROJECT_ID'))
        
        # 如果环境变量没有设置，检查用户的连接上下文
        if not has_project_id:
            # 遍历活动连接，查找当前用户
            for context in manager.active_connections.values():
                if context.get_user_identifier() == user_identifier:
                    has_project_id = bool(context.project_id)
                    break
        
        # 如果没有设置 project_id，拒绝上传
        if not has_project_id:
            return JSONResponse(
                content={
                    "error": "请先设置项目 ID 后再上传文件。",
                    "code": "PROJECT_ID_REQUIRED"
                },
                status_code=403
            )
        
        # 获取用户特定的文件目录
        user_files_dir = user_file_manager.get_user_files_dir(user_identifier)
        output_dir = user_files_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 文件大小限制 (10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        
        # 允许的文件扩展名
        ALLOWED_EXTENSIONS = {
            'txt', 'pdf', 'csv', 'json', 'xml', 
            'png', 'jpg', 'jpeg', 'gif', 'svg', 
            'py', 'js', 'ts', 'java', 'cpp', 'c',
            'md', 'rst', 'yaml', 'yml', 'log',
            'html', 'htm', 'css', 'scss',
            'sh', 'bash', 'sql', 'toml'
        }
        
        uploaded_files = []
        
        for file in files:
            # 验证文件扩展名
            file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if file_ext not in ALLOWED_EXTENSIONS:
                return JSONResponse(
                    content={"error": f"不支持的文件类型: {file_ext}"},
                    status_code=400
                )
            
            # 读取文件内容
            content = await file.read()
            
            # 验证文件大小
            if len(content) > MAX_FILE_SIZE:
                return JSONResponse(
                    content={"error": f"文件 {file.filename} 超过大小限制 (10MB)"},
                    status_code=400
                )
            
            # 生成安全的文件名
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            
            # 处理文件名冲突
            file_path = output_dir / safe_filename
            if file_path.exists():
                # 添加时间戳避免覆盖
                name_parts = safe_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    safe_filename = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
                else:
                    safe_filename = f"{safe_filename}_{uuid.uuid4().hex[:8]}"
                file_path = output_dir / safe_filename
            
            # 保存文件
            file_path.write_bytes(content)
            
            # 生成相对路径（相对于 user_files_dir）
            relative_path = file_path.relative_to(user_files_dir)
            
            # 添加到返回列表
            uploaded_files.append({
                "name": file.filename,
                "saved_name": safe_filename,
                "path": str(file_path),
                "file_path": str(file_path.resolve()),
                "relative_path": str(relative_path),
                "url": f"/api/files/{user_identifier}/output/{safe_filename}",
                "size": len(content),
                "mime_type": file.content_type or 'application/octet-stream'
            })
        
        return JSONResponse({
            "success": True,
            "files": uploaded_files
        })
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )