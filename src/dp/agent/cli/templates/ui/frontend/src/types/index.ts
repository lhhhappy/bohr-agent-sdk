// Message Types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  timestamp: Date
  tool_name?: string
  tool_status?: string
  tool_args?: any  // 工具调用参数
  isStreaming?: boolean
}

// Session Types
export interface Session {
  id: string
  title: string
  created_at: string
  last_message_at: string
  message_count: number
}

// File Types
export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
  isExpanded?: boolean
  size?: number
  modified?: string
}

// Shell Types
export interface ShellOutput {
  type: 'command' | 'output' | 'error'
  content: string
  timestamp: Date
}

// Agent Configuration Types
export interface AgentConfig {
  agent: {
    name: string
    description: string
    welcomeMessage: string
    module: string
    rootAgent: string
  }
  ui: {
    title: string
    theme?: string
    features?: {
      showFileExplorer?: boolean
      showSessionList?: boolean
    }
  }
  files: {
    watchDirectories: string[]
  }
  server: {
    port: number
    host: string[]
  }
  user_type?: 'registered' | 'temporary'
}

// WebSocket Message Types

// 基础消息接口
interface BaseWSMessage {
  type: string
  timestamp?: string
  id?: string
}

// 具体的消息类型定义
export interface SessionCreatedMessage extends BaseWSMessage {
  type: 'session_created'
  session_id: string
}

export interface MessageMessage extends BaseWSMessage {
  type: 'message'
  message: Message
}

export interface FileChangeMessage extends BaseWSMessage {
  type: 'file_change'
  event_type: string
  relative_path: string
  watch_directory: string
}

export interface ErrorMessage extends BaseWSMessage {
  type: 'error'
  error: string
}

export interface StatusMessage extends BaseWSMessage {
  type: 'status'
  status: string
}

export interface ContentMessage extends BaseWSMessage {
  type: string
  content: string
}

// 其他消息类型
export interface SessionsMessage extends BaseWSMessage {
  type: 'sessions'
  sessions: Session[]
  current_session_id?: string
}

export interface MessagesMessage extends BaseWSMessage {
  type: 'messages'
  messages: any[]
}

export interface ToolMessage extends BaseWSMessage {
  type: 'tool'
  tool_name: string
  status: string
  is_long_running?: boolean
  result?: string
}

export interface ToolCallMessage extends BaseWSMessage {
  type: 'tool_call'
  tool_name: string
  args: any
  status: string
}

export interface ToolResponseMessage extends BaseWSMessage {
  type: 'tool_response'
  tool_name: string
  result: string
  status: string
}

// 联合类型，包含所有可能的消息类型
export type WSMessage = 
  | SessionCreatedMessage 
  | MessageMessage 
  | FileChangeMessage 
  | ErrorMessage 
  | StatusMessage
  | ContentMessage
  | SessionsMessage
  | MessagesMessage
  | ToolMessage
  | ToolCallMessage
  | ToolResponseMessage
  | BaseWSMessage  // 兜底类型，用于未知的消息类型

// Connection Status
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'