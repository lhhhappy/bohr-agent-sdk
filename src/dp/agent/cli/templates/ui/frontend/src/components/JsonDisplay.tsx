import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Copy, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface JsonDisplayProps {
  data: any;
  className?: string;
}

interface JsonNodeProps {
  keyName?: string;
  value: any;
  depth?: number;
  isLast?: boolean;
}

const JsonNode: React.FC<JsonNodeProps> = ({ keyName, value, depth = 0, isLast = true }) => {
  const [isExpanded, setIsExpanded] = useState(depth < 5); // 默认展开前五层
  const [copied, setCopied] = useState(false);

  const isObject = value !== null && typeof value === 'object';
  const isArray = Array.isArray(value);
  const hasChildren = isObject && Object.keys(value).length > 0;

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(JSON.stringify(value, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore error
    }
  };

  const getValueDisplay = () => {
    if (value === null) return <span className="text-gray-500">null</span>;
    if (value === undefined) return <span className="text-gray-500">undefined</span>;
    if (typeof value === 'boolean') return <span className="text-blue-600 dark:text-blue-400">{String(value)}</span>;
    if (typeof value === 'number') return <span className="text-green-600 dark:text-green-400">{value}</span>;
    if (typeof value === 'string') {
      // 检查是否是 URL
      if (value.match(/^https?:\/\//)) {
        return (
          <a 
            href={value} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            "{value}"
          </a>
        );
      }
      return <span className="text-orange-600 dark:text-orange-400">"{value}"</span>;
    }
    return null;
  };

  const getChildrenCount = () => {
    if (isArray) return `[${value.length}]`;
    if (isObject) return `{${Object.keys(value).length}}`;
    return '';
  };

  return (
    <div className={`${depth > 0 ? 'ml-4' : ''}`}>
      <div className="flex items-start">
        {hasChildren && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mr-1 p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-3 h-3 text-gray-500" />
            ) : (
              <ChevronRight className="w-3 h-3 text-gray-500" />
            )}
          </button>
        )}
        {!hasChildren && <span className="w-4 inline-block" />}
        
        <div className="flex-1 flex items-start group">
          {keyName && (
            <>
              <span className="text-purple-600 dark:text-purple-400 font-medium">"{keyName}"</span>
              <span className="text-gray-600 dark:text-gray-400 mx-1">:</span>
            </>
          )}
          
          {!hasChildren ? (
            <span>{getValueDisplay()}</span>
          ) : (
            <>
              <span className="text-gray-600 dark:text-gray-400">
                {isArray ? '[' : '{'}
              </span>
              {!isExpanded && (
                <span className="text-gray-500 dark:text-gray-500 ml-1 text-sm">
                  {getChildrenCount()}
                </span>
              )}
              {!isExpanded && (
                <span className="text-gray-600 dark:text-gray-400 ml-1">
                  {isArray ? ']' : '}'}
                </span>
              )}
            </>
          )}
          
          {!isLast && !isExpanded && <span className="text-gray-600 dark:text-gray-400">,</span>}
          
          {/* Copy button */}
          {hasChildren && (
            <button
              onClick={handleCopy}
              className="ml-2 p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-all"
              title="复制"
            >
              {copied ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : (
                <Copy className="w-3 h-3 text-gray-500" />
              )}
            </button>
          )}
        </div>
      </div>
      
      <AnimatePresence>
        {isExpanded && hasChildren && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            {isArray ? (
              value.map((item: any, index: number) => (
                <JsonNode
                  key={index}
                  value={item}
                  depth={depth + 1}
                  isLast={index === value.length - 1}
                />
              ))
            ) : (
              Object.entries(value).map(([key, val], index, arr) => (
                <JsonNode
                  key={key}
                  keyName={key}
                  value={val}
                  depth={depth + 1}
                  isLast={index === arr.length - 1}
                />
              ))
            )}
            {hasChildren && (
              <div className={`${depth > 0 ? 'ml-4' : ''}`}>
                <span className="text-gray-600 dark:text-gray-400">
                  {isArray ? ']' : '}'}
                </span>
                {!isLast && <span className="text-gray-600 dark:text-gray-400">,</span>}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const JsonDisplay: React.FC<JsonDisplayProps> = ({ data, className = '' }) => {
  return (
    <div className={`font-mono text-sm ${className}`}>
      <JsonNode value={data} />
    </div>
  );
};