import React from 'react';
import { Bot, User, FileText, Download } from 'lucide-react';
import { ToolResultDisplay } from './ToolResultDisplay';
import { MemoizedMarkdown } from './MemoizedMarkdown';
import { FileAttachment } from '../types';

interface MessageProps {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp: Date;
  isLastMessage?: boolean;
  isStreaming?: boolean;
  tool_name?: string;
  tool_status?: string;
  tool_args?: any;
  attachments?: FileAttachment[];
}

export const MemoizedMessage = React.memo<MessageProps>(({
  role,
  content,
  timestamp,
  isLastMessage = false,
  isStreaming = false,
  tool_name,
  tool_status,
  tool_args,
  attachments
}) => {
  // Helper function to format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Helper function to get file icon color based on MIME type
  const getFileIconColor = (mimeType: string): string => {
    if (mimeType.startsWith('image/')) return 'text-pink-500';
    if (mimeType.includes('pdf')) return 'text-red-500';
    if (mimeType.includes('json')) return 'text-orange-500';
    if (mimeType.includes('csv')) return 'text-green-500';
    if (mimeType.includes('text/')) return 'text-blue-500';
    return 'text-gray-500';
  };
  return (
    <>
      {role !== 'user' && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg">
            <Bot className="w-5 h-5 text-white" />
          </div>
        </div>
      )}
      
      <div className={`max-w-[80%] ${role === 'user' ? 'order-1' : ''}`}>
        <div className={`rounded-2xl px-4 py-3 shadow-sm ${
          role === 'user'
            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
            : role === 'tool'
            ? 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 glass-premium'
            : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 glass-premium shadow-depth'
        }`}>
          {role === 'tool' && tool_name && tool_status ? (
            <ToolResultDisplay
              toolName={tool_name}
              status={tool_status}
              result={content || undefined}
              args={tool_args}
            />
          ) : role === 'assistant' ? (
            <div className="prose prose-gray dark:prose-invert max-w-none">
              <MemoizedMarkdown 
                className="claude-markdown"
                isStreaming={isStreaming}
                isLastMessage={isLastMessage}
              >
                {content}
              </MemoizedMarkdown>
            </div>
          ) : (
            <div>
              {attachments && attachments.length > 0 && (
                <div className="mb-2 space-y-1">
                  {attachments.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 bg-white/50 dark:bg-gray-700/50 rounded-lg">
                      <FileText className={`w-4 h-4 ${getFileIconColor(file.mime_type)}`} />
                      <span className="text-sm font-medium">{file.name}</span>
                      <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                      {file.url && (
                        <a
                          href={file.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-auto text-blue-500 hover:text-blue-600"
                          title="下载文件"
                        >
                          <Download className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{content}</p>
            </div>
          )}
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 px-1">
          {timestamp.toLocaleTimeString('zh-CN')}
        </p>
      </div>
      
      {role === 'user' && (
        <div className="flex-shrink-0 order-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-600 to-gray-700 flex items-center justify-center shadow-lg">
            <User className="w-5 h-5 text-white" />
          </div>
        </div>
      )}
    </>
  );
}, (prevProps, nextProps) => {
  // 只有当这些关键属性改变时才重新渲染
  return prevProps.id === nextProps.id &&
         prevProps.content === nextProps.content &&
         prevProps.isStreaming === nextProps.isStreaming &&
         prevProps.isLastMessage === nextProps.isLastMessage &&
         prevProps.tool_name === nextProps.tool_name &&
         prevProps.tool_status === nextProps.tool_status &&
         JSON.stringify(prevProps.tool_args) === JSON.stringify(nextProps.tool_args) &&
         JSON.stringify(prevProps.attachments) === JSON.stringify(nextProps.attachments);
});

MemoizedMessage.displayName = 'MemoizedMessage';