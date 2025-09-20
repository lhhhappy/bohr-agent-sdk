/**
 * Timing constants used throughout the application
 */

export const DELAYS = {
  // Loading and animations
  LOADING_ANIMATION_DELAY: 200, // Delay before showing loading animation
  
  // Scrolling
  SCROLL_TO_BOTTOM_DELAY: 100, // Delay before scrolling to bottom
  SCROLL_TO_BOTTOM_FALLBACK_DELAY: 100, // Fallback scroll delay
  
  // Session operations
  SESSION_CREATE_TIMEOUT: 3000, // Timeout for session creation
  
  // WebSocket
  WEBSOCKET_RECONNECT_DELAY: 3000, // Base reconnect delay
  WEBSOCKET_MAX_RECONNECT_DELAY: 30000, // Maximum reconnect delay
  
  // UI updates
  MESSAGE_UPDATE_DELAY: 50, // Delay for message updates
} as const

export const SIZES = {
  // Layout
  FILE_TREE_WIDTH: 280, // Fixed width for file explorer tree
  FILE_TREE_MIN_WIDTH: 200,
  FILE_TREE_MAX_WIDTH: 400,
  
  // Messages
  MAX_MESSAGE_LENGTH: 10000,
  
  // WebSocket
  MAX_RECONNECT_ATTEMPTS: 10,
} as const