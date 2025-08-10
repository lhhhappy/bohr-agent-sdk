import React, { useState, useMemo } from 'react'
import { Eye, Code, Maximize2, Minimize2 } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface HTMLViewerProps {
  content: string
  fileName?: string
}

const HTMLViewer: React.FC<HTMLViewerProps> = ({ content, fileName }) => {
  const [viewMode, setViewMode] = useState<'preview' | 'source'>('preview')
  const [isFullScreen, setIsFullScreen] = useState(false)
  
  // 基本的安全清理
  const sanitizedHTML = useMemo(() => {
    // 移除脚本标签
    let cleanHTML = content
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<script[^>]*\/>/gi, '')
      .replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '')
    
    return cleanHTML
  }, [content])

  return (
    <div className={`flex flex-col bg-white dark:bg-gray-800 ${isFullScreen ? 'fixed inset-0 z-50' : 'h-full'}`}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center gap-3">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {fileName || 'HTML 文件'}
          </h4>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 视图模式切换 */}
          <div className="flex items-center bg-gray-200 dark:bg-gray-700 rounded-md p-1">
            <button
              onClick={() => setViewMode('preview')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                viewMode === 'preview'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              <Eye className="w-3 h-3 inline mr-1" />
              预览
            </button>
            <button
              onClick={() => setViewMode('source')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                viewMode === 'source'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              <Code className="w-3 h-3 inline mr-1" />
              源码
            </button>
          </div>

          {/* 全屏切换 */}
          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
            title={isFullScreen ? '退出全屏' : '全屏预览'}
          >
            {isFullScreen ? (
              <Minimize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'preview' ? (
          <div className="h-full">
            <iframe
              srcDoc={sanitizedHTML}
              className="w-full h-full border-none"
              sandbox="allow-same-origin"
              style={{
                backgroundColor: 'white',
                minHeight: '100%'
              }}
            />
          </div>
        ) : (
          <div className="p-4">
            <SyntaxHighlighter
              language="html"
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                lineHeight: '1.5'
              }}
              showLineNumbers
              wrapLines={true}
              wrapLongLines={true}
            >
              {content}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    </div>
  )
}

export default HTMLViewer