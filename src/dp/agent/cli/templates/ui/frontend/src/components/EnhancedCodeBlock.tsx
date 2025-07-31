import React, { useState } from 'react';
import { Copy, Check, Download } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { motion } from 'framer-motion';

interface EnhancedCodeBlockProps {
  language: string;
  children: string;
  filename?: string;
  showLineNumbers?: boolean;
  className?: string;
}

export const EnhancedCodeBlock: React.FC<EnhancedCodeBlockProps> = React.memo(({
  language,
  children,
  filename,
  showLineNumbers = true,
  className = ''
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([children], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `code.${language}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const CodeContent = () => (
    <div className="relative group">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 rounded-t-lg">
        <div className="flex items-center gap-3">
          {filename ? (
            <span className="text-sm text-gray-400 font-mono">{filename}</span>
          ) : language === 'json' ? (
            <span className="text-sm text-gray-400 font-mono">结果</span>
          ) : null}
        </div>
        <div className={`flex items-center gap-2 ${language === 'json' ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity`}>
          <motion.button
            onClick={handleCopy}
            className="p-1.5 rounded hover:bg-gray-700 transition-colors text-gray-400 hover:text-white"
            whileTap={{ scale: 0.95 }}
            title="复制代码"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </motion.button>
          {filename && (
            <motion.button
              onClick={handleDownload}
              className="p-1.5 rounded hover:bg-gray-700 transition-colors text-gray-400 hover:text-white"
              whileTap={{ scale: 0.95 }}
              title="下载代码"
            >
              <Download className="w-4 h-4" />
            </motion.button>
          )}
        </div>
      </div>

      {/* Code */}
      <div className="overflow-auto max-h-96">
        <SyntaxHighlighter
          language={language}
          style={oneLight}
          showLineNumbers={language === 'json' ? false : showLineNumbers}
          customStyle={{
            margin: 0,
            borderRadius: '0 0 0.5rem 0.5rem',
            fontSize: '0.875rem',
            lineHeight: '1.5',
            padding: '1rem',
            background: '#f9fafb'
          }}
          wrapLines={true}
          wrapLongLines={true}
        >
          {children}
        </SyntaxHighlighter>
      </div>
    </div>
  );

  return (
    <div className={`rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <CodeContent />
    </div>
  );
});

// 用于替换Markdown中的代码块
export const createCodeComponent = () => {
  return React.memo(({ inline, className, children }: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) => {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : 'text';
    
    if (inline) {
      return (
        <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0 rounded-sm font-mono text-sm">
          {children}
        </code>
      );
    }

    // 检查是否有文件名（通过注释或其他方式）
    const codeString = String(children).replace(/\n$/, '');
    const firstLine = codeString.split('\n')[0];
    let filename: string | undefined;
    let actualCode = codeString;

    // 检查第一行是否是文件名注释
    if (firstLine.startsWith('//') || firstLine.startsWith('#') || firstLine.startsWith('/*')) {
      const fileMatch = firstLine.match(/(?:\/\/|#|\/\*)\s*(?:filename:|file:)?\s*(.+?)(?:\*\/)?$/i);
      if (fileMatch) {
        filename = fileMatch[1].trim();
        actualCode = codeString.split('\n').slice(1).join('\n');
      }
    }

    // 检测是否为单行短代码块
    const codeLines = actualCode.split('\n');
    const isSingleLineShort = codeLines.length === 1 && actualCode.length < 60;

    // 对于单行短代码块，使用紧凑样式
    if (isSingleLineShort) {
      return (
        <div className="inline-block my-2">
          <code className="inline-block bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-md text-sm font-mono border border-gray-200 dark:border-gray-700">
            {actualCode}
          </code>
        </div>
      );
    }

    return (
      <EnhancedCodeBlock
        language={language}
        filename={filename}
        showLineNumbers={actualCode.split('\n').length > 5}
      >
        {actualCode}
      </EnhancedCodeBlock>
    );
  });
};