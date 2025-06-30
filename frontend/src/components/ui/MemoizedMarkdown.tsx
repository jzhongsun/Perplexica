import { memo } from 'react';
import Markdown, { MarkdownToJSX } from 'markdown-to-jsx';

interface MemoizedMarkdownProps {
  content: string;
  options?: MarkdownToJSX.Options;
  className?: string;
  id?: string;
  style?: React.CSSProperties;
  onClick?: React.MouseEventHandler<HTMLDivElement>;
  onMouseEnter?: React.MouseEventHandler<HTMLDivElement>;
  onMouseLeave?: React.MouseEventHandler<HTMLDivElement>;
}

export const MemoizedMarkdown = memo(
  ({ content, options, className, ...props }: MemoizedMarkdownProps) => {
    if (!content) return null;
    
    return (
      <div className={className} {...props}>
        <Markdown options={options}>
          {content}
        </Markdown>
      </div>
    );
  },
  (prevProps, nextProps) => {
    // Only re-render if content or options change
    return (
      prevProps.content === nextProps.content &&
      JSON.stringify(prevProps.options) === JSON.stringify(nextProps.options)
    );
  }
);

MemoizedMarkdown.displayName = 'MemoizedMarkdown';