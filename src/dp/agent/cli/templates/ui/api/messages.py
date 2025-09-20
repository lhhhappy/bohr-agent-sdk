"""
User-facing messages for API modules
Supports internationalization - Chinese and English messages
"""

# Language detection helper
def get_message(messages_dict, lang='zh'):
    """Get message in specified language, fallback to Chinese"""
    return messages_dict.get(lang, messages_dict.get('zh'))

# Error messages
ERROR_MESSAGES = {
    'access_denied': {
        'zh': '访问被拒绝',
        'en': 'Access denied'
    },
    'invalid_file_path': {
        'zh': '无效的文件路径',
        'en': 'Invalid file path'
    },
    'file_not_found': {
        'zh': '文件未找到',
        'en': 'File not found'
    },
    'folder_not_found': {
        'zh': '文件夹未找到',
        'en': 'Folder not found'
    },
    'file_or_folder_not_found': {
        'zh': '文件或文件夹不存在',
        'en': 'File or folder does not exist'
    },
    'decode_error': {
        'zh': '无法解码文件内容',
        'en': 'Unable to decode file content'
    },
    'session_not_exist': {
        'zh': '会话不存在',
        'en': 'Session does not exist'
    },
    'delete_session_failed': {
        'zh': '删除会话失败',
        'en': 'Failed to delete session'
    },
    'invalid_project_id': {
        'zh': '无效的 Project ID: {project_id}，必须是整数',
        'en': 'Invalid Project ID: {project_id}, must be an integer'
    },
    'project_id_required': {
        'zh': '请先设置项目 ID 后再上传文件。',
        'en': 'Please set project ID before uploading files.'
    },
    'unsupported_file_type': {
        'zh': '不支持的文件类型: {file_ext}',
        'en': 'Unsupported file type: {file_ext}'
    },
    'file_too_large': {
        'zh': '文件 {filename} 超过大小限制 (10MB)',
        'en': 'File {filename} exceeds size limit (10MB)'
    },
    'no_permission_project': {
        'zh': '您没有权限使用项目 ID: {project_id}。请从项目列表中选择您有权限的项目。',
        'en': 'You do not have permission to use project ID: {project_id}. Please select a project you have permission for.'
    },
    'accesskey_not_found': {
        'zh': '未找到 AccessKey',
        'en': 'AccessKey not found'
    },
    'appkey_not_found': {
        'zh': '未找到 AppKey',
        'en': 'AppKey not found'
    },
    'accesskey_or_appkey_not_found': {
        'zh': '未找到 AccessKey 或 AppKey',
        'en': 'AccessKey or AppKey not found'
    },
    'get_project_list_failed': {
        'zh': '获取项目列表失败',
        'en': 'Failed to get project list'
    },
    'project_not_belong_to_user': {
        'zh': '该项目不属于当前用户',
        'en': 'This project does not belong to current user'
    },
    'temp_user_no_session': {
        'zh': '临时用户没有历史会话',
        'en': 'Temporary users have no session history'
    },
    'temp_user_cannot_export': {
        'zh': '临时用户没有会话可导出',
        'en': 'Temporary users have no sessions to export'
    },
    'no_session_found': {
        'zh': '没有找到会话',
        'en': 'No sessions found'
    },
    'clear_failed': {
        'zh': '清除失败: {error}',
        'en': 'Clear failed: {error}'
    },
    'export_failed': {
        'zh': '导出失败: {error}',
        'en': 'Export failed: {error}'
    },
    'no_active_session': {
        'zh': '没有活动的会话',
        'en': 'No active session'
    },
    'session_service_not_initialized': {
        'zh': '会话服务未初始化',
        'en': 'Session service not initialized'
    },
    'get_session_list_failed': {
        'zh': '获取会话列表失败',
        'en': 'Failed to get session list'
    },
    'get_session_messages_failed': {
        'zh': '获取会话消息失败',
        'en': 'Failed to get session messages'
    },
    'please_set_project_id': {
        'zh': '🔒 请先设置项目 ID',
        'en': '🔒 Please set project ID first'
    }
}

# Success messages
SUCCESS_MESSAGES = {
    'project_id_set': {
        'zh': 'Project ID 已设置为: {project_id}',
        'en': 'Project ID set to: {project_id}'
    },
    'project_id_set_from_env': {
        'zh': 'Project ID 已从环境变量设置为: {project_id} (开发模式)',
        'en': 'Project ID set from environment variable: {project_id} (development mode)'
    },
    'delete_success': {
        'zh': '成功删除: {filename}',
        'en': 'Successfully deleted: {filename}'
    },
    'session_cleared': {
        'zh': '历史会话已清除',
        'en': 'Session history cleared'
    },
    'no_session_to_clear': {
        'zh': '没有找到历史会话',
        'en': 'No session history found'
    }
}

# UI labels
UI_LABELS = {
    'workspace': {
        'zh': '工作空间',
        'en': 'Workspace'
    },
    'websocket_server_running': {
        'zh': '{agent_name} WebSocket 服务器正在运行',
        'en': '{agent_name} WebSocket server is running'
    }
}