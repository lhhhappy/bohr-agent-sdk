// API and Server Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || '',
  WS_ENDPOINT: '/ws',
  API_ENDPOINTS: {
    FILES: '/api/files',
    FILE_TREE: '/api/files/tree',
    STATUS: '/api/status',
    CONFIG: '/api/config',
  },
}

// WebSocket Configuration
export const WS_CONFIG = {
  RECONNECT_DELAY: 3000,
  MESSAGE_TYPES: {
    MESSAGE: 'message',
    CREATE_SESSION: 'create_session',
    SWITCH_SESSION: 'switch_session',
    DELETE_SESSION: 'delete_session',
    SESSIONS_LIST: 'sessions_list',
    SESSION_MESSAGES: 'session_messages',
    SHELL_COMMAND: 'shell_command',
    SHELL_OUTPUT: 'shell_output',
    SHELL_ERROR: 'shell_error',
    USER: 'user',
    ASSISTANT: 'assistant',
    TOOL: 'tool',
    RESPONSE: 'response',
    COMPLETE: 'complete',
    ERROR: 'error',
  },
  TOOL_STATUS: {
    EXECUTING: 'executing',
    COMPLETED: 'completed',
  },
}

// UI Configuration
export const UI_CONFIG = {
  MESSAGE_ANIMATION_DELAY: 200,
  SCROLL_DELAY: 100,
  SESSION_CREATE_TIMEOUT: 3000,
  AUTO_REFRESH_INTERVAL: 5000,
}

// File Types
export const FILE_TYPES = {
  TEXT_EXTENSIONS: ['.json', '.md', '.txt', '.csv', '.py', '.js', '.ts', '.log', '.xml', '.yaml', '.yml'],
  IMAGE_EXTENSIONS: ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
}

// Default Messages
export const DEFAULT_MESSAGES = {
  WELCOME_TITLE: 'Welcome to Agent',
  WELCOME_MESSAGE: 'How can I help you today?',
  CONNECTION_ERROR: 'Unable to connect to server. Please try again later.',
  NO_SESSION_SELECTED: 'Select a session to view details',
}

// Shell Commands Configuration
export const SHELL_CONFIG = {
  SAFE_COMMANDS: [
    'ls', 'pwd', 'cd', 'cat', 'echo', 'grep', 'find', 'head', 'tail',
    'wc', 'sort', 'uniq', 'diff', 'cp', 'mv', 'mkdir', 'touch', 'date',
    'whoami', 'hostname', 'uname', 'df', 'du', 'ps', 'top', 'which',
    'git', 'npm', 'python', 'pip', 'node', 'yarn', 'curl', 'wget',
    'tree', 'clear', 'history'
  ],
  DANGEROUS_COMMANDS: [
    'rm', 'rmdir', 'kill', 'killall', 'shutdown', 'reboot', 'sudo',
    'su', 'chmod', 'chown', 'dd', 'format', 'mkfs', 'fdisk', 'apt',
    'yum', 'brew', 'systemctl', 'service', 'docker', 'kubectl'
  ],
}