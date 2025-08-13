import React, { useState } from 'react'
import { ChevronRight, Copy, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface JsonTreeViewProps {
  data: any
  name?: string
}

const JsonTreeView: React.FC<JsonTreeViewProps> = ({ data, name = 'root' }) => {
  const [expanded, setExpanded] = useState<{ [key: string]: boolean }>({})
  const [copiedValue, setCopiedValue] = useState<string | null>(null)

  const toggleExpand = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const handleCopy = (value: any) => {
    const textToCopy = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
    navigator.clipboard.writeText(textToCopy).then(() => {
      setCopiedValue(textToCopy)
      setTimeout(() => setCopiedValue(null), 2000)
    })
  }

  const getValueColor = (value: any) => {
    if (value === null) return 'text-gray-500'
    if (typeof value === 'boolean') return value ? 'text-green-600' : 'text-red-600'
    if (typeof value === 'number') return 'text-blue-600'
    if (typeof value === 'string') return 'text-orange-600'
    return 'text-gray-700'
  }

  const renderValue = (value: any, key: string, fullPath: string) => {
    if (value === null) {
      return <span className="text-gray-500 italic">null</span>
    }

    if (typeof value === 'object' && !Array.isArray(value)) {
      const isExpanded = expanded[fullPath] !== false
      const keys = Object.keys(value)
      
      return (
        <div>
          <div className="flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded px-1 py-0.5 cursor-pointer group"
               onClick={() => toggleExpand(fullPath)}>
            <motion.div
              animate={{ rotate: isExpanded ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight className="w-3 h-3 text-gray-500" />
            </motion.div>
            <span className="font-medium text-purple-700 dark:text-purple-400">{key}</span>
            <span className="text-gray-500">:</span>
            <span className="text-gray-400 text-xs ml-1">
              {'{' + keys.length + ' keys}'}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); handleCopy(value) }}
              className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
            >
              {copiedValue === JSON.stringify(value, null, 2) ? 
                <Check className="w-3 h-3 text-green-500" /> : 
                <Copy className="w-3 h-3 text-gray-400" />
              }
            </button>
          </div>
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="ml-4 overflow-hidden"
              >
                {keys.map(k => (
                  <div key={k} className="border-l-2 border-gray-200 dark:border-gray-600 pl-2 ml-1">
                    {renderValue(value[k], k, `${fullPath}.${k}`)}
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )
    }

    if (Array.isArray(value)) {
      const isExpanded = expanded[fullPath] !== false
      
      return (
        <div>
          <div className="flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded px-1 py-0.5 cursor-pointer group"
               onClick={() => toggleExpand(fullPath)}>
            <motion.div
              animate={{ rotate: isExpanded ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight className="w-3 h-3 text-gray-500" />
            </motion.div>
            <span className="font-medium text-purple-700 dark:text-purple-400">{key}</span>
            <span className="text-gray-500">:</span>
            <span className="text-gray-400 text-xs ml-1">
              {'[' + value.length + ' items]'}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); handleCopy(value) }}
              className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
            >
              {copiedValue === JSON.stringify(value, null, 2) ? 
                <Check className="w-3 h-3 text-green-500" /> : 
                <Copy className="w-3 h-3 text-gray-400" />
              }
            </button>
          </div>
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="ml-4 overflow-hidden"
              >
                {value.map((item, index) => (
                  <div key={index} className="border-l-2 border-gray-200 dark:border-gray-600 pl-2 ml-1">
                    {renderValue(item, `[${index}]`, `${fullPath}[${index}]`)}
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )
    }

    return (
      <div className="flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded px-1 py-0.5 group">
        <span className="font-medium text-gray-700 dark:text-gray-300">{key}</span>
        <span className="text-gray-500">:</span>
        <span className={getValueColor(value)}>
          {typeof value === 'string' ? `"${value}"` : String(value)}
        </span>
        <button
          onClick={() => handleCopy(value)}
          className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
        >
          {copiedValue === String(value) ? 
            <Check className="w-3 h-3 text-green-500" /> : 
            <Copy className="w-3 h-3 text-gray-400" />
          }
        </button>
      </div>
    )
  }

  return (
    <div className="font-mono text-sm bg-white dark:bg-gray-800 rounded-lg p-4">
      {renderValue(data, name, name)}
    </div>
  )
}

export default JsonTreeView