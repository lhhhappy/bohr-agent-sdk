# Session management API
import json
import shutil
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse, Response

from server.utils import get_ak_info_from_request
from api.websocket import manager


async def clear_user_sessions(request: Request):
    """Clear all historical sessions for current user"""
    access_key, _ = get_ak_info_from_request(request.headers)
    
    if not access_key:
        return JSONResponse(
            content={"error": "临时用户没有历史会话"},
            status_code=400
        )
    
    try:
        # Get user's session directory
        ak_hash = manager.persistent_manager._get_ak_hash(access_key)
        user_sessions_dir = manager.persistent_manager.ak_sessions_dir / ak_hash / "sessions"
        
        if user_sessions_dir.exists():
            # Delete all session files
            shutil.rmtree(user_sessions_dir)
            user_sessions_dir.mkdir(parents=True, exist_ok=True)
            
            return JSONResponse(content={
                "message": "历史会话已清除",
                "status": "success"
            })
        else:
            return JSONResponse(content={
                "message": "没有找到历史会话",
                "status": "success"
            })
            
    except Exception as e:
        return JSONResponse(
            content={"error": f"清除失败: {str(e)}"},
            status_code=500
        )


async def export_user_sessions(request: Request):
    """Export all sessions for current user"""
    access_key, _ = get_ak_info_from_request(request.headers)
    
    if not access_key:
        return JSONResponse(
            content={"error": "临时用户没有会话可导出"},
            status_code=400
        )
    
    try:
        # Load all user sessions
        sessions = await manager.persistent_manager.load_user_sessions(access_key)
        
        if not sessions:
            return JSONResponse(
                content={"error": "没有找到会话"},
                status_code=404
            )
        
        # Build export data
        export_data = {
            "export_time": datetime.now().isoformat(),
            "user_type": "registered",
            "sessions": []
        }
        
        for session in sessions.values():
            session_data = manager.persistent_manager._serialize_session(session)
            export_data["sessions"].append(session_data)
        
        # Return JSON file
        return Response(
            content=json.dumps(export_data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=sessions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"导出失败: {str(e)}"},
            status_code=500
        )