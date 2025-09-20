"""
Constants for API modules
"""

# File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_UPLOAD = 10

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'csv', 'json', 'xml', 
    'png', 'jpg', 'jpeg', 'gif', 'svg', 
    'py', 'js', 'ts', 'java', 'cpp', 'c',
    'md', 'rst', 'yaml', 'yml', 'log',
    'html', 'htm', 'css', 'scss',
    'sh', 'bash', 'sql', 'toml'
}

# WebSocket message types
WS_MESSAGE_TYPES = {
    'MESSAGE': 'message',
    'CREATE_SESSION': 'create_session',
    'SWITCH_SESSION': 'switch_session',
    'GET_SESSIONS': 'get_sessions',
    'DELETE_SESSION': 'delete_session',
    'SET_PROJECT_ID': 'set_project_id',
    'ERROR': 'error',
    'PROJECT_ID_SET': 'project_id_set',
    'SESSION_MESSAGES': 'session_messages'
}

# Session states
SESSION_STATES = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'DELETED': 'deleted'
}

# API endpoints
API_ENDPOINTS = {
    'WEBSOCKET': '/ws',
    'FILES': '/api/files',
    'FILE_TREE': '/api/files/tree',
    'CONFIG': '/api/config',
    'PROJECTS': '/api/projects',
    'SESSIONS': '/api/sessions',
    'DEBUG': '/api/debug'
}

# File operations
FILE_OPS = {
    'DOWNLOAD': 'download',
    'UPLOAD': 'upload',
    'DELETE': 'delete',
    'LIST': 'list'
}

# Default values
DEFAULT_WORKSPACE_NAME = "Workspace"
DEFAULT_SESSION_LIMIT = 50
DEFAULT_MESSAGE_LIMIT = 100