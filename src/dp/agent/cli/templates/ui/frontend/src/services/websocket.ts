import { WS_CONFIG } from '../constants/config'
import { WSMessage, ConnectionStatus } from '../types'

type MessageHandler<T = WSMessage> = (data: T) => void
type EventHandler = () => void

interface QueuedMessage {
  type: string
  data: unknown
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimeout: NodeJS.Timeout | null = null
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map()
  private eventHandlers: Map<string, Set<EventHandler>> = new Map()
  private connectionStatus: ConnectionStatus = 'disconnected'
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private messageQueue: QueuedMessage[] = []

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      return
    }

    this.setConnectionStatus('connecting')
    
    // Dynamic WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = window.location.port
    
    let wsUrl = `${protocol}//${host}`
    if (port) {
      wsUrl += `:${port}`
    }
    wsUrl += '/ws'
    
    // Connecting to WebSocket
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      // WebSocket connected
      this.setConnectionStatus('connected')
      this.reconnectAttempts = 0
      this.flushMessageQueue()
      this.emit('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSMessage
        this.handleMessage(data)
      } catch (error) {
        // Failed to parse WebSocket message
      }
    }

    this.ws.onclose = () => {
      // WebSocket disconnected
      this.setConnectionStatus('disconnected')
      this.emit('disconnected')
      this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      // WebSocket error occurred
      this.emit('error')
    }
  }

  private setConnectionStatus(status: ConnectionStatus) {
    this.connectionStatus = status
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      // Max reconnection attempts reached
      return
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }

    const delay = Math.min(WS_CONFIG.RECONNECT_DELAY * Math.pow(1.5, this.reconnectAttempts), 30000)
    this.reconnectAttempts++
    
    this.reconnectTimeout = setTimeout(() => {
      // Attempting reconnection
      this.connect()
    }, delay)
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.messageQueue = []
    this.reconnectAttempts = 0
  }

  send(data: QueuedMessage | Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      // Queue message for later delivery
      this.messageQueue.push(data as QueuedMessage)
      // WebSocket not connected, message queued
    }
  }

  private flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()
      if (message) {
        this.send(message)
      }
    }
  }

  private handleMessage(message: WSMessage) {
    const { type } = message
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.forEach(handler => handler(message))
    }
  }

  onMessage(type: string, handler: MessageHandler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set())
    }
    this.messageHandlers.get(type)!.add(handler)
  }

  offMessage(type: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  on(event: string, handler: EventHandler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set())
    }
    this.eventHandlers.get(event)!.add(handler)
  }

  off(event: string, handler: EventHandler) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  private emit(event: string) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.forEach(handler => handler())
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus
  }
}

// Singleton instance
export const websocketService = new WebSocketService()