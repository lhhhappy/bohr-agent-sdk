// UI Text Constants - Legacy support (deprecated, use translations.ts instead)
// This file is kept for backward compatibility
// New code should use the useTranslation hook
export const UI_TEXT = {
  // Connection Status
  CONNECTION: {
    CONNECTED: 'Connected',
    CONNECTING: 'Connecting...',
    DISCONNECTED: 'Disconnected',
    ERROR: 'Connection Error',
  },

  // Tool Messages
  TOOL: {
    EXECUTING: 'Executing tool',
    LONG_RUNNING: '(long running)',
    COMPLETED: 'Tool completed',
    STATUS_UPDATE: 'Tool status update',
  },

  // UI Actions
  ACTIONS: {
    SHOW_TERMINAL: 'Show Terminal',
    HIDE_TERMINAL: 'Hide Terminal',
    SHOW_FILES: 'Show Files',
    HIDE_FILES: 'Hide Files',
    SEND: 'Send',
    NEW_SESSION: 'New Session',
  },

  // Error Messages
  ERRORS: {
    GENERAL: 'Error',
    SERVER_DISCONNECTED: 'Not connected to server. Please try again later.',
    COMMAND_PARSE: 'Command parse error',
    COMMAND_EXECUTION: 'Command execution error',
    PERMISSION_DENIED: 'Permission denied',
    DANGEROUS_COMMAND: 'This command is potentially dangerous and has been blocked',
  },

  // Placeholders
  PLACEHOLDERS: {
    MESSAGE_INPUT: 'Type a message...',
    COMMAND_INPUT: 'Enter command...',
  },

  // Session Messages
  SESSION: {
    NEW_CONVERSATION: 'New Conversation',
    DELETE_CONFIRM: 'Are you sure you want to delete this session?',
  },

  // File Explorer
  FILES: {
    LOADING: 'Loading files...',
    LOAD_ERROR: 'Failed to load files',
    EMPTY: 'No files found',
  },
}