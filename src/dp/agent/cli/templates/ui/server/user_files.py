"""
用户文件管理器
"""
import os
from pathlib import Path
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
        self.user_sessions_dir = self.sessions_dir / "user_sessions"
        self.temp_sessions_dir = self.sessions_dir / "temp_sessions"
        
        # 确保目录存在
        self.user_sessions_dir.mkdir(parents=True, exist_ok=True)
        self.temp_sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: str) -> str:
        """获取用户目录名称"""
        # 直接使用user_id作为目录名
        return user_id
    
    def get_user_files_dir(self, user_id: str) -> Path:
        """获取用户的文件目录
        
        Args:
            user_id: 用户的唯一标识符（Bohrium user_id 或临时用户ID）
            
        Returns:
            用户的文件目录路径
        """
        if not user_id:
            # 如果没有user_id，使用默认目录
            user_files_dir = self.temp_sessions_dir / "default" / "files"
        elif user_id.startswith("user_"):
            # 临时用户（生成的ID以user_开头）
            user_files_dir = self.temp_sessions_dir / user_id / "files"
        else:
            # 注册用户（Bohrium user_id）
            user_dir_name = self._get_user_dir(user_id)
            user_files_dir = self.user_sessions_dir / user_dir_name / "files"
        
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