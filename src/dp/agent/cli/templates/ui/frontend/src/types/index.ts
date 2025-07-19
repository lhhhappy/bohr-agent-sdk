// Message Types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  timestamp: Date
  tool_name?: string
  tool_status?: string
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
    outputDirectory: string
    watchDirectories: string[]
  }
  websocket: {
    host: string
    port: number
  }
  server: {
    port: number
    host: string[]
  }
}

// WebSocket Message Types
export interface WSMessage {
  type: string
  content?: string
  timestamp?: string
  id?: string
  [key: string]: any
}

// Connection Status
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'