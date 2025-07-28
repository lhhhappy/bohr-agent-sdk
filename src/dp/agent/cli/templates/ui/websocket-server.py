#!/usr/bin/env python3
"""
Agent WebSocket 服务器
使用 Session 运行 rootagent，并通过 WebSocket 与前端通信
"""

import os
import sys

# Add user working directory to Python path first
user_working_dir = os.environ.get('USER_WORKING_DIR')
if user_working_dir and user_working_dir not in sys.path:
    sys.path.insert(0, user_working_dir)

# Add UI template directory to Python path for config imports
ui_template_dir = os.environ.get('UI_TEMPLATE_DIR')
if ui_template_dir and ui_template_dir not in sys.path:
    sys.path.insert(0, ui_template_dir)

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import time
from dataclasses import dataclass, field
import uuid
from http.cookies import SimpleCookie

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from google.adk import Runner
from google.adk.sessions import InMemorySessionService

# 暂时保留原始日志级别以便调试
# logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
from google.genai import types

# Import configuration
from config.agent_config import agentconfig

# Get agent from configuration
try:
    rootagent = agentconfig.get_agent()
    print(f"✅ 成功加载 agent: {agentconfig.config['agent']['module']}")
except Exception as e:
    print(f"❌ 加载 agent 失败: {e}")
    print(f"📂 当前工作目录: {os.getcwd()}")
    print(f"🐍 Python 路径: {sys.path}")
    print(f"📋 配置内容: {agentconfig.config}")
    raise

# 配置日志
# 检查是否已经有 handler，避免重复添加
logger = logging.getLogger(__name__)
if not logger.handlers:
    # 创建文件 handler，使用覆盖模式
    file_handler = logging.FileHandler('websocket.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加 handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    # 在日志文件中添加会话分隔符
    logger.info("="*80)
    logger.info(f"新的 WebSocket 服务器会话开始于 {datetime.now()}")
    logger.info("="*80)

@dataclass
class Message:
    id: str
    role: str  # 'user' or 'assistant' or 'tool'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: Optional[str] = None
    tool_status: Optional[str] = None

@dataclass 
class Session:
    id: str
    title: str = "New Session"
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_message_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, tool_name: Optional[str] = None, tool_status: Optional[str] = None):
        """Add message to session"""
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            tool_name=tool_name,
            tool_status=tool_status
        )
        self.messages.append(message)
        self.last_message_at = datetime.now()
        
        if self.title == "New Session" and role == "user" and len(self.messages) <= 2:
            self.title = content[:30] + "..." if len(content) > 30 else content
        
        return message

app = FastAPI(title="Agent WebSocket Server")

# 获取服务器配置
server_config = agentconfig.get_server_config()
allowed_hosts = server_config.get("allowedHosts", ["localhost", "127.0.0.1", "0.0.0.0"])

# 记录允许的主机列表
logger.info(f"允许的主机列表: {allowed_hosts}")

# 构建允许的 CORS origins
allowed_origins = []
for host in allowed_hosts:
    allowed_origins.extend([
        f"http://{host}:*",
        f"https://{host}:*",
        f"http://{host}",
        f"https://{host}"
    ])

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件 - 用于调试
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # 简单记录请求信息
            logger.info(f"收到请求: {request.method} {request.url.path}")
        except:
            # 忽略任何日志错误
            pass
        
        response = await call_next(request)
        return response

# Host 验证中间件
class HostValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        if host and host not in allowed_hosts:
            logger.warning(f"拒绝访问: Host '{host}' 不在允许列表中")
            return PlainTextResponse(
                content=f"Host '{host}' is not allowed",
                status_code=403
            )
        response = await call_next(request)
        return response

# 注意：中间件按相反顺序执行，最后添加的最先执行
# 所以先添加 HostValidation，再添加 RequestLogging
app.add_middleware(HostValidationMiddleware)
app.add_middleware(RequestLoggingMiddleware)


