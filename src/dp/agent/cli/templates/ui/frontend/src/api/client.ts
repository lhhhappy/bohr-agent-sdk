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