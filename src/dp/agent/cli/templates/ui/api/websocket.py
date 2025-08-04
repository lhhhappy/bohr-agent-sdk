"""
WebSocket 端点处理
"""
import os
import logging
import aiohttp
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from server.utils import get_ak_info_from_request
from server.session_manager import SessionManager

logger = logging.getLogger(__name__)

# 创建全局管理器
manager = SessionManager()

# Bohrium API 配置
BOHRIUM_API_BASE = "https://openapi.dp.tech/openapi/v1"


async def verify_user_project(access_key: str, project_id: int) -> bool:
    """验证 project_id 是否属于当前用户（已注释验证逻辑，直接返回 True）
    
    Args:
        access_key: 用户的 AccessKey
        project_id: 待验证的项目 ID
        
    Returns:
        bool: 总是返回 True，允许用户自定义任意 project_id
    """
    # 注释掉原有验证逻辑，直接返回 True 允许任意 project_id
    # if not access_key or not project_id:
    #     return False
    #     
    # try:
    #     headers = {
    #         "AccessKey": access_key,
    #         "Content-Type": "application/json"
    #     }
    #     
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(
    #             f"{BOHRIUM_API_BASE}/project/list",
    #             headers=headers,
    #             timeout=aiohttp.ClientTimeout(total=10)
    #         ) as response:
    #             data = await response.json()
    #             
    #             if data.get("code") != 0:
    #                 logger.error(f"获取项目列表失败: {data}")
    #                 return False
    #             
    #             # 检查 project_id 是否在用户的项目列表中
    #             items = data.get("data", {}).get("items", [])
    #             user_project_ids = [item["id"] for item in items]
    #             
    #             return project_id in user_project_ids
    #             
    # except Exception as e:
    #     logger.error(f"验证项目时发生错误: {e}")
    #     return False
    
    # 直接返回 True，允许任意 project_id
    return True


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
    
    # 尝试从环境变量获取 project_id（用于开发）
    env_project_id = os.environ.get('BOHR_PROJECT_ID')
    if env_project_id and not context.project_id:
        try:
            project_id_int = int(env_project_id)
            
            # 在开发环境中，记录警告但仍允许使用
            logger.warning(f"使用环境变量 BOHR_PROJECT_ID: {project_id_int} (开发模式)")
            
            # 验证 project_id（但不阻止开发环境使用）
            is_valid = await verify_user_project(access_key, project_id_int)
            if not is_valid:
                logger.warning(f"环境变量设置的 project_id {project_id_int} 未通过验证，但在开发模式下仍允许使用")
            
            context.project_id = project_id_int
            logger.info(f"从环境变量设置初始 project_id: {context.project_id}")
            # 通知前端 project_id 已设置
            await websocket.send_json({
                "type": "project_id_set",
                "project_id": context.project_id,
                "content": f"Project ID 已从环境变量设置为: {context.project_id} (开发模式)"
            })
        except ValueError:
            logger.error(f"环境变量 BOHR_PROJECT_ID 值无效: {env_project_id}")
        
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
                        project_id_int = int(project_id)
                        
                        # 注释掉 project_id 验证，允许用户设置任意 project_id
                        # is_valid = await verify_user_project(access_key, project_id_int)
                        # 
                        # if not is_valid:
                        #     logger.warning(f"用户 {context.user_id} 尝试设置无权限的 project_id: {project_id_int}")
                        #     await websocket.send_json({
                        #         "type": "error",
                        #         "content": f"您没有权限使用项目 ID: {project_id_int}。请从项目列表中选择您有权限的项目。"
                        #     })
                        #     return
                        
                        # 验证通过，设置 project_id
                        context.project_id = project_id_int
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