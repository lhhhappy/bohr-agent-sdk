import axios from 'axios'
import { API_CONFIG, WS_CONFIG } from '../constants/config'

const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API methods (only keeping the ones actually used)
export const api = {
  // Files
  async getFile(path: string): Promise<string> {
    const response = await apiClient.get(`${API_CONFIG.API_ENDPOINTS.FILES}/${path}`, {
      responseType: 'text',
    })
    return response.data
  },

  async getFileTree(path?: string): Promise<any> {
    const url = path 
      ? `${API_CONFIG.API_ENDPOINTS.FILE_TREE}?path=${path}`
      : API_CONFIG.API_ENDPOINTS.FILE_TREE
    const response = await apiClient.get(url)
    return response.data
  },

  async getConfig(): Promise<any> {
    const response = await apiClient.get(API_CONFIG.API_ENDPOINTS.CONFIG)
    return response.data
  },

  async getASEByFileReq(params: { fileContent: string; format: string }) {
    const response = await apiClient.post('/api/materials_db/public/v1/material_visualization/info_by_str', params)
    return response.data
  }
}

// WebSocket connection
export class WSClient {
  private ws: WebSocket | null = null
  private reconnectTimeout: NodeJS.Timeout | null = null
  private listeners: Map<string, Set<Function>> = new Map()

  connect() {
    // Dynamic WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = window.location.port
    
    let wsUrl = `${protocol}//${host}`
    if (port) {
      wsUrl += `:${port}`
    }
    wsUrl += API_CONFIG.WS_ENDPOINT
    
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      // console.log('WebSocket connected')
      this.emit('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit(data.type, data)
      } catch (error) {
        // console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      // console.log('WebSocket disconnected')
      this.emit('disconnected')
      this.reconnect()
    }

    this.ws.onerror = (error) => {
      // console.error('WebSocket error:', error)
      this.emit('error', error)
    }
  }

  private reconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }

    this.reconnectTimeout = setTimeout(() => {
      // console.log('Attempting to reconnect WebSocket...')
      this.connect()
    }, WS_CONFIG.RECONNECT_DELAY)
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      // console.warn('WebSocket is not connected')
    }
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.delete(callback)
    }
  }

  private emit(event: string, data?: any) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach(callback => callback(data))
    }
  }
}

export const wsClient = new WSClient()