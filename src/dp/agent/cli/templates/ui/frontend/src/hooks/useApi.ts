import { useState, useEffect } from 'react'
import { api, wsClient } from '../api/client'

export function useFile(path: string) {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!path) {
      setLoading(false)
      return
    }

    const fetchFile = async () => {
      try {
        setLoading(true)
        const data = await api.getFile(path)
        setContent(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load file')
        setContent('')
      } finally {
        setLoading(false)
      }
    }

    fetchFile()

    // Listen for file changes
    const handleFileChanged = (data: any) => {
      if (data.path && data.path.includes(path)) {
        fetchFile()
      }
    }

    wsClient.on('file_changed', handleFileChanged)

    return () => {
      wsClient.off('file_changed', handleFileChanged)
    }
  }, [path])

  return { content, loading, error }
}

export function useWebSocket() {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    wsClient.connect()

    const handleConnected = () => setConnected(true)
    const handleDisconnected = () => setConnected(false)

    wsClient.on('connected', handleConnected)
    wsClient.on('disconnected', handleDisconnected)

    return () => {
      wsClient.off('connected', handleConnected)
      wsClient.off('disconnected', handleDisconnected)
      wsClient.disconnect()
    }
  }, [])

  return { connected }
}