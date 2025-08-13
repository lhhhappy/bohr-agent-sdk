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
        # 为每个连接生成唯一的user_id
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        # 文件监视器
        self.file_observers: List[Observer] = []
        self._setup_file_watchers()
    
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
            # 注意：这里使用 access_key 或生成的 user_id 作为 session_id 的替代
            if self.access_key:
                user_files_dir = user_file_manager.get_user_files_dir(access_key=self.access_key)
            else:
                # 临时用户，使用 user_id 作为 session_id
                user_files_dir = user_file_manager.get_user_files_dir(session_id=self.user_id)
            
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