import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import Card from '../components/Card'
import Button from '../components/Button'
import Badge from '../components/Badge'
import { 
  FileText, 
  ChevronLeft, 
  Download, 
  Copy, 
  Check,
  FileJson,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { motion } from 'framer-motion'

const FileViewer: React.FC = () => {
  const { '*': filePath } = useParams()
  const navigate = useNavigate()
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [fileType, setFileType] = useState<'markdown' | 'json' | 'text'>('text')

  useEffect(() => {
    if (filePath) {
      loadFile(filePath)
    }
  }, [filePath])

  const loadFile = async (path: string) => {
    setLoading(true)
    setError(null)

    try {
      // Determine file type
      if (path.endsWith('.md')) {
        setFileType('markdown')
      } else if (path.endsWith('.json')) {
        setFileType('json')
      } else {
        setFileType('text')
      }

      // Simulated file loading - replace with actual API call
      const response = await fetch(`/api/files/${path}`)
      if (!response.ok) {
        throw new Error('File not found')
      }
      const text = await response.text()
      setContent(text)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filePath?.split('/').pop() || 'file.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-apple-gray-400 animate-spin" />
        </div>
      )
    }

    if (error && !content) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-apple-gray-500">
          <AlertCircle className="w-12 h-12 mb-3" />
          <p className="text-lg font-medium">无法加载文件</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )
    }

    switch (fileType) {
      case 'markdown':
        return (
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                },
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )

      case 'json':
        try {
          const jsonData = JSON.parse(content)
          return (
            <SyntaxHighlighter
              language="json"
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                borderRadius: '0.5rem',
              }}
            >
              {JSON.stringify(jsonData, null, 2)}
            </SyntaxHighlighter>
          )
        } catch {
          return <pre className="code-block">{content}</pre>
        }

      default:
        return <pre className="code-block">{content}</pre>
    }
  }

  const getFileIcon = () => {
    switch (fileType) {
      case 'markdown':
        return <FileText className="w-5 h-5" />
      case 'json':
        return <FileJson className="w-5 h-5" />
      default:
        return <FileText className="w-5 h-5" />
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="glass border-b border-apple-gray-200/50 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              icon={<ChevronLeft className="w-4 h-4" />}
              onClick={() => navigate(-1)}
            >
              返回
            </Button>
            <div className="flex items-center gap-2">
              {getFileIcon()}
              <h2 className="text-lg font-medium text-apple-gray-900">
                {filePath?.split('/').pop() || 'File'}
              </h2>
              <Badge variant="info" className="ml-2">
                {fileType.toUpperCase()}
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              icon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              onClick={handleCopy}
            >
              {copied ? '已复制' : '复制'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Download className="w-4 h-4" />}
              onClick={handleDownload}
            >
              下载
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="min-h-[calc(100vh-200px)]">
            {renderContent()}
          </Card>
        </motion.div>
      </div>
    </div>
  )
}

export default FileViewer