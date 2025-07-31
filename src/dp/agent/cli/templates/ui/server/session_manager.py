"""
会话管理核心逻辑
"""
import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import WebSocket
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from server.models import Session
from server.connection import ConnectionContext
from server.persistence import PersistentSessionManager
from config.agent_config import agentconfig

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, ConnectionContext] = {}
        # Use configuration values
        self.app_name = agentconfig.config.get("agent", {}).get("name", "Agent")
        
        # 初始化持久化管理器
        user_working_dir = os.environ.get('USER_WORKING_DIR', os.getcwd())
        self.persistent_manager = PersistentSessionManager(user_working_dir)
        logger.info(f"持久化管理器初始化，基础目录: {user_working_dir}")
        
    async def create_session(self, context: ConnectionContext) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = Session(id=session_id)
        
        # 先将会话添加到连接的会话列表
        context.sessions[session_id] = session
        logger.info(f"为用户 {context.user_id} 创建新会话: {session_id}")
        
        # 异步创建 session service 和 runner，避免阻塞
        task = asyncio.create_task(self._init_session_runner(context, session_id))
        
        # 添加错误处理回调
        def handle_init_error(future):
            try:
                future.result()
            except Exception as e:
                logger.error(f"初始化会话Runner时发生未处理的错误: {e}", exc_info=True)
        
        task.add_done_callback(handle_init_error)
        
        return session
    
    async def _init_session_runner(self, context: ConnectionContext, session_id: str):
        """异步初始化会话的runner"""
        try:
            # 检查是否有 project_id（可以从环境变量获取用于开发）
            project_id = context.project_id
            if not project_id:
                # 尝试从环境变量获取（仅用于开发调试）
                env_project_id = os.environ.get('BOHR_PROJECT_ID')
                if env_project_id:
                    try:
                        project_id = int(env_project_id)
                        context.project_id = project_id
                        logger.info(f"从环境变量获取 project_id: {project_id}")
                    except ValueError:
                        logger.error(f"环境变量 BOHR_PROJECT_ID 值无效: {env_project_id}")
            
            # 如果仍然没有 project_id，记录警告但继续（让前端处理）
            if not project_id:
                logger.warning(f"会话 {session_id} 初始化时没有 project_id")
            
            # 直接传递 AK 给 agent，避免使用环境变量
            logger.info(f"开始为会话 {session_id} 创建 Runner，AK: {context.access_key[:8] if context.access_key else 'None'}，project_id: {project_id}...")
            
            # 在异步任务中创建agent，避免阻塞主线程
            # 确保传入正确的AK（如果是空字符串或None，agent应该知道这是临时用户）
            loop = asyncio.get_event_loop()
            user_agent = await loop.run_in_executor(
                None, 
                agentconfig.get_agent, 
                context.access_key if context.access_key else "",
                context.app_key if context.app_key else "",
                project_id
            )
            
            session_service = InMemorySessionService()
            await session_service.create_session(
                app_name=self.app_name,
                user_id=context.user_id,
                session_id=session_id
            )
            
            runner = Runner(
                agent=user_agent,
                session_service=session_service,
                app_name=self.app_name
            )
            
            context.session_services[session_id] = session_service
            context.runners[session_id] = runner
            
            logger.info(f"Runner 初始化完成: {session_id}")
            
        except Exception as e:
            logger.error(f"初始化Runner失败 (session_id: {session_id}): {e}", exc_info=True)
            # 清理失败的会话
            if session_id in context.sessions:
                del context.sessions[session_id]
            if session_id in context.session_services:
                del context.session_services[session_id]
            if session_id in context.runners:
                del context.runners[session_id]
    
    def get_session(self, context: ConnectionContext, session_id: str) -> Optional[Session]:
        """获取会话"""
        return context.sessions.get(session_id)
    
    def get_all_sessions(self, context: ConnectionContext) -> List[Session]:
        """获取连接的所有会话列表"""
        return list(context.sessions.values())
    
    async def delete_session(self, context: ConnectionContext, session_id: str) -> bool:
        """删除会话"""
        if session_id in context.sessions:
            # 先从内存中删除
            del context.sessions[session_id]
            if session_id in context.runners:
                del context.runners[session_id]
            if session_id in context.session_services:
                del context.session_services[session_id]
            
            # 如果有AK，同时删除持久化文件
            if context.access_key:
                await self.persistent_manager.delete_session(context.access_key, session_id)
            
            logger.info(f"用户 {context.user_id} 删除会话: {session_id}")
            return True
        return False
    
    async def switch_session(self, context: ConnectionContext, session_id: str) -> bool:
        """切换当前会话"""
        if session_id in context.sessions:
            context.current_session_id = session_id
            logger.info(f"用户 {context.user_id} 切换到会话: {session_id}")
            return True
        return False
    
    async def connect_client(self, websocket: WebSocket, access_key: str = "", app_key: str = ""):
        """连接新客户端"""
        await websocket.accept()
        
        # 为新连接创建独立的上下文，包含AK和app_key
        context = ConnectionContext(websocket, access_key, app_key)
        self.active_connections[websocket] = context
        
        # 加载历史会话（如果有AK）
        if access_key:
            logger.info(f"有AK用户连接: {context.user_id}, AK: {access_key[:8]}...")
            logger.info("正在加载历史会话...")
            
            try:
                historical_sessions = await self.persistent_manager.load_user_sessions(access_key)
                
                if historical_sessions:
                    # 恢复历史会话
                    context.sessions = historical_sessions
                    
                    # 选择最近的会话作为当前会话
                    sorted_sessions = sorted(
                        historical_sessions.values(), 
                        key=lambda s: s.last_message_at, 
                        reverse=True
                    )
                    context.current_session_id = sorted_sessions[0].id if sorted_sessions else None
                    
                    # 为每个会话异步初始化runner
                    init_tasks = []
                    for session_id in historical_sessions:
                        task = asyncio.create_task(self._init_session_runner(context, session_id))
                        init_tasks.append(task)
                    
                    # 不等待所有任务完成，让它们在后台运行
                    logger.info(f"已恢复 {len(historical_sessions)} 个历史会话，正在后台初始化Runner...")
                else:
                    # 新的AK用户，创建首个会话
                    logger.info("没有找到历史会话，创建新会话")
                    session = await self.create_session(context)
                    context.current_session_id = session.id
            except Exception as e:
                logger.error(f"加载历史会话失败: {e}")
                # 加载失败时创建新会话
                session = await self.create_session(context)
                context.current_session_id = session.id
        else:
            # 临时用户，创建默认会话
            logger.info(f"临时用户连接（无AK）: {context.user_id}")
            session = await self.create_session(context)
            context.current_session_id = session.id
        
        # 发送初始会话信息
        await self.send_sessions_list(context)
        
        # 如果有当前会话，发送其消息历史
        if context.current_session_id:
            await self.send_session_messages(context, context.current_session_id)
        
        # 发送 project_id 状态
        if not context.project_id and not os.environ.get('BOHR_PROJECT_ID'):
            await context.websocket.send_json({
                "type": "require_project_id",
                "content": "需要设置 Project ID 才能使用 Agent"
            })
        
    async def disconnect_client(self, websocket: WebSocket):
        """断开客户端连接"""
        if websocket in self.active_connections:
            context = self.active_connections[websocket]
            logger.info(f"用户断开连接: {context.user_id}")
            
            # 如果有AK，保存所有会话
            if context.access_key:
                for session in context.sessions.values():
                    try:
                        await self.persistent_manager.save_session(
                            context.access_key,
                            session
                        )
                        logger.info(f"断开连接时保存会话: {session.id}")
                    except Exception as e:
                        logger.error(f"保存会话失败: {e}")
            
            # 清理文件监视器
            context.cleanup()
            # 清理该连接的所有资源
            del self.active_connections[websocket]
    
    async def send_sessions_list(self, context: ConnectionContext):
        """发送会话列表到客户端"""
        sessions_data = []
        for session in context.sessions.values():
            sessions_data.append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "last_message_at": session.last_message_at.isoformat(),
                "message_count": len(session.messages)
            })
        
        message = {
            "type": "sessions_list",
            "sessions": sessions_data,
            "current_session_id": context.current_session_id
        }
        
        await context.websocket.send_json(message)
    
    async def send_session_messages(self, context: ConnectionContext, session_id: str):
        """发送会话的历史消息"""
        session = self.get_session(context, session_id)
        if not session:
            return
            
        messages_data = []
        for msg in session.messages:
            messages_data.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "tool_name": msg.tool_name,
                "tool_status": msg.tool_status
            })
        
        message = {
            "type": "session_messages",
            "session_id": session_id,
            "messages": messages_data
        }
        
        await context.websocket.send_json(message)
    
    async def send_to_connection(self, context: ConnectionContext, message: dict):
        """发送消息到特定连接"""
        # 为消息添加唯一标识符
        if 'id' not in message:
            message['id'] = f"{message.get('type', 'unknown')}_{datetime.now().timestamp()}"
        
        try:
            await context.websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            # 注意：这里不能使用 await，因为在同步上下文中
            # 创建一个新的任务来处理断开连接
            asyncio.create_task(self.disconnect_client(context.websocket))
    
    async def process_message(self, context: ConnectionContext, message: str):
        """处理用户消息"""
        # 首先检查是否有 project_id
        if not context.project_id and not os.environ.get('BOHR_PROJECT_ID'):
            await context.websocket.send_json({
                "type": "error", 
                "content": "🔒 请先选择您的项目"
            })
            return
        
        if not context.current_session_id:
            await context.websocket.send_json({
                "type": "error", 
                "content": "没有活动的会话"
            })
            return
            
        # 等待runner初始化完成
        retry_count = 0
        while context.current_session_id not in context.runners and retry_count < 50:  # 最多等待5秒
            await asyncio.sleep(0.1)
            retry_count += 1
            
        if context.current_session_id not in context.runners:
            await context.websocket.send_json({
                "type": "error", 
                "content": "会话初始化失败，请重试"
            })
            return
            
        session = context.sessions[context.current_session_id]
        runner = context.runners[context.current_session_id]
        
        # 保存用户消息到会话历史
        session.add_message("user", message)
        
        try:
            # 构建包含历史上下文的消息（如果有历史）
            if len(session.messages) > 1:  # 有历史消息
                # 构建历史上下文
                history_parts = []
                # 只取最近的消息，跳过刚刚添加的用户消息
                recent_messages = session.messages[-11:-1]  # 最多10条历史
                
                for msg in recent_messages:
                    if msg.role == 'user':
                        history_parts.append(f"用户: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                    elif msg.role == 'assistant':
                        history_parts.append(f"助手: {msg.content[:150]}{'...' if len(msg.content) > 150 else ''}")
                    elif msg.role == 'tool' and msg.tool_status == 'completed':
                        # 简化工具输出
                        tool_summary = f"[使用工具 {msg.tool_name}]"
                        history_parts.append(tool_summary)
                
                if history_parts:
                    # 构建增强消息
                    enhanced_message = f"[对话历史]\n{chr(10).join(history_parts[-8:])}\n\n[当前问题]\n{message}"
                    logger.info(f"包含 {len(history_parts)} 条历史消息在上下文中")
                    
                    content = types.Content(
                        role='user',
                        parts=[types.Part(text=enhanced_message)]
                    )
                else:
                    content = types.Content(
                        role='user',
                        parts=[types.Part(text=message)]
                    )
            else:
                # 没有历史，直接使用原始消息
                content = types.Content(
                    role='user',
                    parts=[types.Part(text=message)]
                )
            
            # 收集所有事件
            all_events = []
            seen_tool_calls = set()  # 跟踪已发送的工具调用
            seen_tool_responses = set()  # 跟踪已发送的工具响应
            
            async for event in runner.run_async(
                    new_message=content,
                    user_id=context.user_id,
                    session_id=context.current_session_id
                ):
                    all_events.append(event)
                    logger.info(f"Received event: {type(event).__name__}")
                    
                    # 检查事件中的工具调用（按照官方示例）
                    if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            # 检查是否是函数调用
                            if hasattr(part, 'function_call') and part.function_call:
                                function_call = part.function_call
                                tool_name = getattr(function_call, 'name', 'unknown')
                                tool_id = getattr(function_call, 'id', tool_name)
                                
                                # 避免重复发送相同的工具调用
                                if tool_id in seen_tool_calls:
                                    continue
                                seen_tool_calls.add(tool_id)
                                
                                tool_executing_msg = {
                                    "type": "tool",
                                    "tool_name": tool_name,
                                    "status": "executing",
                                    "timestamp": datetime.now().isoformat()
                                }
                                logger.info(f"Sending tool executing status: {tool_executing_msg}")
                                await self.send_to_connection(context, tool_executing_msg)
                                
                                # 不保存执行中的状态到历史记录
                                logger.info(f"Tool call detected: {tool_name}")
                                # 给前端一点时间来处理和显示执行状态
                                await asyncio.sleep(0.1)
                            
                            # 检查是否是函数响应（工具完成）
                            elif hasattr(part, 'function_response') and part.function_response:
                                function_response = part.function_response
                                # 从响应中获取更多信息
                                tool_name = "unknown"
                                
                                if hasattr(function_response, 'name'):
                                    tool_name = function_response.name
                                
                                # 创建唯一标识符
                                response_id = f"{tool_name}_response"
                                if hasattr(function_response, 'id'):
                                    response_id = function_response.id
                                
                                # 避免重复发送相同的工具响应
                                if response_id in seen_tool_responses:
                                    continue
                                seen_tool_responses.add(response_id)
                                
                                if hasattr(function_response, 'response'):
                                    response_data = function_response.response
                                    
                                    # 智能格式化不同类型的响应
                                    if isinstance(response_data, dict):
                                        # 如果是字典，尝试美化JSON格式
                                        try:
                                            result_str = json.dumps(response_data, indent=2, ensure_ascii=False)
                                        except:
                                            result_str = str(response_data)
                                    elif isinstance(response_data, (list, tuple)):
                                        # 如果是列表或元组，也尝试JSON格式化
                                        try:
                                            result_str = json.dumps(response_data, indent=2, ensure_ascii=False)
                                        except:
                                            result_str = str(response_data)
                                    elif isinstance(response_data, str):
                                        # 字符串直接使用，保留原始格式
                                        result_str = response_data
                                    else:
                                        # 其他类型转换为字符串
                                        result_str = str(response_data)
                                    
                                    tool_completed_msg = {
                                        "type": "tool",
                                        "tool_name": tool_name,
                                        "status": "completed",
                                        "result": result_str,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    logger.info(f"Sending tool completed status: {tool_name}")
                                    await self.send_to_connection(context, tool_completed_msg)
                                    
                                    # 保存工具完成消息到会话历史
                                    session.add_message("tool", result_str, tool_name=tool_name, tool_status="completed")
                                else:
                                    # 没有结果的情况
                                    await self.send_to_connection(context, {
                                        "type": "tool",
                                        "tool_name": tool_name,
                                        "status": "completed",
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    # 保存工具完成消息到会话历史（无结果）
                                    session.add_message("tool", f"工具 {tool_name} 执行完成", tool_name=tool_name, tool_status="completed")
                                
                                logger.info(f"Tool response received: {tool_name}")
            
            # 处理所有事件，只获取最后一个有效响应
            logger.info(f"Total events: {len(all_events)}")
            
            final_response = None
            # 从后往前查找最后一个有效的响应
            for event in reversed(all_events):
                if hasattr(event, 'content') and event.content:
                    content = event.content
                    # 处理 Google ADK 的 Content 对象
                    if hasattr(content, 'parts') and content.parts:
                        # 提取所有文本部分
                        text_parts = []
                        for part in content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            final_response = '\n'.join(text_parts)
                            break
                        elif hasattr(content, 'text') and content.text:
                            final_response = content.text
                            break
                    elif hasattr(event, 'text') and event.text:
                        final_response = event.text
                        break
                    elif hasattr(event, 'output') and event.output:
                        final_response = event.output
                        break
                    elif hasattr(event, 'message') and event.message:
                        final_response = event.message
                        break
            
            # 只发送最后一个响应内容
            if final_response:
                logger.info(f"Sending final response: {final_response[:200]}")
                # 保存助手回复到会话历史
                session.add_message("assistant", final_response)
                
                await self.send_to_connection(context, {
                    "type": "assistant",
                    "content": final_response,
                    "session_id": context.current_session_id
                })
            else:
                logger.warning("No response content found in events")
            
            # 发送一个空的完成标记，前端会识别这个来停止loading
            await self.send_to_connection(context, {
                "type": "complete",
                "content": ""
            })
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"处理消息时出错: {e}\n{error_details}")
            
            # 如果是 ExceptionGroup，尝试提取更多信息
            if hasattr(e, '__cause__') and e.__cause__:
                logger.error(f"根本原因: {e.__cause__}")
            if hasattr(e, 'exceptions'):
                logger.error(f"子异常数量: {len(e.exceptions)}")
                for i, sub_exc in enumerate(e.exceptions):
                    logger.error(f"子异常 {i}: {sub_exc}", exc_info=(type(sub_exc), sub_exc, sub_exc.__traceback__))
            
                await context.websocket.send_json({
                    "type": "error",
                    "content": f"处理消息失败: {str(e)}"
                })
        
        # 如果有AK，保存会话
        if context.access_key and context.current_session_id:
            try:
                await self.persistent_manager.save_session(
                    context.access_key,
                    session
                )
                logger.info(f"已自动保存会话: {session.id}")
            except Exception as e:
                logger.error(f"自动保存会话失败: {e}")