# User-specific file access API
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse, FileResponse

from server.user_files import UserFileManager
from config.agent_config import agentconfig

# Import user_file_manager from files.py
from .files import user_file_manager


async def get_user_file(request: Request, user_id: str, filename: str):
    """Get file for specific user"""
    try:
        # Use user_id to directly get user file directory
        # UserFileManager will automatically choose the correct path based on user_id type
        user_files_dir = user_file_manager.get_user_files_dir(user_id)
        file_path = user_files_dir / "output" / filename
        
        # Security check
        if not file_path.exists() or not file_path.is_file():
            return JSONResponse(
                content={"error": "文件未找到"},
                status_code=404
            )
        
        # Verify file is indeed within user directory
        try:
            file_path_resolved = file_path.resolve()
            user_dir_resolved = user_files_dir.resolve()
            if not str(file_path_resolved).startswith(str(user_dir_resolved)):
                return JSONResponse(
                    content={"error": "访问被拒绝"},
                    status_code=403
                )
        except:
            return JSONResponse(
                content={"error": "无效的文件路径"},
                status_code=400
            )
        
        # Return file
        return FileResponse(file_path)
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )