# WebSocket endpoint handler
import os
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from server.utils import get_ak_info_from_request
from server.session_manager import SessionManager
from api.projects import verify_user_project
from bohrium_open_sdk import OpenSDK

# Global session manager
manager = SessionManager()


async def websocket_endpoint(websocket: WebSocket):
    # Extract access_key and app_key from headers
    access_key, app_key = get_ak_info_from_request(websocket.headers)
    
    await manager.connect_client(websocket, access_key, app_key)
    
    # Get connection context
    context = manager.active_connections.get(websocket)
    if not context:
        await websocket.close()
        return
    
    # Try to get project_id from environment variable (for development)
    env_project_id = os.environ.get('BOHR_PROJECT_ID')
    if env_project_id and not context.project_id:
        try:
            project_id_int = int(env_project_id)
            
            # Verify project_id (but allow usage in development mode)
            is_valid = await verify_user_project(access_key, project_id_int)
            
            context.project_id = project_id_int
            # Notify frontend that project_id has been set
            await websocket.send_json({
                "type": "project_id_set",
                "project_id": context.project_id,
                "content": f"Project ID 已从环境变量设置为: {context.project_id} (开发模式)"
            })
        except ValueError:
            pass
        
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "message":
                content = data.get("content", "").strip()
                attachments = data.get("attachments", [])
                if content or attachments:
                    await manager.process_message(context, content, attachments)
                    
            elif message_type == "create_session":
                # Create new session
                session = await manager.create_session(context)
                await manager.switch_session(context, session.id)
                await manager.send_sessions_list(context)
                await manager.send_session_messages(context, session.id)
                
            elif message_type == "switch_session":
                # Switch session
                session_id = data.get("session_id")
                if session_id and await manager.switch_session(context, session_id):
                    # Send updated session list (with new current_session_id)
                    await manager.send_sessions_list(context)
                    # Send message history for new session
                    await manager.send_session_messages(context, session_id)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "会话不存在"
                    })
                    
            elif message_type == "get_sessions":
                # Get session list
                await manager.send_sessions_list(context)
                
            elif message_type == "delete_session":
                # Delete session
                session_id = data.get("session_id")
                if session_id:
                    # Track if deleting current session
                    is_current_session = (session_id == context.current_session_id)
                    
                    success = await manager.delete_session(context, session_id)
                    if success:
                        # If deleted current session, switch to another session
                        if is_current_session:
                            # Get remaining sessions list
                            user_identifier = context.get_user_identifier()
                            session_service = manager.session_services.get(user_identifier)
                            
                            if session_service:
                                response = await session_service.list_sessions(
                                    app_name=manager.app_name,
                                    user_id=user_identifier
                                )
                                remaining_sessions = response.sessions if hasattr(response, 'sessions') else []
                                
                                if remaining_sessions:
                                    # Switch to first (most recent) session
                                    # Sort by last update time
                                    remaining_sessions.sort(
                                        key=lambda s: manager._get_session_last_update_time(s),
                                        reverse=True
                                    )
                                    new_session_id = remaining_sessions[0].id
                                    await manager.switch_session(context, new_session_id)
                                    # Send message history for new session
                                    await manager.send_session_messages(context, new_session_id)
                                else:
                                    # If no sessions left, create new one
                                    session = await manager.create_session(context)
                                    await manager.switch_session(context, session.id)
                                    # New session has no message history, send empty list
                                    await websocket.send_json({
                                        "type": "session_messages",
                                        "session_id": session.id,
                                        "messages": []
                                    })
                        
                        # Send updated session list (with current session ID)
                        await manager.send_sessions_list(context)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": "删除会话失败"
                        })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "删除会话失败"
                    })
                    
            elif message_type == "set_project_id":
                # Set project_id
                project_id = data.get("project_id")
                if project_id is not None:
                    try:
                        # Ensure project_id is integer
                        project_id_int = int(project_id)
                        
                        # Commented out project_id validation, allow users to set any project_id
                        # is_valid = await verify_user_project(access_key, project_id_int)
                        # 
                        # if not is_valid:
                        #     await websocket.send_json({
                        #         "type": "error",
                        #         "content": f"您没有权限使用项目 ID: {project_id_int}。请从项目列表中选择您有权限的项目。"
                        #     })
                        #     return
                        
                        # Validation passed, set project_id
                        context.project_id = project_id_int
                        
                        # Only reinitialize runner for current session
                        if context.current_session_id:
                            # Reinitialize runner through SessionManager
                            user_identifier = context.get_user_identifier()
                            runner_key = f"{user_identifier}_{context.current_session_id}"
                            if runner_key in manager.runners:
                                del manager.runners[runner_key]
                            # Reinitialize
                            await manager._init_runner(context, context.current_session_id)
                        
                        await websocket.send_json({
                            "type": "project_id_set",
                            "project_id": context.project_id,
                            "content": f"Project ID 已设置为: {context.project_id}"
                        })
                    except ValueError:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"无效的 Project ID: {project_id}，必须是整数"
                        })
                
    except WebSocketDisconnect:
        await manager.disconnect_client(websocket)
    except Exception as e:
        await manager.disconnect_client(websocket)