/**
 * 统一的端口配置常量
 * 避免在代码中硬编码端口号
 */

export const PORTS = {
  // 默认的 WebSocket 服务器端口
  DEFAULT_WEBSOCKET_PORT: 8000,
  
  // 默认的前端开发服务器端口
  DEFAULT_FRONTEND_DEV_PORT: 3000,
  
  // 默认的服务器端口（生产环境）
  DEFAULT_SERVER_PORT: 50002,
} as const

// 获取环境变量中的端口配置
export const getWebSocketPort = (): number => {
  return parseInt(process.env.VITE_WS_PORT || String(PORTS.DEFAULT_WEBSOCKET_PORT))
}

export const getFrontendPort = (): number => {
  return parseInt(process.env.FRONTEND_PORT || String(PORTS.DEFAULT_FRONTEND_DEV_PORT))
}

// 默认允许的主机列表
export const DEFAULT_ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0'] as const