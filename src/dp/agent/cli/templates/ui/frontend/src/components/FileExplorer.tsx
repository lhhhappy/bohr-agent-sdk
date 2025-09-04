import React, { useState, useCallback } from 'react'
import { ChevronRight, File, Folder, FileText, Loader2, X, Copy, Check, Maximize2, Minimize2, Image, Atom, FolderOpen, Globe, Download, FolderDown, Trash2 } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import HTMLViewer from './HTMLViewer'
import MoleculeViewer from './MoleculeViewer'
import JsonTreeView from './JsonTreeView'
import CsvTableView from './CsvTableView'
import TextViewer from './TextViewer'

const API_BASE_URL = ''

interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
  isExpanded?: boolean
  size?: number
  modified?: string
}

interface FileExplorerProps {
  isOpen: boolean
  onClose: () => void
  fileTree: FileNode[]
  onFileTreeUpdate: (tree: FileNode[]) => void
  onLoadFileTree: (path?: string) => void
}

const FileExplorer: React.FC<FileExplorerProps> = ({
  onClose,
  fileTree,
  onFileTreeUpdate,
  onLoadFileTree
}) => {
  const [customPath, setCustomPath] = useState<string>('')
  const [isEditingPath, setIsEditingPath] = useState(false)
  const [selectedFileContent, setSelectedFileContent] = useState<string | null>(null)
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null)
  const [loadingFiles, setLoadingFiles] = useState<Set<string>>(new Set())
  const [fileContentCache, setFileContentCache] = useState<Map<string, string | { type: 'image' | 'molecule' | 'html'; url?: string; content?: string }>>(new Map())
  const [isFileContentExpanded, setIsFileContentExpanded] = useState(false)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  // 文件树宽度固定，不再需要调整
  const fileTreeWidth = 280 // 固定宽度

  const toggleDirectory = useCallback(async (path: string) => {
    onFileTreeUpdate(fileTree.map(node => {
      const toggleNode = (n: FileNode): FileNode => {
        if (n.path === path) {
          return { ...n, isExpanded: !n.isExpanded }
        }
        if (n.children) {
          return { ...n, children: n.children.map(toggleNode) }
        }
        return n
      }
      return toggleNode(node)
    }))

    const findNode = (nodes: FileNode[], targetPath: string): FileNode | null => {
      for (const node of nodes) {
        if (node.path === targetPath) return node
        if (node.children) {
          const found = findNode(node.children, targetPath)
          if (found) return found
        }
      }
      return null
    }

    const node = findNode(fileTree, path)
    if (node && node.type === 'directory' && !node.children) {
      await loadDirectoryChildren(path)
    }
  }, [fileTree, onFileTreeUpdate])

  const loadDirectoryChildren = async (dirPath: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/files/tree`, {
        params: { path: dirPath }
      })
      
      const children = response.data
      
      onFileTreeUpdate(fileTree.map(node => {
        const updateWithChildren = (n: FileNode): FileNode => {
          if (n.path === dirPath) {
            return { ...n, children }
          }
          if (n.children) {
            return { ...n, children: n.children.map(updateWithChildren) }
          }
          return n
        }
        return updateWithChildren(node)
      }))
    } catch (error) {
      // Error loading directory children
    }
  }

  const selectFile = useCallback(async (path: string, node: FileNode) => {
    if (node.type === 'file') {
      setSelectedFilePath(path)
      
      if (fileContentCache.has(path)) {
        const cached = fileContentCache.get(path)!
        if (typeof cached === 'string') {
          setSelectedFileContent(cached)
        } else {
          setSelectedFileContent(null) // For special file types
        }
        return
      }
      
      if (loadingFiles.has(path)) return
      
      setLoadingFiles(prev => new Set(prev).add(path))
      
      try {
        const ext = path.split('.').pop()?.toLowerCase()
        const isImage = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext || '')
        const isMolecule = ext === 'xyz'
        const isHTML = ext === 'html' || ext === 'htm'
        
        if (isImage) {
          // For images, we'll use the file URL directly
          const imageUrl = `${API_BASE_URL}/api/files/${path}`
          setFileContentCache(prev => new Map(prev).set(path, { type: 'image', url: imageUrl }))
          setSelectedFileContent(null)
        } else if (isMolecule) {
          // For molecules, we need to fetch the content
          const response = await axios.get(`${API_BASE_URL}/api/files/${path}`, {
            responseType: 'text'
          })
          setFileContentCache(prev => new Map(prev).set(path, { type: 'molecule', content: response.data }))
          setSelectedFileContent(null)
        } else if (isHTML) {
          // For HTML files, fetch the content for safe rendering
          const response = await axios.get(`${API_BASE_URL}/api/files/${path}`, {
            responseType: 'text'
          })
          setFileContentCache(prev => new Map(prev).set(path, { type: 'html', content: response.data }))
          setSelectedFileContent(null)
        } else {
          // For other files, fetch as text
          const response = await axios.get(`${API_BASE_URL}/api/files/${path}`, {
            responseType: 'text'
          })
          setFileContentCache(prev => new Map(prev).set(path, response.data))
          setSelectedFileContent(response.data)
        }
      } catch (error) {
        // Error loading file
        const errorMsg = '加载文件失败: ' + (error as Error).message
        setSelectedFileContent(errorMsg)
      } finally {
        setLoadingFiles(prev => {
          const newSet = new Set(prev)
          newSet.delete(path)
          return newSet
        })
      }
    }
  }, [fileContentCache, loadingFiles])

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    
    const colorMap: { [key: string]: string } = {
      'json': 'text-orange-500',
      'md': 'text-purple-500',
      'txt': 'text-blue-500',
      'csv': 'text-green-500',
      'py': 'text-yellow-500',
      'js': 'text-yellow-400',
      'ts': 'text-blue-600',
      'log': 'text-gray-500',
      'png': 'text-pink-500',
      'jpg': 'text-pink-500',
      'jpeg': 'text-pink-500',
      'gif': 'text-pink-500',
      'svg': 'text-pink-500',
      'webp': 'text-pink-500',
      'xyz': 'text-cyan-500',
      'html': 'text-red-500',
      'htm': 'text-red-500',
    }
    
    const color = colorMap[ext || ''] || 'text-gray-400'
    
    // Image files
    if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext || '')) {
      return <Image className={`w-4 h-4 ${color}`} />
    }
    
    // Molecule files
    if (ext === 'xyz') {
      return <Atom className={`w-4 h-4 ${color}`} />
    }
    
    // HTML files
    if (['html', 'htm'].includes(ext || '')) {
      return <Globe className={`w-4 h-4 ${color}`} />
    }
    
    // Text files
    if (['md', 'txt', 'json', 'csv', 'log'].includes(ext || '')) {
      return <FileText className={`w-4 h-4 ${color}`} />
    }
    
    return <File className={`w-4 h-4 ${color}`} />
  }

  const handleCopyCode = useCallback((code: string) => {
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code)
      setTimeout(() => setCopiedCode(null), 2000)
    })
  }, [])

  const handleDeleteFile = useCallback(async (filePath: string, fileName: string) => {
    const confirmed = window.confirm(`确定要删除 "${fileName}" 吗？`)
    if (!confirmed) return
    
    try {
      const response = await axios.delete(`${API_BASE_URL}/api/files${filePath}`)
      if (response.data.success) {
        // 从文件树中移除已删除的文件
        const removeFileFromTree = (nodes: FileNode[]): FileNode[] => {
          return nodes.filter(node => {
            if (node.path === filePath) {
              return false // 移除这个节点
            }
            if (node.children) {
              node.children = removeFileFromTree(node.children)
            }
            return true
          })
        }
        
        onFileTreeUpdate(removeFileFromTree(fileTree))
        
        // 如果当前选中的文件被删除，清除选择
        if (selectedFilePath === filePath) {
          setSelectedFilePath(null)
          setSelectedFileContent(null)
        }
        
        // 清除缓存
        fileContentCache.delete(filePath)
        
        alert('文件删除成功')
      }
    } catch (error) {
      console.error('删除文件失败:', error)
      alert('删除文件失败: ' + (error as any).response?.data?.error || '未知错误')
    }
  }, [fileTree, onFileTreeUpdate, selectedFilePath, fileContentCache])

  const handleDownloadFile = useCallback((filePath: string) => {
    // 创建下载链接
    const downloadUrl = `${API_BASE_URL}/api/download/file/${filePath}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filePath.split('/').pop() || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }, [])

  const handleDownloadFolder = useCallback((folderPath: string) => {
    // 创建文件夹下载链接
    const downloadUrl = `${API_BASE_URL}/api/download/folder/${folderPath}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${folderPath.split('/').pop() || 'folder'}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }, [])

  const renderFileContent = (content: string, filePath: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase()
    
    if (ext === 'json') {
      try {
        const jsonData = JSON.parse(content)
        return <JsonTreeView data={jsonData} name={filePath.split('/').pop()?.replace('.json', '') || 'data'} />
      } catch (e) {
        // If JSON is invalid, show as text with error message
        return (
          <div>
            <div className="mb-2 p-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-sm">
              JSON 格式错误：{(e as Error).message}
            </div>
            <TextViewer content={content} language="json" />
          </div>
        )
      }
    }
    
    if (ext === 'csv') {
      return <CsvTableView content={content} />
    }
    
    if (ext === 'md') {
      return (
        <div className="prose prose-sm dark:prose-invert max-w-none p-6">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              pre({ children, ...props }: React.HTMLAttributes<HTMLPreElement>) {
                return (
                  <pre className="overflow-x-auto bg-gray-900 text-gray-100 p-4 rounded-lg" {...props}>
                    {children}
                  </pre>
                )
              },
              code({ inline, className, children, ...props }: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) {
                const match = /language-(\w+)/.exec(className || '')
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    customStyle={{
                      margin: 0,
                      fontSize: '0.875rem',
                      lineHeight: '1.5'
                    }}
                    wrapLines={true}
                    wrapLongLines={true}
                    showLineNumbers={true}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm" {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      )
    }
    
    // 对于 txt, log 等纯文本文件，使用 TextViewer
    if (['txt', 'log', 'text', 'conf', 'ini', 'cfg', 'yaml', 'yml', 'toml'].includes(ext || '')) {
      return <TextViewer content={content} language={ext} />
    }
    
    // 对于代码文件，使用语法高亮
    const languageMap: { [key: string]: string } = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'jsx': 'javascript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'cs': 'csharp',
      'php': 'php',
      'rb': 'ruby',
      'go': 'go',
      'rs': 'rust',
      'sh': 'bash',
      'bash': 'bash',
      'sql': 'sql',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'sass': 'sass',
      'less': 'less',
      'xml': 'xml'
    }
    
    const language = languageMap[ext || ''] || 'text'
    
    // 对于识别的编程语言，使用语法高亮
    if (languageMap[ext || '']) {
      return (
        <div className="p-4">
          <SyntaxHighlighter
            language={language}
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
      )
    }
    
    // 默认使用 TextViewer
    return <TextViewer content={content} />
  }

  const renderFileTree = (nodes: FileNode[], level = 0) => {
    return nodes.map((node) => (
      <motion.div
        key={node.path}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -10 }}
        transition={{ duration: 0.2, delay: level * 0.02 }}
      >
        <motion.div
          className={`group flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded-md transition-colors ${
            selectedFilePath === node.path ? 'bg-blue-100 dark:bg-blue-900/30 ring-1 ring-blue-500/20' : ''
          }`}
          style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
          onClick={() => node.type === 'directory' ? toggleDirectory(node.path) : selectFile(node.path, node)}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          {node.type === 'directory' && (
            <motion.div
              animate={{ rotate: node.isExpanded ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight className="w-4 h-4 text-gray-500" />
            </motion.div>
          )}
          {node.type === 'directory' ? (
            <motion.div
              animate={{ scale: node.isExpanded ? 1.1 : 1 }}
              transition={{ duration: 0.2 }}
            >
              <Folder className={`w-4 h-4 ${node.isExpanded ? 'text-blue-600' : 'text-gray-500'}`} />
            </motion.div>
          ) : (
            getFileIcon(node.name)
          )}
          <span className="text-sm text-gray-700 dark:text-gray-300 truncate flex-1">
            {node.name}
          </span>
          {/* 文件夹下载按钮 */}
          {node.type === 'directory' && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDownloadFolder(node.path)
              }}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors opacity-0 group-hover:opacity-100"
              title="下载文件夹"
            >
              <FolderDown className="w-3 h-3 text-gray-500" />
            </button>
          )}
          {/* 文件下载按钮 */}
          {node.type === 'file' && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDownloadFile(node.path)
              }}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors opacity-0 group-hover:opacity-100"
              title="下载文件"
            >
              <Download className="w-3 h-3 text-gray-500" />
            </button>
          )}
          {/* 删除按钮 - 文件和文件夹都可以删除 */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleDeleteFile(node.path, node.name)
            }}
            className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-colors opacity-0 group-hover:opacity-100"
            title={`删除${node.type === 'file' ? '文件' : '文件夹'}`}
          >
            <Trash2 className="w-3 h-3 text-red-500 hover:text-red-600" />
          </button>
          {loadingFiles.has(node.path) && (
            <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
          )}
        </motion.div>
        <AnimatePresence>
          {node.type === 'directory' && node.isExpanded && node.children && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              style={{ overflow: 'hidden' }}
            >
              {renderFileTree(node.children, level + 1)}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    ))
  }

  return (
    <div className="h-full bg-white dark:bg-gray-800 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">文件浏览器</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditingPath(!isEditingPath)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="自定义路径"
          >
            <FolderOpen className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={() => onLoadFileTree(customPath || undefined)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="刷新"
          >
            <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Custom Path Input */}
      {isEditingPath && (
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onLoadFileTree(customPath || undefined)
                  setIsEditingPath(false)
                }
              }}
              placeholder="输入自定义路径（留空显示所有）"
              className="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => {
                onLoadFileTree(customPath || undefined)
                setIsEditingPath(false)
              }}
              className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
            >
              加载
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* File Tree - Fixed Width */}
        <div 
          className="border-r border-gray-200 dark:border-gray-700 overflow-y-auto bg-gray-50 dark:bg-gray-900"
          style={{ width: `${fileTreeWidth}px`, flexShrink: 0 }}
        >
          <div className="p-4">
            <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">文件列表</h4>
            {fileTree.length > 0 ? (
              renderFileTree(fileTree)
            ) : (
              <div className="text-center text-sm text-gray-500 mt-8">
                <Folder className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>暂无文件</p>
              </div>
            )}
          </div>
        </div>

        {/* File Content */}
        <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900" style={{ minWidth: '600px' }}>
          {(() => {
            const cached = selectedFilePath ? fileContentCache.get(selectedFilePath) : null
            console.log('selectedFilePath',selectedFileContent,2,cached)
            
            if (!selectedFilePath) {
              return (
                <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p className="text-sm">选择文件查看内容</p>
                  </div>
                </div>
              )
            }
            
            if (cached) {
              // Special file types (images, molecules, html)
              const name = selectedFilePath?.split('/').pop() || ''
              
              return (
                <>
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getFileIcon(selectedFilePath?.split('/').pop() || '')}
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {selectedFilePath?.split('/').pop()}
                      </span>
                    </div>
                    <button
                      onClick={() => handleDownloadFile(selectedFilePath)}
                      className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                      title="下载文件"
                    >
                      <Download className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                  <div className="flex-1 overflow-auto bg-white dark:bg-gray-800">
                    {typeof cached === 'object' && cached.type === 'html' && cached.content && (
                      <HTMLViewer content={cached.content} fileName={name} />
                    )}
                    {typeof cached === 'object' && cached.type === 'molecule' && cached.content && (
                      <MoleculeViewer content={cached.content} height="100%" />
                    )}
                    {typeof cached === 'object' && cached.type === 'image' && cached.url && (
                      <div className="p-6 flex items-center justify-center h-full">
                        <img src={cached.url} alt={name} className="max-w-full max-h-full object-contain" />
                      </div>
                    )}
                    {typeof cached === 'string' && (
                      <div className="flex-1 overflow-auto bg-white dark:bg-gray-800">
                        {renderFileContent(cached, selectedFilePath || '')}
                      </div>
                    )}
                  </div>
                </>
              )
            }
            
            if (selectedFileContent) {
              // Regular text files
              return (
                <>
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getFileIcon(selectedFilePath?.split('/').pop() || '')}
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {selectedFilePath?.split('/').pop()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDownloadFile(selectedFilePath)}
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                        title="下载文件"
                      >
                        <Download className="w-4 h-4 text-gray-500" />
                      </button>
                      <button
                        onClick={() => handleCopyCode(selectedFileContent)}
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                        title="复制内容"
                      >
                        {copiedCode === selectedFileContent ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4 text-gray-500" />
                        )}
                      </button>
                      <button
                        onClick={() => setIsFileContentExpanded(!isFileContentExpanded)}
                        className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                        title={isFileContentExpanded ? '收起' : '展开'}
                      >
                        {isFileContentExpanded ? (
                          <Minimize2 className="w-4 h-4 text-gray-500" />
                        ) : (
                          <Maximize2 className="w-4 h-4 text-gray-500" />
                        )}
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-auto bg-white dark:bg-gray-800">
                    {renderFileContent(selectedFileContent, selectedFilePath || '')}
                  </div>
                </>
              )
            }
            
            return null
          })()}
        </div>
      </div>
    </div>
  )
}

export default FileExplorer