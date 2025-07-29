import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, FileText } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import SessionList from './SessionList'
import FileExplorer from './FileExplorer'
import { ResizablePanel } from './ResizablePanel'
import { useAgentConfig } from '../hooks/useAgentConfig'
import { MessageAnimation, LoadingDots } from './MessageAnimation'
import { MemoizedMessage } from './MemoizedMessage'
import axios from 'axios'
import { Message, Session, FileNode, WSMessage } from '../types'

const API_BASE_URL = ''  // Use proxy in vite config


const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showLoadingDelay, setShowLoadingDelay] = useState(false)
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const [fileTree, setFileTree] = useState<FileNode[]>([])
  const [showFileExplorer, setShowFileExplorer] = useState(true) 
  const [projectId, setProjectId] = useState<string>('')
  const [tempProjectId, setTempProjectId] = useState<string>('')
  const [showProjectIdInput, setShowProjectIdInput] = useState(true)
  const [isProjectIdSet, setIsProjectIdSet] = useState(false)
  const [projectIdStatus, setProjectIdStatus] = useState<'idle' | 'updating' | 'success'>('idle')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const messageIdef = useRef<Set<string>>(new Set())
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Load agent configuration
  const { config } = useAgentConfig()

  // Show/hide project ID input based on user type
  useEffect(() => {
    console.log('Config:', config)
    console.log('User type:', config?.user_type)
    // Always show project ID input for all users
    setShowProjectIdInput(true)
  }, [config])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // 延迟显示加载动画，避免闪烁
  useEffect(() => {
    if (isLoading) {
      loadingTimeoutRef.current = setTimeout(() => {
        setShowLoadingDelay(true)
      }, 200) // 200ms 延迟
    } else {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current)
      }
      setShowLoadingDelay(false)
    }
    
    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current)
      }
    }
  }, [isLoading])

  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')

  // Define loadFileTree before using it
  const loadFileTree = useCallback(async (customPath?: string) => {
    try {
      // Get file tree for specified path or all watched directories
      const params = customPath ? { path: customPath } : {}
      const response = await axios.get(`${API_BASE_URL}/api/files/tree`, { params })
      let files = response.data
      
      if (!files || files.length === 0) {
        setFileTree([])
        return
      }
      
      // Ensure all root directories are expanded
      files.forEach((node: FileNode) => {
        if (node.type === 'directory') {
          node.isExpanded = true
        }
      })
      
      setFileTree(files)
    } catch (_error) {
      // Error loading file tree
      setFileTree([])
    }
  }, [])

  useEffect(() => {
    // Load initial file tree
    loadFileTree()
    
    // Keep track of current websocket instance
    let currentWebSocket: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout | null = null
    
    // Connect to WebSocket
    const connectWebSocket = () => {
      // Clean up any existing connection
      if (currentWebSocket?.readyState === WebSocket.OPEN || currentWebSocket?.readyState === WebSocket.CONNECTING) {
        currentWebSocket.close()
      }
      
      setConnectionStatus('connecting')
      // 动态获取 WebSocket URL，支持代理和远程访问
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname
      const port = window.location.port
      
      // 如果是通过代理访问，使用当前页面的 host
      let wsUrl = `${protocol}//${host}`
      if (port) {
        wsUrl += `:${port}`
      }
      wsUrl += '/ws'
      
      // Connecting to WebSocket
      const websocket = new WebSocket(wsUrl)
      currentWebSocket = websocket
      
      websocket.onopen = () => {
        // WebSocket connected
        setConnectionStatus('connected')
        setWs(websocket)
        
        // Send project ID if we have one (for registered users)
        if (projectId) {
          websocket.send(JSON.stringify({
            type: 'set_project_id',
            project_id: parseInt(projectId)
          }))
          setIsProjectIdSet(true)
        }
      }
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          // Received WebSocket message
          handleWebSocketMessage(data)
        } catch (_error) {
          // WebSocket message error
        }
      }
      
      websocket.onerror = (_error) => {
        // WebSocket error
        setConnectionStatus('disconnected')
      }
      
      websocket.onclose = () => {
        setConnectionStatus('disconnected')
        setWs(null)
        // Only reconnect if this is the current websocket
        if (websocket === currentWebSocket) {
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(connectWebSocket, 3000)
        }
      }
    }
    
    connectWebSocket()
    
    return () => {
      // Clean up on unmount
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      if (currentWebSocket) {
        currentWebSocket.close()
      }
    }
  }, [loadFileTree])

  const scrollToBottom = () => {
    // 使用setTimeout确保DOM更新后再滚动
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      // 备用方案：如果scrollIntoView不起作用，直接操作滚动容器
      const scrollContainer = messagesEndRef.current?.parentElement?.parentElement
      if (scrollContainer) {
        // 滚动到底部，但留出一点空间
        const targetScroll = scrollContainer.scrollHeight - scrollContainer.clientHeight
        scrollContainer.scrollTo({
          top: targetScroll,
          behavior: 'smooth'
        })
      }
    }, 100)
  }

  // Handle project ID confirmation
  const handleProjectIdConfirm = useCallback(() => {
    if (tempProjectId && tempProjectId !== projectId) {
      setProjectId(tempProjectId)
      setIsProjectIdSet(true)
      setProjectIdStatus('updating')
      // Send to server if connected
      if (ws && connectionStatus === 'connected') {
        ws.send(JSON.stringify({
          type: 'set_project_id',
          project_id: parseInt(tempProjectId)
        }))
        // Show success status after a short delay
        setTimeout(() => {
          setProjectIdStatus('success')
          // Reset to idle after showing success
          setTimeout(() => {
            setProjectIdStatus('idle')
          }, 2000)
        }, 500)
      }
    }
  }, [ws, connectionStatus, tempProjectId, projectId])

  // Session management functions
  const handleCreateSession = useCallback(async () => {
    if (ws && connectionStatus === 'connected' && !isCreatingSession) {
      setIsCreatingSession(true)
      // 清空当前消息
      setMessages([])
      ws.send(JSON.stringify({ type: 'create_session' }))
      // 设置超时，避免永久等待
      setTimeout(() => {
        setIsCreatingSession(false)
      }, 3000)
    }
  }, [ws, connectionStatus, isCreatingSession])

  const handleSelectSession = useCallback(async (sessionId: string) => {
    if (ws && connectionStatus === 'connected') {
      ws.send(JSON.stringify({ 
        type: 'switch_session',
        session_id: sessionId 
      }))
    }
  }, [ws, connectionStatus])

  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (ws && connectionStatus === 'connected') {
      ws.send(JSON.stringify({ 
        type: 'delete_session',
        session_id: sessionId 
      }))
    }
  }, [ws, connectionStatus])

  const handleSend = () => {
    if (!input.trim()) return
    if (!ws || connectionStatus !== 'connected') {
      alert('未连接到服务器，请稍后重试')
      return
    }

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, newMessage])
    setInput('')
    setIsLoading(true)
    
    // 发送消息后立即滚动到底部
    scrollToBottom()

    // Send message through WebSocket
    ws.send(JSON.stringify({
      type: 'message',
      content: input
    }))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleWebSocketMessage = useCallback((data: WSMessage) => {
    const { type, timestamp, id } = data
    
    // 如果消息有ID，检查是否已经处理过
    if (id && messageIdef.current.has(id)) {
      return
    }
    if (id) {
      messageIdef.current.add(id)
    }
    
    
    if (type === 'sessions_list' && 'sessions' in data && 'current_session_id' in data) {
      // 更新会话列表
      setSessions((data as any).sessions || [])
      setCurrentSessionId((data as any).current_session_id)
      setIsCreatingSession(false)
      return
    }
    
    if (type === 'session_messages' && 'messages' in data) {
      // 加载会话历史消息
      const messages = (data as any).messages || []
      setMessages(messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })))
      // 清除消息ID缓存，避免重复
      messageIdef.current.clear()
      messages.forEach((msg: any) => {
        if (msg.id) {
          messageIdef.current.add(msg.id)
        }
      })
      setIsCreatingSession(false)
      return
    }
    
    if (type === 'user') {
      // Skip echoed user messages
      return
    }
    
    if (type === 'tool' && 'tool_name' in data && 'status' in data) {
      // Tool execution status
      const { tool_name, status } = data
      const result = 'result' in data ? (data as any).result : undefined
      // 对于工具消息，我们传递原始结果，让 ToolResultDisplay 组件处理展示
      const content = result || ''
      
      // 使用基于工具名称和会话的唯一ID，这样同一工具的状态更新会替换而不是新增
      const toolId = `tool-${currentSessionId}-${tool_name}`
      
      const toolMessage: Message = {
        id: toolId,
        role: 'tool' as const,
        content,
        timestamp: new Date(timestamp || Date.now()),
        tool_name,
        tool_status: status
      }
      
      // 使用函数式更新，检查是否需要更新现有的工具消息
      setMessages(prev => {
        const existingIndex = prev.findIndex(m => m.id === toolId)
        if (existingIndex >= 0) {
          // 更新现有消息
          const updated = [...prev]
          updated[existingIndex] = toolMessage
          return updated
        } else {
          // 添加新消息
          return [...prev, toolMessage]
        }
      })
      // 工具消息后滚动到底部
      scrollToBottom()
      return
    }
    
    if (type === 'assistant' || type === 'response') {
      const assistantMessage: Message = {
        id: id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: 'content' in data ? (data as any).content || '' : '',
        timestamp: new Date(timestamp || Date.now())
      }
      
      // 使用函数式更新来避免消息重复
      setMessages(prev => {
        // 检查是否已经存在相同ID的消息
        if (prev.some(m => m.id === assistantMessage.id)) {
          return prev
        }
        return [...prev, assistantMessage]
      })
      // 收到新消息后滚动到底部
      scrollToBottom()
    }
    
    if (type === 'complete') {
      setIsLoading(false)
      // 加载完成后滚动到底部
      scrollToBottom()
    }
    
    if (type === 'error') {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `❌ 错误: ${'content' in data ? (data as any).content : '未知错误'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setIsLoading(false)
    }
    
    if (type === 'file_change') {
      // Handle file change notification
      // File change detected
      
      // Automatically refresh the file tree when files change
      loadFileTree()
    }
  }, [loadFileTree])

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Session List Sidebar */}
      <ResizablePanel
        direction="horizontal"
        minSize={200}
        maxSize={400}
        defaultSize={280}
        className="border-r border-gray-200 dark:border-gray-700"
      >
        <SessionList
          sessions={sessions}
          currentSessionId={currentSessionId}
          onCreateSession={handleCreateSession}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
        />
      </ResizablePanel>

      {/* Main Content Area */}
      <div className="flex-1 flex">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 aurora-bg">
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200/50 dark:border-gray-700/50 glass-premium glass-glossy flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {config?.ui?.title || 'Agent'}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            {showProjectIdInput && (
              <div className="flex items-center gap-2">
                <label htmlFor="projectId" className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  Project ID:
                </label>
                <input
                  id="projectId"
                  type="text"
                  value={tempProjectId || projectId}
                  onChange={(e) => setTempProjectId(e.target.value)}
                  placeholder="如果你需要在Bohrium上提交任务，请输入项目ID"
                  className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
                  disabled={isProjectIdSet && projectId === tempProjectId}
                />
                {tempProjectId && tempProjectId !== projectId && (
                  <button
                    onClick={handleProjectIdConfirm}
                    className="px-3 py-1.5 text-sm font-medium text-white bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors"
                  >
                    确认
                  </button>
                )}
                {projectIdStatus === 'updating' && (
                  <span className="text-sm text-blue-600 dark:text-blue-400">
                    正在更新...
                  </span>
                )}
                {projectIdStatus === 'success' && (
                  <span className="text-sm text-green-600 dark:text-green-400">
                    ✓ 更新成功
                  </span>
                )}
                {projectIdStatus === 'idle' && isProjectIdSet && projectId && (
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    已设置: {projectId}
                  </span>
                )}
              </div>
            )}
            <button
              onClick={() => setShowFileExplorer(!showFileExplorer)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors btn-animated"
            >
              <FileText className="w-4 h-4" />
              {showFileExplorer ? '隐藏文件' : '查看文件'}
            </button>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
              connectionStatus === 'connected' 
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
                : connectionStatus === 'connecting'
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' : 
                connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
                'bg-red-500'
              }`} />
              <span>
                {connectionStatus === 'connected' ? '已连接' : 
                 connectionStatus === 'connecting' ? '连接中...' : 
                 '未连接'}
              </span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 relative">
          <div className="max-w-4xl mx-auto space-y-6 h-full">
            {messages.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                  <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
                    欢迎使用 {config?.agent?.name || 'Agent'}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-500">
                    {config?.agent?.welcomeMessage || 'welcome to chat with me'}
                  </p>
                </div>
              </div>
            ) : (
              <AnimatePresence initial={false} mode="popLayout">
                {messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    layout="position"
                    initial={index === messages.length - 1 ? { opacity: 0, y: 20 } : false}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2 }}
                    className={`flex gap-4 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <MemoizedMessage
                      id={message.id}
                      role={message.role}
                      content={message.content}
                      timestamp={message.timestamp}
                      isLastMessage={index === messages.length - 1}
                      isStreaming={message.isStreaming}
                      tool_name={message.tool_name}
                      tool_status={message.tool_status}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
            
            {showLoadingDelay && (
              <MessageAnimation isNew={true} type="assistant">
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-4"
                >
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-2xl px-4 py-3 shadow-sm border border-gray-200 dark:border-gray-700">
                    <LoadingDots />
                  </div>
                </motion.div>
              </MessageAnimation>
            )}
            
            {/* 底部垫高，确保最后一条消息不贴底 */}
            <div className="h-24" />
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 glass-premium p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入消息..."
                className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-all input-animated glow"
                rows={1}
                style={{
                  minHeight: '48px',
                  maxHeight: '200px'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = `${target.scrollHeight}px`
                }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading || connectionStatus !== 'connected'}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2 btn-animated liquid-button"
              >
                <Send className="w-4 h-4" />
                发送
              </button>
            </div>
          </div>
        </div>
        </div>
        
        {/* File Explorer Sidebar */}
        {showFileExplorer && (
          <ResizablePanel
            direction="horizontal"
            minSize={400}
            maxSize={800}
            defaultSize={600}
            className="border-l border-gray-200 dark:border-gray-700"
            resizeBarPosition="start"
          >
            <FileExplorer
              isOpen={showFileExplorer}
              onClose={() => setShowFileExplorer(false)}
              fileTree={fileTree}
              onFileTreeUpdate={setFileTree}
              onLoadFileTree={loadFileTree}
            />
          </ResizablePanel>
        )}
      </div>
    </div>
  )
}

export default ChatInterface