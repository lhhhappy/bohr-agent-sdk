"""
User file manager
"""
from pathlib import Path


class UserFileManager:
    """Manage user-specific file directories"""
    
    def __init__(self, base_dir: str, sessions_dir: str = ".agent_sessions"):
        self.base_dir = Path(base_dir)
        # Support custom sessions directory, can be absolute or relative path
        sessions_path = Path(sessions_dir)
        if sessions_path.is_absolute():
            self.sessions_dir = sessions_path
        else:
            self.sessions_dir = self.base_dir / sessions_dir
        self.user_sessions_dir = self.sessions_dir / "user_sessions"
        self.temp_sessions_dir = self.sessions_dir / "temp_sessions"
        
        # Ensure directories exist
        self.user_sessions_dir.mkdir(parents=True, exist_ok=True)
        self.temp_sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: str) -> str:
        """Get user directory name"""
        # Use user_id directly as directory name
        return user_id
    
    def get_user_files_dir(self, user_id: str) -> Path:
        """Get user's file directory
        
        Args:
            user_id: User's unique identifier (Bohrium user_id or temporary user ID)
            
        Returns:
            User's file directory path
        """
        if not user_id:
            # If no user_id, use default directory
            user_files_dir = self.temp_sessions_dir / "default" / "files"
        elif user_id.startswith("user_"):
            # Temporary user (generated ID starts with user_)
            user_files_dir = self.temp_sessions_dir / user_id / "files"
        else:
            # Registered user (Bohrium user_id)
            user_dir_name = self._get_user_dir(user_id)
            user_files_dir = self.user_sessions_dir / user_dir_name / "files"
        
        # Ensure directory exists
        user_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default output subdirectory
        output_dir = user_files_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        return user_files_dir
    
    def cleanup_temp_files(self, max_age_days: int = 7):
        """Clean up expired temporary user files
        
        Args:
            max_age_days: Maximum days to keep files
        """
        import time
        import shutil
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        # Only clean temporary sessions directory
        if not self.temp_sessions_dir.exists():
            return
        
        for session_dir in self.temp_sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            # Check directory modification time
            dir_mtime = session_dir.stat().st_mtime
            if current_time - dir_mtime > max_age_seconds:
                try:
                    shutil.rmtree(session_dir)
                except Exception:
                    pass