"""
File monitoring functionality
"""
import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING
from datetime import datetime
from watchdog.events import FileSystemEventHandler, FileSystemEvent

if TYPE_CHECKING:
    from server.connection import ConnectionContext


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system change events"""
    def __init__(self, context: 'ConnectionContext', watch_path: str):
        self.context = context
        self.watch_path = watch_path
        self.last_event_time = {}
        self.debounce_seconds = 0.5  # Debounce time
        
    def should_ignore_path(self, path: str) -> bool:
        """Check if this path should be ignored"""
        # Ignore hidden files and temporary files
        path_obj = Path(path)
        for part in path_obj.parts:
            if part.startswith('.') or part.endswith('~') or part.endswith('.tmp'):
                return True
        return False
        
    def debounce_event(self, event_key: str) -> bool:
        """Event debounce, avoid duplicate events"""
        current_time = time.time()
        last_time = self.last_event_time.get(event_key, 0)
        
        if current_time - last_time < self.debounce_seconds:
            return True  # Should ignore this event
            
        self.last_event_time[event_key] = current_time
        return False
        
    async def notify_file_change(self, event_type: str, path: str):
        """Notify frontend of file changes"""
        try:
            # Calculate relative path
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
        except Exception as e:
            pass
            
    def on_any_event(self, event: FileSystemEvent):
        """Handle all file system events"""
        if event.is_directory:
            return  # Temporarily ignore directory events
            
        if self.should_ignore_path(event.src_path):
            return
            
        # Debounce handling
        event_key = f"{event.event_type}:{event.src_path}"
        if self.debounce_event(event_key):
            return
            
        # Map event types
        event_map = {
            'created': 'created',
            'modified': 'modified',
            'deleted': 'deleted',
            'moved': 'moved'
        }
        
        event_type = event_map.get(event.event_type, event.event_type)
        
        # Use asyncio to run async notification in event loop
        asyncio.create_task(self.notify_file_change(event_type, event.src_path))