import React from 'react';
import { Bot, User } from 'lucide-react';
import { ToolResultDisplay } from './ToolResultDisplay';
import { MemoizedMarkdown } from './MemoizedMarkdown';

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
}

export const MemoizedMessage = React.memo<MessageProps>(({
  role,
  content,
  timestamp,
  isLastMessage = false,
  isStreaming = false,
  tool_name,
  tool_status,
  tool_args
}) => {
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
            <p className="text-sm whitespace-pre-wrap">{content}</p>
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
         JSON.stringify(prevProps.tool_args) === JSON.stringify(nextProps.tool_args);
});

MemoizedMessage.displayName = 'MemoizedMessage';