class FileChangeHandler(FileSystemEventHandler):
    """处理文件系统变化事件"""
    def __init__(self, context: 'ConnectionContext', watch_path: str):
        self.context = context
        self.watch_path = watch_path
        self.last_event_time = {}
        self.debounce_seconds = 0.5  # 防抖时间
        
    def should_ignore_path(self, path: str) -> bool:
        """检查是否应该忽略该路径"""
        # 忽略隐藏文件和临时文件
        path_obj = Path(path)
        for part in path_obj.parts:
            if part.startswith('.') or part.endswith('~') or part.endswith('.tmp'):
                return True
        return False
        
    def debounce_event(self, event_key: str) -> bool:
        """事件防抖，避免重复事件"""
        current_time = time.time()
        last_time = self.last_event_time.get(event_key, 0)
        
        if current_time - last_time < self.debounce_seconds:
            return True  # 应该忽略这个事件
            
        self.last_event_time[event_key] = current_time
        return False
        
    async def notify_file_change(self, event_type: str, path: str):
        """通知前端文件变化"""
        try:
            # 计算相对路径
            rel_path = os.path.relpath(path, self.watch_path)
            
            await self.context.websocket.send_json({
                "type": "file_change",
                "event_type": event_type,
                "path": path,
                "relative_path": rel_path,
                "watch_directory": self.watch_path,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"文件变化通知: {event_type} - {rel_path}")
        except Exception as e:
            logger.error(f"发送文件变化通知失败: {e}")
            
    def on_any_event(self, event: FileSystemEvent):
        """处理所有文件系统事件"""
        if event.is_directory:
            return  # 暂时忽略目录事件
            
        if self.should_ignore_path(event.src_path):
            return
            
        # 防抖处理
        event_key = f"{event.event_type}:{event.src_path}"
        if self.debounce_event(event_key):
            return
            
        # 映射事件类型
        event_map = {
            'created': 'created',
            'modified': 'modified',
            'deleted': 'deleted',
            'moved': 'moved'
        }
        
        event_type = event_map.get(event.event_type, event.event_type)
        
        # 使用 asyncio 在事件循环中运行异步通知
        asyncio.create_task(self.notify_file_change(event_type, event.src_path))


class ConnectionContext:
    """每个WebSocket连接的独立上下文"""
    def __init__(self, websocket: WebSocket, access_key: str = ""):
        self.websocket = websocket
        self.access_key = access_key  # 存储该连接的AK
        self.sessions: Dict[str, Session] = {}
        self.runners: Dict[str, Runner] = {}
        self.session_services: Dict[str, InMemorySessionService] = {}
        self.current_session_id: Optional[str] = None
        # 为每个连接生成唯一的user_id
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        # 文件监视器
        self.file_observers: List[Observer] = []
        self._setup_file_watchers()
    
    def _setup_file_watchers(self):
        """设置文件监视器"""
        try:
            # 从配置获取要监视的目录
            files_config = agentconfig.get_files_config()
            watch_directories = files_config.get("watch_directories", files_config.get("watchDirectories", []))
            
            if not watch_directories:
                logger.info("未配置监视目录")
                return
                
            user_working_dir = os.environ.get('USER_WORKING_DIR', os.getcwd())
            
            for watch_dir in watch_directories:
                # 处理相对路径
                if not os.path.isabs(watch_dir):
                    watch_path = os.path.join(user_working_dir, watch_dir)
                else:
                    watch_path = watch_dir
                    
                watch_path = os.path.normpath(watch_path)
                
                # 确保目录存在
                if not os.path.exists(watch_path):
                    os.makedirs(watch_path, exist_ok=True)
                    logger.info(f"创建监视目录: {watch_path}")
                
                if os.path.isdir(watch_path):
                    # 创建文件监视器
                    observer = Observer()
                    handler = FileChangeHandler(self, watch_path)
                    observer.schedule(handler, watch_path, recursive=True)
                    observer.start()
                    self.file_observers.append(observer)
                    logger.info(f"开始监视目录: {watch_path}")
                else:
                    logger.warning(f"监视路径不是目录: {watch_path}")
                    
        except Exception as e:
            logger.error(f"设置文件监视器失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        # 停止所有文件监视器
        for observer in self.file_observers:
            try:
                observer.stop()
                observer.join(timeout=1)
            except Exception as e:
                logger.error(f"停止文件监视器失败: {e}")
        self.file_observers.clear()

def get_ak_info_from_request(headers) -> Tuple[str, str]:
    """从请求头中提取AK信息"""
    cookie_header = headers.get("cookie", "")
    if cookie_header:
        simple_cookie = SimpleCookie()
        simple_cookie.load(cookie_header)
        
        access_key = ""
        app_key = ""
        
        if "appAccessKey" in simple_cookie:
            access_key = simple_cookie["appAccessKey"].value
        if "clientName" in simple_cookie:
            app_key = simple_cookie["clientName"].value
            
        return access_key, app_key
    return "", ""

class SessionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, ConnectionContext] = {}
        # Use configuration values
        self.app_name = agentconfig.config.get("agent", {}).get("name", "Agent")
        
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
            session_service = InMemorySessionService()
            await session_service.create_session(
                app_name=self.app_name,
                user_id=context.user_id,
                session_id=session_id
            )
            
            runner = Runner(
                agent=rootagent,
                session_service=session_service,
                app_name=self.app_name
            )
            
            context.session_services[session_id] = session_service
            context.runners[session_id] = runner
            
            logger.info(f"Runner 初始化完成: {session_id}")
            
        except Exception as e:
            logger.error(f"初始化Runner失败: {e}")
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
    
    def delete_session(self, context: ConnectionContext, session_id: str) -> bool:
        """删除会话"""
        if session_id in context.sessions:
            del context.sessions[session_id]
            if session_id in context.runners:
                del context.runners[session_id]
            if session_id in context.session_services:
                del context.session_services[session_id]
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
    
    async def connect_client(self, websocket: WebSocket, access_key: str = ""):
        """连接新客户端"""
        await websocket.accept()
        
        # 为新连接创建独立的上下文，包含AK
        context = ConnectionContext(websocket, access_key)
        self.active_connections[websocket] = context
        
        logger.info(f"新用户连接: {context.user_id}, AK: {access_key[:8]}..." if access_key else f"新用户连接: {context.user_id}")
        
        # 创建默认会话
        session = await self.create_session(context)
        context.current_session_id = session.id
            
        # 发送初始会话信息
        await self.send_sessions_list(context)
        
    def disconnect_client(self, websocket: WebSocket):
        """断开客户端连接"""
        if websocket in self.active_connections:
            context = self.active_connections[websocket]
            logger.info(f"用户断开连接: {context.user_id}")
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
            self.disconnect_client(context.websocket)
    
    async def process_message(self, context: ConnectionContext, message: str):
        """处理用户消息"""
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
        
        # 保存原始的AK环境变量（如果存在）
        original_ak = os.environ.get("AK")
        
        try:
            # 设置当前连接的AK
            if context.access_key:
                os.environ["AK"] = context.access_key
                logger.info(f"设置环境变量 AK: {context.access_key}...")
            
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
                            else:
                                # 没有结果的情况
                                await self.send_to_connection(context, {
                                    "type": "tool",
                                    "tool_name": tool_name,
                                    "status": "completed",
                                    "timestamp": datetime.now().isoformat()
                                })
                            
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
        
        finally:
            # 恢复原始环境变量
            if original_ak is not None:
                os.environ["AK"] = original_ak
                logger.info("恢复原始环境变量 AK")
            elif "AK" in os.environ:
                del os.environ["AK"]
                logger.info("删除环境变量 AK")

# 创建全局管理器
manager = SessionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    # 提取AK信息
    access_key, _ = get_ak_info_from_request(websocket.headers)
    
    await manager.connect_client(websocket, access_key)
    
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
                if session_id and manager.delete_session(context, session_id):
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
                    
                
    except WebSocketDisconnect:
        manager.disconnect_client(websocket)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        manager.disconnect_client(websocket)

@app.get("/api/files/tree")
async def get_file_tree(path: str = None):
    """获取文件树结构"""
    try:
        user_working_dir = os.environ.get('USER_WORKING_DIR', Path.cwd())
        files_config = agentconfig.get_files_config()
        
        def build_tree(directory: Path):
            items = []
            try:
                for item in sorted(directory.iterdir()):
                    if item.name.startswith('.'):
                        continue
                        
                    node = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file"
                    }
                    
                    if item.is_dir():
                        node["children"] = build_tree(item)
                    else:
                        node["size"] = item.stat().st_size
                        
                    items.append(node)
            except PermissionError:
                pass
            return items
        
        if path is None:
            # Return all watched directories
            watch_directories = files_config.get("watchDirectories", files_config.get("watch_directories", []))
            
            logger.info(f"Files config: {files_config}")
            logger.info(f"Watch directories: {watch_directories}")
            logger.info(f"Full agent config: {agentconfig.config}")
            logger.info(f"Config path: {os.environ.get('AGENT_CONFIG_PATH', 'Not set')}")
            
            # Use watch directories
            all_directories = set(watch_directories)
            
            logger.info(f"All directories to show: {all_directories}")
            
            # Build tree for all directories
            tree = []
            for dir_path in sorted(all_directories):
                # Handle relative paths
                if not os.path.isabs(dir_path):
                    full_path = Path(user_working_dir) / dir_path
                else:
                    full_path = Path(dir_path)
                    
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    
                if full_path.is_dir():
                    dir_node = {
                        "name": dir_path.replace("./", ""),
                        "path": str(full_path),
                        "type": "directory",
                        "isExpanded": True,
                        "children": build_tree(full_path)
                    }
                    tree.append(dir_node)
                    
            logger.info(f"返回的文件树: {json.dumps(tree, indent=2)}")
            return JSONResponse(content=tree)
        else:
            # Handle specific path request
            base_path = Path(user_working_dir) / path
            if not base_path.exists():
                base_path.mkdir(parents=True, exist_ok=True)
            return JSONResponse(content=build_tree(base_path))
        
    except Exception as e:
        logger.error(f"获取文件树错误: {e}")
        return JSONResponse(content=[], status_code=500)

