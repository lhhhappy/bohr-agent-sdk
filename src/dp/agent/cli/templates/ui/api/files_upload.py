# File Upload API Extension
from typing import List
from pathlib import Path
from fastapi import Request, File, UploadFile
from fastapi.responses import JSONResponse
import uuid

from server.utils import get_ak_info_from_request
from server.user_files import UserFileManager
from config.agent_config import agentconfig

# Import required functions and variables from files.py
from .files import user_file_manager
from .utils import get_user_identifier, extract_session_id_from_request, check_project_id_required
from .constants import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from .messages import ERROR_MESSAGES, get_message


async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    """Upload files to user directory"""
    try:
        # Get user identity
        access_key, app_key = get_ak_info_from_request(request.headers)
        
        # Get session_id (from cookie)
        session_id = extract_session_id_from_request(request)
        
        # Get user unique identifier
        user_identifier = get_user_identifier(access_key, app_key, session_id)
        
        # Check if user has set project_id
        from api.websocket import manager
        
        has_project_id = await check_project_id_required(manager, user_identifier)
        
        # If project_id not set, reject upload
        if not has_project_id:
            return JSONResponse(
                content={
                    "error": get_message(ERROR_MESSAGES['project_id_required']),
                    "code": "PROJECT_ID_REQUIRED"
                },
                status_code=403
            )
        
        # Get user-specific file directory
        user_files_dir = user_file_manager.get_user_files_dir(user_identifier)
        output_dir = user_files_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # File limits are now imported from constants
        
        uploaded_files = []
        
        for file in files:
            # Verify file extension
            file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            if file_ext not in ALLOWED_EXTENSIONS:
                return JSONResponse(
                    content={"error": get_message(ERROR_MESSAGES['unsupported_file_type']).format(file_ext=file_ext)},
                    status_code=400
                )
            
            # Read file content
            content = await file.read()
            
            # Verify file size
            if len(content) > MAX_FILE_SIZE:
                return JSONResponse(
                    content={"error": get_message(ERROR_MESSAGES['file_too_large']).format(filename=file.filename)},
                    status_code=400
                )
            
            # Generate safe filename
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            
            # Handle filename conflicts
            file_path = output_dir / safe_filename
            if file_path.exists():
                # Add timestamp to avoid overwriting
                name_parts = safe_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    safe_filename = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
                else:
                    safe_filename = f"{safe_filename}_{uuid.uuid4().hex[:8]}"
                file_path = output_dir / safe_filename
            
            # Save file
            file_path.write_bytes(content)
            
            # Generate relative path (relative to user_files_dir)
            relative_path = file_path.relative_to(user_files_dir)
            
            # Add to return list
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