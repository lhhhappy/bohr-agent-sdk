import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { createCodeComponent } from './EnhancedCodeBlock';
import { StreamingText } from './MessageAnimation';

interface MemoizedMarkdownProps {
  children: string;
  className?: string;
  isStreaming?: boolean;
  isLastMessage?: boolean;
}

export const MemoizedMarkdown = React.memo<MemoizedMarkdownProps>(({ 
  children, 
  className,
  isStreaming = false,
  isLastMessage = false
}) => {
  return (
    <ReactMarkdown
      className={className}
      remarkPlugins={[remarkGfm]}
      components={{
        code: createCodeComponent(),
        a({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline"
              {...props}
            >
              {children}
            </a>
          );
        },
        p({ children }: React.HTMLAttributes<HTMLParagraphElement>) {
          if (isLastMessage && isStreaming) {
            return (
              <p className="mb-4 leading-relaxed text-[15px] text-gray-700 dark:text-gray-300">
                <StreamingText
                  text={String(children)}
                  isStreaming={true}
                />
              </p>
            )
          }
          return <p className="mb-4 leading-relaxed text-[15px] text-gray-700 dark:text-gray-300">{children}</p>;
        },
        ul({ children }: React.HTMLAttributes<HTMLUListElement>) {
          return <ul className="mb-4 space-y-1">{children}</ul>;
        },
        ol({ children }: React.HTMLAttributes<HTMLOListElement>) {
          return <ol className="mb-4 space-y-1 list-decimal list-inside pl-4">{children}</ol>;
        },
        li({ children }: React.HTMLAttributes<HTMLLIElement>) {
          // 检查是否在有序列表中
          const isInOrderedList = (children as any)?.props?.className?.includes('list-decimal');
          if (isInOrderedList) {
            return <li className="leading-relaxed text-gray-700 dark:text-gray-300">{children}</li>;
          }
          // 无序列表样式
          return (
            <li className="relative pl-6 leading-relaxed text-gray-700 dark:text-gray-300">
              <span className="absolute left-0 top-[0.6em] w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full"></span>
              {children}
            </li>
          );
        },
        h1({ children }: React.HTMLAttributes<HTMLHeadingElement>) {
          return <h1 className="text-2xl font-semibold mb-4 mt-6 first:mt-0 text-gray-900 dark:text-gray-100">{children}</h1>;
        },
        h2({ children }: React.HTMLAttributes<HTMLHeadingElement>) {
          return <h2 className="text-xl font-semibold mb-3 mt-5 first:mt-0 text-gray-900 dark:text-gray-100">{children}</h2>;
        },
        h3({ children }: React.HTMLAttributes<HTMLHeadingElement>) {
          return <h3 className="text-lg font-semibold mb-2 mt-4 first:mt-0 text-gray-900 dark:text-gray-100">{children}</h3>;
        },
        strong({ children }: React.HTMLAttributes<HTMLElement>) {
          return <strong className="font-semibold text-gray-900 dark:text-gray-100">{children}</strong>;
        },
        blockquote({ children }: React.HTMLAttributes<HTMLQuoteElement>) {
          return (
            <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 pl-4 my-4 text-gray-700 dark:text-gray-300 bg-blue-50 dark:bg-blue-950/20 py-3 pr-4 rounded-r-md">
              {children}
            </blockquote>
          );
        },
        // 表格支持
        table({ children }: React.HTMLAttributes<HTMLTableElement>) {
          return (
            <div className="my-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                {children}
              </table>
            </div>
          );
        },
        thead({ children }: React.HTMLAttributes<HTMLTableSectionElement>) {
          return <thead className="bg-gray-50 dark:bg-gray-800">{children}</thead>;
        },
        th({ children }: React.HTMLAttributes<HTMLTableCellElement>) {
          return (
            <th className="px-4 py-2 text-left text-sm font-medium text-gray-900 dark:text-gray-100">
              {children}
            </th>
          );
        },
        td({ children }: React.HTMLAttributes<HTMLTableCellElement>) {
          return (
            <td className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 border-t border-gray-200 dark:border-gray-700">
              {children}
            </td>
          );
        }
      }}
    >
      {children}
    </ReactMarkdown>
  );
}, (prevProps, nextProps) => {
  // 只有当内容真正改变时才重新渲染
  return prevProps.children === nextProps.children;
});

MemoizedMarkdown.displayName = 'MemoizedMarkdown';