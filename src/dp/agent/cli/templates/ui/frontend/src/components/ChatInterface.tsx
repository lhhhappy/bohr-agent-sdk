import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, FileText, Paperclip, X, Globe } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import SessionList from './SessionList'
import FileExplorer from './FileExplorer'
import { ResizablePanel } from './ResizablePanel'
import { useAgentConfig } from '../hooks/useAgentConfig'
import { MessageAnimation, LoadingDots } from './MessageAnimation'
import { MemoizedMessage } from './MemoizedMessage'
import { useTranslation } from '../hooks/useTranslation'
import axios from 'axios'
import { Message, Session, FileNode, WSMessage, FileAttachment } from '../types'

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
  const [showFileExplorer, setShowFileExplorer] = useState(false) 
  const [projectId, setProjectId] = useState<string>('')
  const [tempProjectId, setTempProjectId] = useState<string>('')
  const [showProjectIdInput, setShowProjectIdInput] = useState(true)
  const [isProjectIdSet, setIsProjectIdSet] = useState(false)
  const [projectIdStatus, setProjectIdStatus] = useState<'idle' | 'updating' | 'success'>('idle')
  const [requireProjectId, setRequireProjectId] = useState(false)
  const [projects, setProjects] = useState<Array<{id: number, name: string}>>([])
  const [loadingProjects, setLoadingProjects] = useState(false)
  const [projectsError, setProjectsError] = useState<string>('')
  const [attachments, setAttachments] = useState<FileAttachment[]>([])
  const [uploading, setUploading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messageIdef = useRef<Set<string>>(new Set())
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isInitialLoad = useRef<boolean>(true)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  
  // Load agent configuration
  const { config } = useAgentConfig()
  
  // Internationalization
  const { t, language, setLanguage } = useTranslation()
  
  // Load projects when component mounts or when connection status changes
  useEffect(() => {
    if (connectionStatus === 'connected' && !projects.length && !loadingProjects) {
      loadProjects()
    }
  }, [connectionStatus])
  
  const loadProjects = async () => {
    setLoadingProjects(true)
    setProjectsError('')
    try {
      const response = await axios.get(`${API_BASE_URL}/api/projects`)
      if (response.data.success && response.data.projects) {
        setProjects(response.data.projects)
      } else {
        setProjectsError(response.data.error || t.errors.getProjectListFailed)
      }
    } catch (error) {
      console.error('Failed to load projects:', error)
      setProjectsError(t.errors.cannotConnectToServer)
    } finally {
      setLoadingProjects(false)
    }
  }

  // Show/hide project ID input based on user type
  useEffect(() => {
    console.log('Config:', config)
    console.log('User type:', config?.user_type)
    // Always show project ID input for all users
    setShowProjectIdInput(true)
  }, [config])

  useEffect(() => {
    // 只有当有消息且不是初始加载时才滚动
    if (messages.length > 0 && !isInitialLoad.current) {
      scrollToBottom()
    }
    // 标记初始加载已完成
    if (isInitialLoad.current) {
      isInitialLoad.current = false
    }
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

  const handleFileUpload = async (files: FileList) => {
    setUploading(true)
    const formData = new FormData()
    
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        withCredentials: true
      })
      
      if (response.data.success) {
        setAttachments(prev => [...prev, ...response.data.files])
      }
    } catch (error: any) {
      console.error('Upload failed:', error)
      alert(error.response?.data?.error || t.errors.fileUploadFailed)
    } finally {
      setUploading(false)
    }
  }

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const handleSend = () => {
    if (!input.trim() && attachments.length === 0) return
    if (!ws || connectionStatus !== 'connected') {
      alert(t.errors.serverDisconnected)
      return
    }

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      attachments: attachments.length > 0 ? attachments : undefined
    }

    setMessages(prev => [...prev, newMessage])
    setInput('')
    setIsLoading(true)
    
    // 发送消息后立即滚动到底部
    scrollToBottom()

    // Send message through WebSocket with attachments
    const messageData: any = {
      type: 'message',
      content: input
    }
    
    if (attachments.length > 0) {
      messageData.attachments = attachments
    }
    
    ws.send(JSON.stringify(messageData))
    
    // Clear attachments after sending
    setAttachments([])
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
      console.log('Loading session messages:', messages)
      const processedMessages = messages.map((msg: any) => {
        // 确定消息角色：优先使用 role 字段，如果没有则使用 type 字段
        let role = msg.role || msg.type
        
        // 确保 tool 类型的消息正确标记
        if (msg.type === 'tool') {
          role = 'tool'
        }
        
        const processed = {
          id: msg.id,
          role: role,
          content: msg.content || '',
          timestamp: new Date(msg.timestamp),
          // 保留工具相关字段
          tool_name: msg.tool_name,
          tool_status: msg.tool_status
        }
        console.log('Processed message:', processed)
        return processed
      })
      setMessages(processedMessages)
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
      const args = 'args' in data ? (data as any).args : undefined  // 获取工具调用参数
      const content = result || ''
      
      console.log('收到工具消息:', { tool_name, status, hasResult: !!result, hasArgs: !!args })
      
      const toolId = `tool-${currentSessionId}-${tool_name}`
      
      const toolMessage: Message = {
        id: toolId,
        role: 'tool' as const,
        content,
        timestamp: new Date(timestamp || Date.now()),
        tool_name,
        tool_status: status,
        tool_args: args  // 保存工具调用参数
      }
      
      setMessages(prev => {
        const existingIndex = prev.findIndex(m => m.id === toolId)
        if (existingIndex >= 0) {
          // 更新现有消息，保留之前的 tool_args
          const updated = [...prev]
          updated[existingIndex] = {
            ...updated[existingIndex],
            ...toolMessage,
            // 保留之前的 tool_args（如果新消息没有 args）
            tool_args: args || updated[existingIndex].tool_args
          }
          return updated
        } else {
          // 添加新消息
          return [...prev, toolMessage]
        }
      })
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
        content: `❌ ${t.errors.general}: ${'content' in data ? (data as any).content : t.errors.unknownError}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setIsLoading(false)
    }
    
    if (type === 'require_project_id') {
      setRequireProjectId(true)
    }
    
    if (type === 'project_id_set' && 'project_id' in data) {
      setProjectId((data as any).project_id.toString())
      setTempProjectId((data as any).project_id.toString())
      setIsProjectIdSet(true)
      setRequireProjectId(false)
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
                {loadingProjects ? (
                  <div className="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400">
                    正在获取项目列表...
                  </div>
                ) : projects.length > 0 ? (
                  <select
                    id="projectId"
                    value={tempProjectId || projectId}
                    onChange={(e) => {
                      setTempProjectId(e.target.value)
                    }}
                    className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 w-64 appearance-none cursor-pointer"
                    style={{ 
                      backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 0.7rem center',
                      backgroundSize: '1.2em 1.2em',
                      paddingRight: '2.5rem'
                    }}
                  >
                    <option value="">{t.placeholders.selectProject}</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id.toString()}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="flex items-center gap-2">
                    <select
                      id="projectId"
                      disabled
                      className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 w-64 cursor-not-allowed"
                    >
                      <option value="">{projectsError || "无法获取项目列表"}</option>
                    </select>
                    {projectsError && (
                      <button
                        onClick={loadProjects}
                        className="px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                      >
                        重试
                      </button>
                    )}
                  </div>
                )}
                {tempProjectId && tempProjectId !== projectId && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleProjectIdConfirm}
                    className="px-4 py-1.5 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
                  >
                    <span className="flex items-center gap-1">
                      确认
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </span>
                  </motion.button>
                )}
                <AnimatePresence mode="wait">
                  {projectIdStatus === 'updating' && (
                    <motion.span
                      key="updating"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      className="text-sm text-blue-600 dark:text-blue-400 flex items-center gap-2"
                    >
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-4 h-4"
                      >
                        <svg className="w-full h-full" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      </motion.div>
                      正在更新...
                    </motion.span>
                  )}
                  {projectIdStatus === 'success' && (
                    <motion.span
                      key="success"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1"
                    >
                      <motion.svg
                        initial={{ scale: 0, rotate: -180 }}
                        animate={{ scale: 1, rotate: 0 }}
                        transition={{ type: "spring", stiffness: 200, damping: 15 }}
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </motion.svg>
                      更新成功
                    </motion.span>
                  )}
                  {projectIdStatus === 'idle' && isProjectIdSet && projectId && (
                    <motion.div
                      key="set"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <span className="text-sm text-gray-500 dark:text-gray-400">{t.project.alreadySet}</span>
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                        {projects.find(p => p.id.toString() === projectId)?.name || projectId}
                      </span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}
            <button
              onClick={() => setShowFileExplorer(!showFileExplorer)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors btn-animated"
            >
              <FileText className="w-4 h-4" />
              {showFileExplorer ? t.actions.hideFiles : t.actions.showFiles}
            </button>
            <button
              onClick={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors btn-animated"
              title={language === 'zh' ? 'Switch to English' : '切换到中文'}
            >
              <Globe className="w-4 h-4" />
              <span>{language === 'zh' ? 'EN' : 'CN'}</span>
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
                {connectionStatus === 'connected' ? t.connection.connected : 
                 connectionStatus === 'connecting' ? t.connection.connecting : 
                 t.connection.disconnected}
              </span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 relative">
          {/* Project ID 提示横幅 */}
          {requireProjectId && !isProjectIdSet && (
            <div className="max-w-4xl mx-auto mb-4">
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      {t.project.needToSelect}
                    </h3>
                    <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                      <p>{t.project.selectFromDropdown}</p>
                      <p className="mt-1 text-xs">{t.project.checkAccessKey}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
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
                      tool_args={message.tool_args}
                      attachments={message.attachments}
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
            {/* Attachments Preview */}
            {attachments.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {attachments.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-lg">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{file.name}</span>
                    <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                    <button
                      onClick={() => removeAttachment(idx)}
                      className="ml-1 text-gray-500 hover:text-red-500 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <div className="flex gap-3">
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                style={{ display: 'none' }}
              />
              
              {/* File upload button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || connectionStatus !== 'connected'}
                className="p-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors disabled:opacity-50"
                title={t.actions.uploadFile}
              >
                <Paperclip className="w-5 h-5" />
              </button>
              
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t.placeholders.messageInput}
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
                disabled={(!input.trim() && attachments.length === 0) || isLoading || connectionStatus !== 'connected' || (requireProjectId && !isProjectIdSet)}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2 btn-animated liquid-button"
                title={requireProjectId && !isProjectIdSet ? t.project.pleaseSelectFirst : ''}
              >
                <Send className="w-4 h-4" />
                {t.actions.send}
              </button>
            </div>
          </div>
        </div>
        </div>
        
        {/* File Explorer Sidebar */}
        {showFileExplorer && (
          <ResizablePanel
            direction="horizontal"
            minSize={600}
            maxSize={1200}
            defaultSize={800}
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