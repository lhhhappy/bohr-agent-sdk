"""
WebSocket 连接管理
"""
import os
import uuid
import logging
from typing import Optional, Dict, List
from fastapi import WebSocket
from watchdog.observers import Observer
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from bohrium_open_sdk import OpenSDK

from server.models import Session
from server.file_watcher import FileChangeHandler
from server.user_files import UserFileManager
from config.agent_config import agentconfig

logger = logging.getLogger(__name__)


class ConnectionContext:
    """每个WebSocket连接的独立上下文"""
    def __init__(self, websocket: WebSocket, access_key: str = "", app_key: str = ""):
        self.websocket = websocket
        self.access_key = access_key  # 存储该连接的AK
        self.app_key = app_key  # 存储该连接的app_key
        self.project_id: Optional[int] = None  # 从前端获取的project_id
        self.sessions: Dict[str, Session] = {}
        self.runners: Dict[str, Runner] = {}
        self.session_services: Dict[str, InMemorySessionService] = {}
        self.current_session_id: Optional[str] = None
        # 为每个连接生成唯一的user_id（用于ADK）
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        # Bohrium用户ID（从OpenSDK获取）
        self.bohrium_user_id: Optional[str] = None
        # 文件监视器
        self.file_observers: List[Observer] = []
    
    async def init_bohrium_user_id(self):
        """异步初始化Bohrium用户ID并设置文件监视器"""
        if self.access_key and self.app_key:
            try:
                # 使用OpenSDK获取用户信息
                import asyncio
                loop = asyncio.get_event_loop()
                
                # 在线程池中执行同步操作
                def get_user_info():
                    client = OpenSDK(
                        access_key=self.access_key,
                        app_key=self.app_key
                    )
                    return client.user.get_info()
                
                user_info = await loop.run_in_executor(None, get_user_info)
                
                if user_info and user_info.get('code') == 0:
                    data = user_info.get('data', {})
                    self.bohrium_user_id = data.get('user_id')
                    logger.info(f"获取到Bohrium用户ID: {self.bohrium_user_id}, 用户名: {data.get('name')}")
                else:
                    logger.warning(f"获取用户信息失败: {user_info}")
            except Exception as e:
                logger.error(f"调用OpenSDK获取用户信息失败: {e}")
        else:
            # 临时用户，没有AK
            logger.info(f"临时用户，使用生成的ID: {self.user_id}")
        
        # 获取用户信息后再设置文件监视器（只在没有设置过的情况下）
        if not self.file_observers:
            self._setup_file_watchers()
    
    def get_user_identifier(self) -> str:
        """获取用户唯一标识符，优先使用bohrium_user_id"""
        return self.bohrium_user_id if self.bohrium_user_id else self.user_id
    
    def _setup_file_watchers(self):
        """设置文件监视器"""
        try:
            # 获取用户特定的文件目录
            user_working_dir = os.environ.get('USER_WORKING_DIR', os.getcwd())
            # 从配置中获取 sessions 目录路径
            from config.agent_config import agentconfig
            files_config = agentconfig.get_files_config()
            sessions_dir = files_config.get('sessionsDir', '.agent_sessions')
            user_file_manager = UserFileManager(user_working_dir, sessions_dir)
            
            # 根据用户身份获取对应的文件目录
            # 使用统一的用户标识符
            user_identifier = self.get_user_identifier()
            user_files_dir = user_file_manager.get_user_files_dir(user_id=user_identifier)
            
            watch_path = str(user_files_dir)
            
            logger.info(f"设置文件监视器，监视目录: {watch_path}")
            
            # 确保目录存在
            if not os.path.exists(watch_path):
                os.makedirs(watch_path, exist_ok=True)
                logger.info(f"创建用户文件目录: {watch_path}")
            
            if os.path.isdir(watch_path):
                # 创建文件监视器
                observer = Observer()
                handler = FileChangeHandler(self, watch_path)
                observer.schedule(handler, watch_path, recursive=True)
                observer.start()
                self.file_observers.append(observer)
                logger.info(f"开始监视用户文件目录: {watch_path}")
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