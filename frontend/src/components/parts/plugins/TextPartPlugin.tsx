'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';
import ThinkBox from '../../ThinkBox';
import { MarkdownToJSX } from 'markdown-to-jsx';

const ThinkTagProcessor = ({ children }: { children: React.ReactNode }) => {
  return <ThinkBox content={children as string} />;
};

export const TextPartPlugin: PartPlugin = {
  type: 'text',
  displayName: 'Text',
  description: 'Renders text content with markdown support',
  renderer: ({ part, message }) => {
    if (part.type !== 'text') {
      return { shouldRender: false };
    }

    const textPart = part as any;
    let content = textPart.text;

    // 处理思考标签
    if (message.role === 'assistant' && content.includes('<think>')) {
      const openThinkTag = content.match(/<think>/g)?.length || 0;
      const closeThinkTag = content.match(/<\/think>/g)?.length || 0;

      if (openThinkTag > closeThinkTag) {
        content += '</think> <a> </a>'; // The extra <a> </a> is to prevent the think component from looking bad
      }
    }

    const markdownOverrides: MarkdownToJSX.Options = {
      overrides: {
        think: {
          component: ThinkTagProcessor,
        },
      },
    };

    return {
      shouldRender: true,
      content: (
        <MemoizedMarkdown
          content={content}
          className={cn(
            'prose prose-h1:mb-3 prose-h2:mb-2 prose-h2:mt-6 prose-h2:font-[800] prose-h3:mt-4 prose-h3:mb-1.5 prose-h3:font-[600] dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 font-[400]',
            'max-w-none break-words text-black dark:text-white',
          )}
          options={markdownOverrides}
        />
      )
    };
  }
}; 