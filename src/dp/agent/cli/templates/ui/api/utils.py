"""
Common utilities for API modules
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from fastapi import Request
from fastapi.responses import JSONResponse

from server.utils import get_ak_info_from_request
from server.user_files import UserFileManager
from api.messages import ERROR_MESSAGES, get_message


def get_user_identifier(access_key: Optional[str], app_key: Optional[str], session_id: Optional[str]) -> str:
    """
    Get unique user identifier based on access_key or session_id
    
    Args:
        access_key: User's access key
        app_key: User's app key
        session_id: Session ID for temporary users
        
    Returns:
        Unique user identifier string
    """
    if access_key:
        return access_key
    return session_id or "anonymous"


def extract_session_id_from_request(request: Request) -> Optional[str]:
    """
    Extract session_id from request cookies
    
    Args:
        request: FastAPI request object
        
    Returns:
        Session ID if found, None otherwise
    """
    cookie_header = request.headers.get("cookie", "")
    if not cookie_header:
        return None
        
    from http.cookies import SimpleCookie
    simple_cookie = SimpleCookie()
    simple_cookie.load(cookie_header)
    
    if "session_id" in simple_cookie:
        return simple_cookie["session_id"].value
    return None


def get_user_context_from_request(request: Request) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Extract user context from request
    
    Returns:
        Tuple of (user_identifier, access_key, app_key)
    """
    access_key, app_key = get_ak_info_from_request(request.headers)
    session_id = extract_session_id_from_request(request)
    user_identifier = get_user_identifier(access_key, app_key, session_id)
    
    return user_identifier, access_key, app_key


def validate_file_access(file_path: Path, user_files_dir: Path, lang='zh') -> Optional[JSONResponse]:
    """
    Validate if file path is within user directory and accessible
    
    Args:
        file_path: Path to validate
        user_files_dir: User's files directory
        lang: Language for error messages
        
    Returns:
        JSONResponse with error if validation fails, None if valid
    """
    try:
        # Resolve paths to absolute
        file_resolved = file_path.resolve()
        user_files_dir_resolved = user_files_dir.resolve()
        
        # Check if file is within user directory
        if not str(file_resolved).startswith(str(user_files_dir_resolved)):
            return JSONResponse(
                content={"error": get_message(ERROR_MESSAGES['access_denied'], lang)},
                status_code=403
            )
            
        # Check if file exists
        if not file_resolved.exists():
            error_key = 'folder_not_found' if file_path.is_dir() else 'file_not_found'
            return JSONResponse(
                content={"error": get_message(ERROR_MESSAGES[error_key], lang)},
                status_code=404
            )
            
        return None
        
    except Exception:
        return JSONResponse(
            content={"error": get_message(ERROR_MESSAGES['invalid_file_path'], lang)},
            status_code=400
        )


def process_file_path(file_path_str: str, user_files_dir: Path) -> Path:
    """
    Process file path string and convert to Path object
    
    Args:
        file_path_str: File path as string
        user_files_dir: User's files directory
        
    Returns:
        Processed Path object
    """
    if file_path_str.startswith('/'):
        return Path(file_path_str)
    else:
        # Relative path, based on user directory
        return user_files_dir / file_path_str


def safe_filename(filename: str) -> str:
    """
    Generate safe filename by replacing dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    return filename.replace('/', '_').replace('\\', '_').replace('..', '_')


async def check_project_id_required(context_manager, user_identifier: str) -> bool:
    """
    Check if project_id is required and set

    Args:
        context_manager: WebSocket manager instance
        user_identifier: User identifier (can be access_key or bohrium_user_id)

    Returns:
        True if project_id is set, False otherwise
    """
    # First check environment variable
    if os.environ.get('BOHR_PROJECT_ID'):
        return True

    # Check user's connection context
    for context in context_manager.active_connections.values():
        # Match by bohrium_user_id or access_key
        if context.get_user_identifier() == user_identifier or context.access_key == user_identifier:
            return bool(context.project_id)

    return False