@app.get("/api/files{file_path:path}")
async def get_file_content(file_path: str):
    """获取文件内容"""
    try:
        # Handle absolute paths that were returned by file tree
        if file_path.startswith('/'):
            file = Path(file_path)
        else:
            # Handle relative paths
            user_working_dir = os.environ.get('USER_WORKING_DIR', Path.cwd())
            file = Path(user_working_dir) / file_path
            
        if not file.exists() or not file.is_file():
            return JSONResponse(
                content={"error": "文件未找到"},
                status_code=404
            )
        
        # 判断文件类型
        suffix = file.suffix.lower()
        
        # 文本文件
        if suffix in ['.json', '.md', '.txt', '.csv', '.py', '.js', '.ts', '.log', '.xml', '.yaml', '.yml']:
            try:
                content = file.read_text(encoding='utf-8')
                return PlainTextResponse(content)
            except UnicodeDecodeError:
                return JSONResponse(
                    content={"error": "无法解码文件内容"},
                    status_code=400
                )
        else:
            # 二进制文件
            return FileResponse(file)
            
    except Exception as e:
        logger.error(f"读取文件错误: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/api/status")
async def status():
    """API 状态"""
    return {
        "message": f"{agentconfig.config.get('agent', {}).get('name', 'Agent')} WebSocket 服务器正在运行",
        "mode": "session",
        "endpoints": {
            "websocket": "/ws",
            "files": "/api/files",
            "file_tree": "/api/files/tree",
            "config": "/api/config"
        }
    }

