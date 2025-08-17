import React, { useState } from 'react';
import { Terminal, CheckCircle, AlertCircle, Clock, Wrench, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { JsonDisplay } from './JsonDisplay';

interface ToolResultDisplayProps {
  toolName: string;
  status: string;
  result?: string;
  args?: any;
  isLongRunning?: boolean;
}

export const ToolResultDisplay: React.FC<ToolResultDisplayProps> = ({
  toolName,
  status,
  result,
  args,
  isLongRunning = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isArgsExpanded, setIsArgsExpanded] = useState(false);
  // 解析结果内容，处理特殊格式
  const formatResult = (content: string) => {
    // 尝试解析 JSON
    try {
      const parsed = JSON.parse(content);
      return <JsonDisplay data={parsed} />;
    } catch {
      // 不是 JSON，按普通文本处理
      // 检查是否是表格格式（包含 | 分隔符）
      if (content.includes('|') && content.split('\n').some(line => line.includes('|'))) {
        return (
          <div className="overflow-x-auto">
            <pre className="text-sm font-mono text-gray-700 dark:text-gray-300 whitespace-pre">
              {content}
            </pre>
          </div>
        );
      }
      
      // 普通文本，保留换行
      return (
        <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
          {content}
        </div>
      );
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'running':
      case 'executing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Wrench className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return '执行完成';
      case 'failed':
        return '执行失败';
      case 'running':
      case 'executing':
        return isLongRunning ? '正在执行（长时间运行）' : '正在执行';
      default:
        return '准备执行';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'failed':
        return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20';
      case 'running':
      case 'executing':
        return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`rounded-lg border ${getStatusColor()} p-4 shadow-sm`}
    >
      {/* 工具头部 */}
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
          <Terminal className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">
            {toolName}
          </h4>
          <div className="flex items-center gap-2 mt-1">
            {getStatusIcon()}
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {getStatusText()}
            </span>
          </div>
        </div>
        {/* 统一的展开/收起按钮 */}
        {((result && status === 'completed') || (args && (status === 'executing' || status === 'running' || status === 'started'))) && (
          <button
            onClick={() => {
              if (status === 'completed') {
                setIsExpanded(!isExpanded)
              } else {
                setIsArgsExpanded(!isArgsExpanded)
              }
            }}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
            title={
              status === 'completed' 
                ? (isExpanded ? '收起结果' : '展开结果')
                : (isArgsExpanded ? '收起参数' : '展开参数')
            }
          >
            {(status === 'completed' ? isExpanded : isArgsExpanded) ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        )}
      </div>

      {/* 工具参数 - 在执行中状态时可展开/收起 */}
      {args && (status === 'executing' || status === 'running' || status === 'started') && (
        <AnimatePresence mode="wait">
          {isArgsExpanded && (
            <motion.div
              initial={{ opacity: 0, maxHeight: 0 }}
              animate={{ opacity: 1, maxHeight: 500 }}
              exit={{ opacity: 0, maxHeight: 0 }}
              transition={{
                maxHeight: {
                  type: "spring",
                  damping: 25,
                  stiffness: 200
                },
                opacity: {
                  duration: 0.2
                }
              }}
              className="overflow-hidden"
            >
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">调用参数:</div>
                <div className="bg-white dark:bg-gray-800 rounded-md p-3 shadow-inner">
                  <JsonDisplay data={args} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {/* 工具结果 */}
      <AnimatePresence mode="wait">
        {result && status === 'completed' && isExpanded && (
          <motion.div
            key="content"
            initial={{ opacity: 0, maxHeight: 0 }}
            animate={{ opacity: 1, maxHeight: 2000 }}
            exit={{ opacity: 0, maxHeight: 0 }}
            transition={{
              maxHeight: {
                type: "spring",
                damping: 25,
                stiffness: 200
              },
              opacity: {
                duration: 0.2
              }
            }}
            className="overflow-hidden"
          >
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              {/* 如果有参数，在结果中也展示 */}
              {args && (
                <>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">调用参数:</div>
                  <div className="bg-white dark:bg-gray-800 rounded-md p-2 shadow-inner mb-3">
                    <JsonDisplay data={args} />
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">执行结果:</div>
                </>
              )}
              <div className="bg-white dark:bg-gray-800 rounded-md p-3 shadow-inner">
                {formatResult(result)}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 运行中的动画 */}
      {(status === 'running' || status === 'executing' || status === 'started') && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-2 h-2 bg-blue-500 rounded-full"
              />
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                className="w-2 h-2 bg-blue-500 rounded-full"
              />
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                className="w-2 h-2 bg-blue-500 rounded-full"
              />
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              工具正在执行中...
            </span>
          </div>
        </div>
      )}

      {/* 失败信息 */}
      {status === 'failed' && result && (
        <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-800">
          <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-3">
            <p className="text-sm text-red-700 dark:text-red-300">
              {result}
            </p>
          </div>
        </div>
      )}
    </motion.div>
  );
};