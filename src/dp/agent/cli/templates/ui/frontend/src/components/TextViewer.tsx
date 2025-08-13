import React, { useState, useMemo } from 'react'
import { Copy, Check, Search, WrapText } from 'lucide-react'

interface TextViewerProps {
  content: string
  language?: string
}

const TextViewer: React.FC<TextViewerProps> = ({ content }) => {
  const [copiedText, setCopiedText] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [wordWrap, setWordWrap] = useState(true)
  const [showLineNumbers, setShowLineNumbers] = useState(true)

  const handleCopy = () => {
    navigator.clipboard.writeText(content).then(() => {
      setCopiedText(true)
      setTimeout(() => setCopiedText(false), 2000)
    })
  }

  const { lines, highlightedLines } = useMemo(() => {
    const allLines = content.split('\n')
    const highlighted = new Set<number>()
    
    if (searchTerm) {
      allLines.forEach((line, index) => {
        if (line.toLowerCase().includes(searchTerm.toLowerCase())) {
          highlighted.add(index)
        }
      })
    }
    
    return { lines: allLines, highlightedLines: highlighted }
  }, [content, searchTerm])

  const renderLine = (line: string, lineNumber: number) => {
    const isHighlighted = highlightedLines.has(lineNumber - 1)
    
    if (searchTerm && isHighlighted) {
      const regex = new RegExp(`(${searchTerm})`, 'gi')
      const parts = line.split(regex)
      
      return (
        <span>
          {parts.map((part, i) => 
            regex.test(part) ? (
              <mark key={i} className="bg-yellow-300 dark:bg-yellow-600 text-gray-900 dark:text-gray-100 px-0.5 rounded">
                {part}
              </mark>
            ) : (
              <span key={i}>{part}</span>
            )
          )}
        </span>
      )
    }
    
    return <span>{line || '\u00A0'}</span>
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      <div className="border-b border-gray-200 dark:border-gray-700 p-3">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索文本..."
              className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowLineNumbers(!showLineNumbers)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                showLineNumbers 
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}
            >
              行号
            </button>
            
            <button
              onClick={() => setWordWrap(!wordWrap)}
              className={`p-1.5 rounded-md transition-colors ${
                wordWrap 
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}
              title={wordWrap ? '关闭自动换行' : '开启自动换行'}
            >
              <WrapText className="w-4 h-4" />
            </button>
            
            <button
              onClick={handleCopy}
              className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
              title="复制全部内容"
            >
              {copiedText ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-gray-500" />
              )}
            </button>
          </div>
        </div>
        
        {searchTerm && (
          <div className="mt-2 text-xs text-gray-500">
            找到 {highlightedLines.size} 个匹配行
          </div>
        )}
      </div>
      
      <div className="flex-1 overflow-auto">
        <div className="font-mono text-sm">
          {lines.map((line, index) => {
            const lineNumber = index + 1
            const isHighlighted = highlightedLines.has(index)
            
            return (
              <div
                key={index}
                className={`flex hover:bg-gray-50 dark:hover:bg-gray-700 ${
                  isHighlighted ? 'bg-yellow-50 dark:bg-yellow-900/20' : ''
                }`}
              >
                {showLineNumbers && (
                  <div className="select-none px-3 py-1 text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 text-right min-w-[3rem]">
                    {lineNumber}
                  </div>
                )}
                <div
                  className={`flex-1 px-4 py-1 text-gray-700 dark:text-gray-300 ${
                    wordWrap ? 'whitespace-pre-wrap break-all' : 'whitespace-pre overflow-x-auto'
                  }`}
                >
                  {renderLine(line, lineNumber)}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default TextViewer