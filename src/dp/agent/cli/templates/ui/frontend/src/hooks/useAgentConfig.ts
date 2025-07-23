import { useState, useEffect } from 'react'
import { AgentConfig } from '../types'
import { configService } from '../services/config'

export function useAgentConfig() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const loadedConfig = await configService.loadConfig()
        setConfig(loadedConfig)
        
        // Update document title
        if (loadedConfig.ui?.title) {
          document.title = loadedConfig.ui.title
        }
      } catch (err) {
        // console.error('Failed to load agent config:', err)
        setError('Failed to load configuration')
      } finally {
        setLoading(false)
      }
    }

    loadConfig()

    // Subscribe to config changes
    const unsubscribe = configService.onChange((newConfig) => {
      setConfig(newConfig)
      if (newConfig.ui?.title) {
        document.title = newConfig.ui.title
      }
    })
    
    return unsubscribe
  }, [])

  return { config, loading, error }
}