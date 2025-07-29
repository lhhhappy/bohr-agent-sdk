"""
WebSocket 端点处理
"""
import logging
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from server.utils import get_ak_info_from_request
from server.session_manager import SessionManager

logger = logging.getLogger(__name__)

# 创建全局管理器
manager = SessionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    # 提取AK和app_key信息
    access_key, app_key = get_ak_info_from_request(websocket.headers)
    
    await manager.connect_client(websocket, access_key, app_key)
    
    # 获取该连接的上下文
    context = manager.active_connections.get(websocket)
    if not context:
        logger.error("无法获取连接上下文")
        await websocket.close()
        return
        
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "message":
                content = data.get("content", "").strip()
                if content:
                    await manager.process_message(context, content)
                    
            elif message_type == "create_session":
                # 创建新会话
                session = await manager.create_session(context)
                await manager.switch_session(context, session.id)
                await manager.send_sessions_list(context)
                await manager.send_session_messages(context, session.id)
                
            elif message_type == "switch_session":
                # 切换会话
                session_id = data.get("session_id")
                if session_id and await manager.switch_session(context, session_id):
                    await manager.send_session_messages(context, session_id)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "会话不存在"
                    })
                    
            elif message_type == "get_sessions":
                # 获取会话列表
                await manager.send_sessions_list(context)
                
            elif message_type == "delete_session":
                # 删除会话
                session_id = data.get("session_id")
                if session_id and await manager.delete_session(context, session_id):
                    # 如果删除的是当前会话，切换到其他会话或创建新会话
                    if session_id == context.current_session_id:
                        if context.sessions:
                            # 切换到第一个可用会话
                            first_session_id = list(context.sessions.keys())[0]
                            await manager.switch_session(context, first_session_id)
                        else:
                            # 创建新会话
                            session = await manager.create_session(context)
                            await manager.switch_session(context, session.id)
                    await manager.send_sessions_list(context)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "删除会话失败"
                    })
                    
            elif message_type == "set_project_id":
                # 设置 project_id
                project_id = data.get("project_id")
                if project_id is not None:
                    try:
                        # 确保 project_id 是整数
                        context.project_id = int(project_id)
                        logger.info(f"设置 project_id: {context.project_id} for user {context.user_id}")
                        
                        # 只重新初始化当前会话的 runner
                        if context.current_session_id:
                            logger.info(f"为当前会话 {context.current_session_id} 重新初始化 runner，project_id: {context.project_id}")
                            # 清理当前会话的旧 runner
                            if context.current_session_id in context.runners:
                                del context.runners[context.current_session_id]
                            if context.current_session_id in context.session_services:
                                del context.session_services[context.current_session_id]
                            # 重新初始化
                            await manager._init_session_runner(context, context.current_session_id)
                        
                        await websocket.send_json({
                            "type": "project_id_set",
                            "project_id": context.project_id,
                            "content": f"Project ID 已设置为: {context.project_id}"
                        })
                    except ValueError:
                        logger.error(f"无效的 project_id 值: {project_id}")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"无效的 Project ID: {project_id}，必须是整数"
                        })
                
    except WebSocketDisconnect:
        await manager.disconnect_client(websocket)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        await manager.disconnect_client(websocket)