"""
会话持久化管理
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
import aiofiles

from server.models import Session, Message

logger = logging.getLogger(__name__)


class PersistentSessionManager:
    """持久化会话管理器，用于保存和恢复用户会话"""
    
    def __init__(self, base_dir: str, sessions_dir: str = ".agent_sessions"):
        self.base_dir = Path(base_dir)
        # 支持自定义 sessions 目录，可以是绝对路径或相对路径
        sessions_path = Path(sessions_dir)
        if sessions_path.is_absolute():
            self.sessions_dir = sessions_path
        else:
            self.sessions_dir = self.base_dir / sessions_dir
        self.user_sessions_dir = self.sessions_dir / "user_sessions"
        self.user_sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: str) -> str:
        """获取用户目录名称"""
        # 直接使用user_id作为目录名，不再进行哈希
        return user_id
    
    async def load_user_sessions(self, user_id: str) -> Dict[str, Session]:
        """加载用户的历史会话"""
        if not user_id:
            return {}  # 没有用户ID，不加载历史
        
        user_dir_name = self._get_user_dir(user_id)
        user_dir = self.user_sessions_dir / user_dir_name / "sessions"
        
        if not user_dir.exists():
            return {}
        
        sessions = {}
        for session_file in user_dir.glob("*.json"):
            try:
                async with aiofiles.open(session_file, 'r', encoding='utf-8') as f:
                    data = json.loads(await f.read())
                    session = self._deserialize_session(data)
                    sessions[session.id] = session
            except Exception as e:
                logger.error(f"加载会话失败 {session_file}: {e}")
        
        return sessions
    
    async def save_session(self, user_id: str, session: Session):
        """保存单个会话"""
        if not user_id:
            return  # 没有用户ID不保存
        
        user_dir_name = self._get_user_dir(user_id)
        user_sessions_dir = self.user_sessions_dir / user_dir_name / "sessions"
        user_sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存元信息（首次）
        metadata_file = self.user_sessions_dir / user_dir_name / "metadata.json"
        if not metadata_file.exists():
            metadata = {
                "user_id": user_id,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
        else:
            # 更新最后访问时间
            try:
                async with aiofiles.open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.loads(await f.read())
                metadata["last_seen"] = datetime.now().isoformat()
                async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
            except Exception as e:
                logger.error(f"更新元信息失败: {e}")
        
        # 保存会话
        session_file = user_sessions_dir / f"{session.id}.json"
        try:
            async with aiofiles.open(session_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self._serialize_session(session), indent=2, ensure_ascii=False))
            logger.info(f"保存会话成功: {session.id}")
        except Exception as e:
            logger.error(f"保存会话失败 {session.id}: {e}")
    
    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """删除指定会话的持久化文件"""
        if not user_id:
            return True
        
        user_dir_name = self._get_user_dir(user_id)
        session_file = self.user_sessions_dir / user_dir_name / "sessions" / f"{session_id}.json"
        
        if session_file.exists():
            try:
                session_file.unlink()
                logger.info(f"删除持久化会话文件: {session_id}")
                return True
            except Exception as e:
                logger.error(f"删除会话文件失败: {e}")
                return False
        return True
    
    def _serialize_session(self, session: Session) -> dict:
        """序列化会话对象"""
        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "last_message_at": session.last_message_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "tool_name": msg.tool_name,
                    "tool_status": msg.tool_status
                }
                for msg in session.messages
            ]
        }
    
    def _deserialize_session(self, data: dict) -> Session:
        """反序列化会话对象"""
        session = Session(
            id=data["id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_message_at=datetime.fromisoformat(data["last_message_at"])
        )
        
        for msg_data in data["messages"]:
            message = Message(
                id=msg_data["id"],
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                tool_name=msg_data.get("tool_name"),
                tool_status=msg_data.get("tool_status")
            )
            session.messages.append(message)
        
        return session