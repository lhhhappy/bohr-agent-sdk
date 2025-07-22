import { AgentConfig } from '../types'
import { api } from '../api/client'
import { DEFAULT_MESSAGES } from '../constants/config'

class ConfigService {
  private config: AgentConfig | null = null
  private loading = false
  private listeners: Set<(config: AgentConfig) => void> = new Set()

  async loadConfig(): Promise<AgentConfig> {
    if (this.config) {
      return this.config
    }

    if (this.loading) {
      // Wait for ongoing load to complete
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!this.loading && this.config) {
            clearInterval(checkInterval)
            resolve(this.config)
          }
        }, 100)
      })
    }

    this.loading = true
    try {
      const data = await api.getConfig()
      this.config = this.mergeWithDefaults(data)
      this.notifyListeners()
      return this.config
    } catch (error) {
      console.error('Failed to load config:', error)
      // Return default config on error
      this.config = this.getDefaultConfig()
      return this.config
    } finally {
      this.loading = false
    }
  }

  private mergeWithDefaults(config: Partial<AgentConfig>): AgentConfig {
    const defaults = this.getDefaultConfig()
    return {
      agent: { ...defaults.agent, ...config.agent },
      ui: { ...defaults.ui, ...config.ui },
      files: { ...defaults.files, ...config.files },
      server: { ...defaults.server, ...config.server },
    }
  }

  private getDefaultConfig(): AgentConfig {
    return {
      agent: {
        name: 'Agent',
        description: 'AI Assistant',
        welcomeMessage: DEFAULT_MESSAGES.WELCOME_MESSAGE,
        module: 'agent',
        rootAgent: 'root_agent',
      },
      ui: {
        title: 'Agent Assistant',
        theme: 'light',
        features: {
          showFileExplorer: true,
          showSessionList: true,
        },
      },
      files: {
        watchDirectories: ['./output'],
      },
      server: {
        port: 8000,
        host: ['localhost', '127.0.0.1'],
      },
    }
  }

  getConfig(): AgentConfig | null {
    return this.config
  }

  onChange(listener: (config: AgentConfig) => void) {
    this.listeners.add(listener)
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notifyListeners() {
    if (this.config) {
      this.listeners.forEach(listener => listener(this.config!))
    }
  }
}

export const configService = new ConfigService()