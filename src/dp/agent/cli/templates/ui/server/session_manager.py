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
from server.user_files import UserFileManager
from config.agent_config import agentconfig

logger = logging.getLogger(__name__)


class SessionManager:
    # 常量定义
    MAX_WAIT_TIME = 5  # runner初始化最大等待时间（秒）
    WAIT_INTERVAL = 0.1  # 等待间隔（秒）
    MAX_HISTORY_MESSAGES = 10  # 历史消息最大数量
    MAX_CONTEXT_MESSAGES = 8  # 上下文中包含的最大消息数
    USER_MESSAGE_TRUNCATE = 100  # 用户消息截断长度
    ASSISTANT_MESSAGE_TRUNCATE = 150  # 助手消息截断长度
    RESPONSE_PREVIEW_LENGTH = 200  # 响应预览长度
    def __init__(self):
        self.active_connections: Dict[WebSocket, ConnectionContext] = {}
        # Use configuration values
        self.app_name = agentconfig.config.get("agent", {}).get("name", "Agent")
        
        # 初始化持久化管理器
        user_working_dir = os.environ.get('USER_WORKING_DIR', os.getcwd())
        # 从配置中获取 sessions 目录路径
        files_config = agentconfig.get_files_config()
        sessions_dir = files_config.get('sessionsDir', '.agent_sessions')
        self.persistent_manager = PersistentSessionManager(user_working_dir, sessions_dir)
        # 初始化用户文件管理器
        self.user_file_manager = UserFileManager(user_working_dir, sessions_dir)
        
    async def create_session(self, context: ConnectionContext) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = Session(id=session_id)
        
        # 先将会话添加到连接的会话列表
        context.sessions[session_id] = session
        
        # 异步初始化runner，不阻塞返回
        asyncio.create_task(self._init_session_runner(context, session_id))
        
        return session
    
    def _cleanup_session(self, context: ConnectionContext, session_id: str):
        """统一的会话清理方法"""
        if session_id in context.sessions:
            del context.sessions[session_id]
        if session_id in context.runners:
            del context.runners[session_id]
        if session_id in context.session_services:
            del context.session_services[session_id]
    
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
            
        except Exception as e:
            logger.error(f"初始化Runner失败 (session_id: {session_id}): {e}", exc_info=True)
            # 清理失败的会话
            self._cleanup_session(context, session_id)
    
    def get_session(self, context: ConnectionContext, session_id: str) -> Optional[Session]:
        """获取会话"""
        return context.sessions.get(session_id)
    
    def get_all_sessions(self, context: ConnectionContext) -> List[Session]:
        """获取连接的所有会话列表"""
        return list(context.sessions.values())
    
    async def delete_session(self, context: ConnectionContext, session_id: str) -> bool:
        """删除会话"""
        if session_id not in context.sessions:
            return False
        
        # 清理会话
        self._cleanup_session(context, session_id)
        
        # 如果有AK，同时删除持久化文件
        if context.access_key:
            await self.persistent_manager.delete_session(context.access_key, session_id)
        
        return True
    
    async def switch_session(self, context: ConnectionContext, session_id: str) -> bool:
        """切换当前会话"""
        if session_id in context.sessions:
            context.current_session_id = session_id
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
                    for session_id in historical_sessions:
                        asyncio.create_task(self._init_session_runner(context, session_id))
                    
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
        
        # 注释掉 project_id 状态检查，允许用户自定义填写
        # if not context.project_id and not os.environ.get('BOHR_PROJECT_ID'):
        #     await context.websocket.send_json({
        #         "type": "require_project_id",
        #         "content": "需要设置 Project ID 才能使用 Agent"
        #     })
        
    async def disconnect_client(self, websocket: WebSocket):
        """断开客户端连接"""
        if websocket in self.active_connections:
            context = self.active_connections[websocket]
            
            # 如果有AK，保存所有会话
            if context.access_key:
                for session in context.sessions.values():
                    try:
                        await self.persistent_manager.save_session(
                            context.access_key,
                            session
                        )
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
    
    def _build_history_context(self, session: Session, current_message: str) -> types.Content:
        """构建包含历史上下文的消息"""
        if len(session.messages) <= 1:
            # 没有历史，直接使用原始消息
            return types.Content(
                role='user',
                parts=[types.Part(text=current_message)]
            )
        
        # 构建历史上下文
        history_parts = []
        recent_messages = session.messages[-(self.MAX_HISTORY_MESSAGES + 1):-1]
        
        for msg in recent_messages:
            if msg.role == 'user':
                truncated = msg.content[:self.USER_MESSAGE_TRUNCATE]
                suffix = '...' if len(msg.content) > self.USER_MESSAGE_TRUNCATE else ''
                history_parts.append(f"用户: {truncated}{suffix}")
            elif msg.role == 'assistant':
                truncated = msg.content[:self.ASSISTANT_MESSAGE_TRUNCATE]
                suffix = '...' if len(msg.content) > self.ASSISTANT_MESSAGE_TRUNCATE else ''
                history_parts.append(f"助手: {truncated}{suffix}")
            elif msg.role == 'tool' and msg.tool_status == 'completed':
                history_parts.append(f"[使用工具 {msg.tool_name}]")
        
        if history_parts:
            enhanced_message = f"[对话历史]\n{chr(10).join(history_parts[-self.MAX_CONTEXT_MESSAGES:])}\n\n[当前问题]\n{current_message}"
            return types.Content(
                role='user',
                parts=[types.Part(text=enhanced_message)]
            )
        
        return types.Content(
            role='user',
            parts=[types.Part(text=current_message)]
        )
    
    async def _handle_tool_events(self, event, context: ConnectionContext, session: Session, 
                                  seen_tool_calls: set, seen_tool_responses: set):
        """处理工具相关事件"""
        if not hasattr(event, 'content') or not event.content or not hasattr(event.content, 'parts'):
            return
        
        for part in event.content.parts:
            # 处理函数调用
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                tool_name = getattr(function_call, 'name', 'unknown')
                tool_id = getattr(function_call, 'id', tool_name)
                
                if tool_id not in seen_tool_calls:
                    seen_tool_calls.add(tool_id)
                    await self.send_to_connection(context, {
                        "type": "tool",
                        "tool_name": tool_name,
                        "status": "executing",
                        "timestamp": datetime.now().isoformat()
                    })
                    await asyncio.sleep(0.1)  # 给前端时间处理
            
            # 处理函数响应
            elif hasattr(part, 'function_response') and part.function_response:
                function_response = part.function_response
                tool_name = getattr(function_response, 'name', 'unknown')
                response_id = getattr(function_response, 'id', f"{tool_name}_response")
                
                if response_id not in seen_tool_responses:
                    seen_tool_responses.add(response_id)
                    
                    if hasattr(function_response, 'response'):
                        response_data = function_response.response
                        result_str = self._format_response_data(response_data)
                        
                        await self.send_to_connection(context, {
                            "type": "tool",
                            "tool_name": tool_name,
                            "status": "completed",
                            "result": result_str,
                            "timestamp": datetime.now().isoformat()
                        })
                        session.add_message("tool", result_str, tool_name=tool_name, tool_status="completed")
                    else:
                        await self.send_to_connection(context, {
                            "type": "tool",
                            "tool_name": tool_name,
                            "status": "completed",
                            "timestamp": datetime.now().isoformat()
                        })
                        session.add_message("tool", f"工具 {tool_name} 执行完成", tool_name=tool_name, tool_status="completed")
    
    def _format_response_data(self, response_data):
        """格式化响应数据"""
        if isinstance(response_data, (dict, list, tuple)):
            try:
                return json.dumps(response_data, indent=2, ensure_ascii=False)
            except:
                return str(response_data)
        return str(response_data) if not isinstance(response_data, str) else response_data
    
    def _extract_final_response(self, events: list) -> Optional[str]:
        """从事件列表中提取最终响应"""
        for event in reversed(events):
            if hasattr(event, 'content') and event.content:
                content = event.content
                if hasattr(content, 'parts') and content.parts:
                    text_parts = []
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        return '\n'.join(text_parts)
                    elif hasattr(content, 'text') and content.text:
                        return content.text
                elif hasattr(event, 'text') and event.text:
                    return event.text
                elif hasattr(event, 'output') and event.output:
                    return event.output
                elif hasattr(event, 'message') and event.message:
                    return event.message
        return None
    
    async def process_message(self, context: ConnectionContext, message: str):
        """处理用户消息"""
        # 检查是否设置了 project_id（必填但不验证所有权）
        if not context.project_id and not os.environ.get('BOHR_PROJECT_ID'):
            await context.websocket.send_json({
                "type": "error", 
                "content": "🔒 请先设置项目 ID"
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
        max_retries = int(self.MAX_WAIT_TIME / self.WAIT_INTERVAL)
        while context.current_session_id not in context.runners and retry_count < max_retries:
            await asyncio.sleep(self.WAIT_INTERVAL)
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
        
        # 获取用户特定的文件目录
        if context.access_key:
            user_files_dir = self.user_file_manager.get_user_files_dir(access_key=context.access_key)
        else:
            # 临时用户，使用 user_id 作为 session_id
            user_files_dir = self.user_file_manager.get_user_files_dir(session_id=context.user_id)
        
        # 保存当前工作目录
        original_cwd = os.getcwd()
        
        try:
            # 切换到用户文件目录
            os.chdir(user_files_dir)
            logger.info(f"切换工作目录到用户文件夹: {user_files_dir}")
            
            # 构建包含历史上下文的消息
            content = self._build_history_context(session, message)
            
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
                    # 处理工具相关事件
                    await self._handle_tool_events(event, context, session, seen_tool_calls, seen_tool_responses)
            
            # 提取最终响应
            final_response = self._extract_final_response(all_events)
            
            # 只发送最后一个响应内容
            if final_response:
                # 保存助手回复到会话历史
                session.add_message("assistant", final_response)
                
                await self.send_to_connection(context, {
                    "type": "assistant",
                    "content": final_response,
                    "session_id": context.current_session_id
                })
            
            # 发送一个空的完成标记，前端会识别这个来停止loading
            await self.send_to_connection(context, {
                "type": "complete",
                "content": ""
            })
                    
        except Exception as e:
            logger.error(f"处理消息时出错: {e}", exc_info=True)
            await context.websocket.send_json({
                "type": "error",
                "content": f"处理消息失败: {str(e)}"
            })
        finally:
            # 无论如何都要恢复原工作目录
            try:
                os.chdir(original_cwd)
                logger.info(f"恢复工作目录: {original_cwd}")
            except Exception as e:
                logger.error(f"恢复工作目录失败: {e}")
        
        # 如果有AK，保存会话
        if context.access_key and context.current_session_id:
            try:
                await self.persistent_manager.save_session(
                    context.access_key,
                    session
                )
            except Exception as e:
                logger.error(f"自动保存会话失败: {e}")