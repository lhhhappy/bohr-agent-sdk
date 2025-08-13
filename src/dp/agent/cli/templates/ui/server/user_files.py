"""
用户文件管理器
"""
import os
import hashlib
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserFileManager:
    """管理用户特定的文件目录"""
    
    def __init__(self, base_dir: str, sessions_dir: str = ".agent_sessions"):
        self.base_dir = Path(base_dir)
        # 支持自定义 sessions 目录，可以是绝对路径或相对路径
        sessions_path = Path(sessions_dir)
        if sessions_path.is_absolute():
            self.sessions_dir = sessions_path
        else:
            self.sessions_dir = self.base_dir / sessions_dir
        self.ak_sessions_dir = self.sessions_dir / "ak_sessions"
        self.temp_sessions_dir = self.sessions_dir / "temp_sessions"
        
        # 确保目录存在
        self.ak_sessions_dir.mkdir(parents=True, exist_ok=True)
        self.temp_sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_ak_hash(self, access_key: str) -> str:
        """生成AK的安全哈希值"""
        return hashlib.sha256(access_key.encode()).hexdigest()[:16]
    
    def get_user_files_dir(self, access_key: Optional[str] = None, session_id: Optional[str] = None) -> Path:
        """获取用户的文件目录
        
        Args:
            access_key: 用户的 access key
            session_id: 临时用户的 session ID
            
        Returns:
            用户的文件目录路径
        """
        if access_key:
            # 有 AK 的用户
            ak_hash = self._get_ak_hash(access_key)
            user_files_dir = self.ak_sessions_dir / ak_hash / "files"
        elif session_id:
            # 临时用户，使用 session_id
            user_files_dir = self.temp_sessions_dir / session_id / "files"
        else:
            # 如果都没有，使用默认的临时目录
            user_files_dir = self.temp_sessions_dir / "default" / "files"
        
        # 确保目录存在
        user_files_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建默认的 output 子目录
        output_dir = user_files_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        logger.info(f"用户文件目录: {user_files_dir}")
        return user_files_dir
    
    def cleanup_temp_files(self, max_age_days: int = 7):
        """清理过期的临时用户文件
        
        Args:
            max_age_days: 文件最大保留天数
        """
        import time
        import shutil
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        # 只清理临时会话目录
        if not self.temp_sessions_dir.exists():
            return
        
        for session_dir in self.temp_sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            # 检查目录的修改时间
            dir_mtime = session_dir.stat().st_mtime
            if current_time - dir_mtime > max_age_seconds:
                try:
                    shutil.rmtree(session_dir)
                    logger.info(f"清理过期临时文件目录: {session_dir}")
                except Exception as e:
                    logger.error(f"清理临时文件失败: {e}")