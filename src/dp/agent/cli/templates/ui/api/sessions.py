"""
会话管理 API
"""
import json
import shutil
import logging
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse, Response

from server.utils import get_ak_info_from_request
from api.websocket import manager

logger = logging.getLogger(__name__)


async def clear_user_sessions(request: Request):
    """清除当前用户的所有历史会话"""
    access_key, _ = get_ak_info_from_request(request.headers)
    
    if not access_key:
        return JSONResponse(
            content={"error": "临时用户没有历史会话"},
            status_code=400
        )
    
    try:
        # 获取用户的会话目录
        ak_hash = manager.persistent_manager._get_ak_hash(access_key)
        user_sessions_dir = manager.persistent_manager.ak_sessions_dir / ak_hash / "sessions"
        
        if user_sessions_dir.exists():
            # 删除所有会话文件
            shutil.rmtree(user_sessions_dir)
            user_sessions_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"清除用户 {access_key[:8]}... 的所有历史会话")
            
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
        logger.error(f"清除历史会话失败: {e}")
        return JSONResponse(
            content={"error": f"清除失败: {str(e)}"},
            status_code=500
        )


async def export_user_sessions(request: Request):
    """导出当前用户的所有会话"""
    access_key, _ = get_ak_info_from_request(request.headers)
    
    if not access_key:
        return JSONResponse(
            content={"error": "临时用户没有会话可导出"},
            status_code=400
        )
    
    try:
        # 加载用户的所有会话
        sessions = await manager.persistent_manager.load_user_sessions(access_key)
        
        if not sessions:
            return JSONResponse(
                content={"error": "没有找到会话"},
                status_code=404
            )
        
        # 构建导出数据
        export_data = {
            "export_time": datetime.now().isoformat(),
            "user_type": "registered",
            "sessions": []
        }
        
        for session in sessions.values():
            session_data = manager.persistent_manager._serialize_session(session)
            export_data["sessions"].append(session_data)
        
        # 返回JSON文件
        return Response(
            content=json.dumps(export_data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=sessions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except Exception as e:
        logger.error(f"导出会话失败: {e}")
        return JSONResponse(
            content={"error": f"导出失败: {str(e)}"},
            status_code=500
        )