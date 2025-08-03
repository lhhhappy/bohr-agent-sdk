"""
文件监控功能
"""
import asyncio
import time
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from datetime import datetime
from watchdog.events import FileSystemEventHandler, FileSystemEvent

if TYPE_CHECKING:
    from server.connection import ConnectionContext

logger = logging.getLogger(__name__)


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
            import os
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