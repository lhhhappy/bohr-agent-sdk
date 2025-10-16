"""
WebSocket connection management
"""
import os
import uuid
import asyncio
from typing import Optional, List
from fastapi import WebSocket
from watchdog.observers import Observer
from bohrium_open_sdk import OpenSDK

from server.file_watcher import FileChangeHandler
from server.user_files import UserFileManager
from config.agent_config import agentconfig


class ConnectionContext:
    """
    WebSocket connection context
    Manages independent state and resources for each connection
    """
    
    def __init__(self, websocket: WebSocket, access_key: str = "", app_key: str = ""):
        """
        Initialize connection context
        
        Args:
            websocket: WebSocket connection
            access_key: Bohrium access key
            app_key: Bohrium app key
        """
        # Basic connection info
        self.websocket = websocket
        self.access_key = access_key
        self.app_key = app_key
        
        # User identification
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"  # ADK user ID
        self.bohrium_user_id: Optional[str] = None  # Bohrium user ID
        
        # Project and session info
        self.project_id: Optional[int] = None
        self.current_session_id: Optional[str] = None
        
        # File watchers
        self.file_observers: List[Observer] = []
        
        # Connection state
        self.is_connected = True
        self.connected_at = asyncio.get_event_loop().time()
        
    async def init_bohrium_user_id(self):
        """
        Asynchronously initialize Bohrium user ID
        Get user info through OpenSDK
        """
        if self.access_key and self.app_key:
            try:
                # Execute sync operation in thread pool
                loop = asyncio.get_event_loop()
                user_info = await loop.run_in_executor(
                    None,
                    self._get_bohrium_user_info
                )
                
                if user_info and user_info.get('code') == 0:
                    data = user_info.get('data', {})
                    self.bohrium_user_id = data.get('user_id')
                    
            except Exception:
                pass
            
        # Initialize file watchers
        self._setup_file_watchers()
        
    def _get_bohrium_user_info(self):
        """
        Sync method: Get Bohrium user info
        """
        client = OpenSDK(
            access_key=self.access_key,
            app_key=self.app_key
        )
        return client.user.get_info()
        
    def get_user_identifier(self) -> str:
        """
        Get unique user identifier
        Use access_key if available (for registered users), otherwise use generated user_id

        Returns:
            User identifier
        """
        # 优先使用 access_key，保持与 HTTP API 的一致性
        if self.access_key:
            return self.access_key
        # 临时用户使用生成的 user_id
        return self.user_id
        
    def is_registered_user(self) -> bool:
        """
        Check if user is registered

        Returns:
            True if has access_key (registered Bohrium user)
        """
        return bool(self.access_key)
        
    def set_project_id(self, project_id: int):
        """
        Set project ID
        
        Args:
            project_id: Project ID
        """
        self.project_id = project_id
        
    def _setup_file_watchers(self):
        """
        Setup file watchers
        Monitor changes in user file directories
        """
        try:
            # Get user-specific file directory
            user_working_dir = os.environ.get('USER_WORKING_DIR', os.getcwd())
            files_config = agentconfig.get_files_config()
            sessions_dir = files_config.get('sessionsDir', '.agent_sessions')
            
            user_file_manager = UserFileManager(user_working_dir, sessions_dir)
            user_files_dir = user_file_manager.get_user_files_dir(user_id=self.get_user_identifier())
            
            watch_path = str(user_files_dir)
            
            # Ensure directory exists
            if not os.path.exists(watch_path):
                os.makedirs(watch_path, exist_ok=True)
                
            # Create file watcher
            event_handler = FileChangeHandler(self, watch_path)
            observer = Observer()
            observer.schedule(event_handler, watch_path, recursive=True)
            observer.start()
            
            self.file_observers.append(observer)
            
        except Exception:
            pass
            
    def cleanup(self):
        """
        Clean up connection resources
        Stop file watchers etc.
        """
        # Mark connection as disconnected
        self.is_connected = False
        
        # Stop all file watchers
        for observer in self.file_observers:
            try:
                observer.stop()
                observer.join(timeout=1)
            except Exception:
                pass
                
        self.file_observers.clear()
        
    async def send_json(self, data: dict):
        """
        Send JSON data to client
        
        Args:
            data: Data to send
        """
        if self.is_connected:
            try:
                await self.websocket.send_json(data)
            except Exception:
                self.is_connected = False
                
    async def receive_json(self) -> Optional[dict]:
        """
        Receive JSON data from client
        
        Returns:
            Received data or None
        """
        if self.is_connected:
            try:
                return await self.websocket.receive_json()
            except Exception:
                self.is_connected = False
                return None
        return None
        
    def get_connection_info(self) -> dict:
        """
        Get connection info
        
        Returns:
            Connection info dict
        """
        current_time = asyncio.get_event_loop().time()
        return {
            "user_id": self.get_user_identifier(),
            "is_registered": self.is_registered_user(),
            "project_id": self.project_id,
            "current_session_id": self.current_session_id,
            "connected_duration": current_time - self.connected_at,
            "is_connected": self.is_connected
        }
        
    def __repr__(self) -> str:
        """String representation"""
        return f"<ConnectionContext user={self.get_user_identifier()} connected={self.is_connected}>"