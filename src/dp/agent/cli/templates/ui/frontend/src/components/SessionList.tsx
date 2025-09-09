import React from 'react'
import { Plus, MessageSquare, Trash2, Clock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from '../hooks/useTranslation'

interface Session {
  id: string
  title: string
  created_at: string
  last_message_at: string
  message_count: number
}

interface SessionListProps {
  sessions: Session[]
  currentSessionId: string | null
  onCreateSession: () => void
  onSelectSession: (sessionId: string) => void
  onDeleteSession: (sessionId: string) => void
}

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  currentSessionId,
  onCreateSession,
  onSelectSession,
  onDeleteSession
}) => {
  const { t, language } = useTranslation()
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return t.session.justNow
    if (diffMins < 60) return `${diffMins} ${t.session.minutesAgo}`
    if (diffHours < 24) return `${diffHours} ${t.session.hoursAgo}`
    if (diffDays < 7) return `${diffDays} ${t.session.daysAgo}`
    
    return date.toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US')
  }

  return (
    <div className="h-full bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header with New Session Button */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={onCreateSession}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg font-medium transition-all duration-200 shadow-sm hover:shadow-md"
        >
          <Plus className="w-5 h-5" />
          <span>{t.actions.newSession}</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <MessageSquare className="w-12 h-12 mb-3 opacity-50" />
              <p className="text-sm">{t.session.noSessions}</p>
              <p className="text-xs mt-1">{t.session.clickToStart}</p>
            </div>
          ) : (
            sessions.map((session) => (
              <motion.div
                key={session.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className={`group relative hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${
                  currentSessionId === session.id ? 'bg-gray-100 dark:bg-gray-800' : ''
                }`}
              >
                <button
                  onClick={() => onSelectSession(session.id)}
                  className="w-full px-4 py-3 text-left"
                >
                  <div className="flex items-start gap-3">
                    <MessageSquare className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                      currentSessionId === session.id 
                        ? 'text-blue-600 dark:text-blue-400' 
                        : 'text-gray-400 dark:text-gray-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <h3 className={`text-sm font-medium truncate ${
                        currentSessionId === session.id
                          ? 'text-gray-900 dark:text-gray-100'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        {session.title === 'Untitled' ? t.session.untitled : session.title}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatDate(session.last_message_at)}
                        </span>
                        <span className="text-xs text-gray-400 dark:text-gray-500">
                          · {session.message_count} {t.session.messages}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>

                {/* Delete Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (confirm(t.session.deleteConfirm)) {
                      onDeleteSession(session.id)
                    }
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-all duration-200"
                >
                  <Trash2 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                </button>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

    </div>
  )
}

export default SessionList