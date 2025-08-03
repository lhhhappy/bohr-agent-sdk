"""
数据模型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class Message:
    """消息数据模型"""
    id: str
    role: str  # 'user' or 'assistant' or 'tool'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: Optional[str] = None
    tool_status: Optional[str] = None


@dataclass 
class Session:
    """会话数据模型"""
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