@app.get("/api/config")
async def get_config():
    """获取前端配置信息"""
    return JSONResponse(content={
        "agent": agentconfig.config.get("agent", {}),
        "ui": agentconfig.get_ui_config(),
        "files": agentconfig.get_files_config(),
        "websocket": agentconfig.get_websocket_config()
    })


# 挂载静态文件服务
# 获取 UI 静态文件目录
ui_template_dir = Path(os.environ.get('UI_TEMPLATE_DIR', Path(__file__).parent))
static_dir = ui_template_dir / "frontend" / "ui-static"

# 检查静态文件目录是否存在
if static_dir.exists():
    # 先定义其他所有路由，最后挂载静态文件
    # 这样可以确保 API 和 WebSocket 路由优先匹配
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    print(f"📁 静态文件目录: {static_dir}")
else:
    print(f"⚠️  静态文件目录不存在: {static_dir}")

if __name__ == "__main__":
    print("🚀 启动 Agent WebSocket 服务器...")
    # 统一使用 server 配置
    server_config = agentconfig.config.get('server', {})
    port = server_config.get('port', 8000)
    # host 数组中的第一个作为显示用
    hosts = server_config.get('host', ['localhost'])
    display_host = hosts[0] if isinstance(hosts, list) else hosts
    
    print("📡 使用 Session 模式运行 rootagent")
    print(f"🌐 服务器地址: http://{display_host}:{port}")
    print(f"🔌 WebSocket 端点: ws://{display_host}:{port}/ws")
    
    # uvicorn 始终监听 0.0.0.0 以支持所有配置的主机
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",  # 使用 info 级别，过滤掉 warning
        access_log=False,  # 禁用访问日志，减少噪音
        # 添加自定义的日志配置
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"]
            },
            "loggers": {
                "uvicorn.error": {
                    "level": "ERROR"
                },
                "uvicorn.access": {
                    "handlers": [],
                    "propagate": False
                }
            }
        }
    )