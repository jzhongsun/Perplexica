'use client';

import React from 'react';
import { partPlugins } from './plugins';
import { DefaultPartRenderer } from './plugins/DefaultPartRenderer';
import { UIDataTypes, UIMessage, UIMessagePart, UITools } from 'ai';

export interface PartRendererProps<TUIMessagePart> {
  part: TUIMessagePart;
  partIndex: number;
  message: UIMessage;
  className?: string;
}

export interface PartRenderResult {
  shouldRender: boolean;
  content?: React.ReactNode;
  skipNext?: number; // 跳过接下来的N个部分
}

export const PartRenderer: React.FC<PartRendererProps<UIMessagePart<any, any>>> = ({
  className,
  part,
  partIndex,
  message
}) => {
  // 查找对应的插件
  let plugin = partPlugins[part.type];

  // 如果没有直接匹配，尝试模式匹配
  if (!plugin) {
    if (part.type.startsWith('tool-')) {
      plugin = partPlugins['__tool__'];
    } else if (part.type.startsWith('data-')) {
      plugin = partPlugins['__data__'];
    } else {
      // 使用自定义匹配函数
      for (const p of Object.values(partPlugins)) {
        if (p.canHandle && p.canHandle(part.type)) {
          plugin = p;
          break;
        }
      }
    }
  }

  if (plugin) {
    // 使用专用插件渲染
    const renderResult = plugin.renderer({
      part,
      partIndex,
      message,
    });

    if (!renderResult.shouldRender) {
      return null;
    }

    if (!renderResult.content || (renderResult.content as string).length === 0) {
      return null;
    }

    return <div className={className}>{renderResult.content}</div>;
  } else {
    // 使用默认渲染器
    const renderResult = DefaultPartRenderer.renderer({
      part,
      partIndex,
      message,
    });

    if (!renderResult.shouldRender) {
      return null;
    }

    return <>{renderResult.content}</>;
  }
};

// 高性能深度比较函数，专门为UIMessagePart优化
const arePartsContentEqual = (prev: UIMessagePart<any, any>, next: UIMessagePart<any, any>): boolean => {
  // 类型不同，内容必然不同
  if (prev.type !== next.type) {
    return false;
  }

  // 根据不同的part类型进行优化的比较
  switch (prev.type) {
    case 'text': {
      const prevText = prev as any;
      const nextText = next as any;
      return prevText.text === nextText.text && prevText.state === nextText.state;
    }
    
    case 'reasoning': {
      const prevReasoning = prev as any;
      const nextReasoning = next as any;
      return prevReasoning.text === nextReasoning.text && 
             prevReasoning.state === nextReasoning.state;
    }
    
    default: {
      // 对于工具类和数据类part，比较关键属性
      if (prev.type.startsWith('tool-')) {
        const prevTool = prev as any;
        const nextTool = next as any;
        return prevTool.state === nextTool.state &&
               JSON.stringify(prevTool.input) === JSON.stringify(nextTool.input) &&
               JSON.stringify(prevTool.output) === JSON.stringify(nextTool.output) &&
               prevTool.errorText === nextTool.errorText;
      }
      
      if (prev.type.startsWith('data-')) {
        const prevData = prev as any;
        const nextData = next as any;
        return prevData.id === nextData.id &&
               JSON.stringify(prevData.data) === JSON.stringify(nextData.data);
      }
      
      if (prev.type.startsWith('source-')) {
        const prevSource = prev as any;
        const nextSource = next as any;
        return prevSource.sourceId === nextSource.sourceId &&
               prevSource.url === nextSource.url &&
               prevSource.title === nextSource.title;
      }
      
      if (prev.type === 'file') {
        const prevFile = prev as any;
        const nextFile = next as any;
        return prevFile.mediaType === nextFile.mediaType &&
               prevFile.filename === nextFile.filename &&
               prevFile.url === nextFile.url;
      }
      
      // 对于其他类型，进行浅层比较主要属性，避免深度递归
      const prevKeys = Object.keys(prev);
      const nextKeys = Object.keys(next);
      
      if (prevKeys.length !== nextKeys.length) {
        return false;
      }
      
      for (const key of prevKeys) {
        if (key === 'type') continue; // 已经比较过
        
        const prevVal = (prev as any)[key];
        const nextVal = (next as any)[key];
        
        // 对于简单值直接比较
        if (prevVal === nextVal) {
          continue;
        }
        
        // 对于对象和数组，使用JSON序列化比较（虽然不是最优，但对于大多数情况足够快）
        if (typeof prevVal === 'object' && typeof nextVal === 'object') {
          if (JSON.stringify(prevVal) !== JSON.stringify(nextVal)) {
            return false;
          }
        } else {
          return false;
        }
      }
      
      return true;
    }
  }
};

export const MemoizedPartRenderer = React.memo<PartRendererProps<UIMessagePart<any, any>>>(
  PartRenderer,
  (prevProps, nextProps) => {
    // 基本属性比较
    if (prevProps.partIndex !== nextProps.partIndex) {
      return false;
    }
    if (prevProps.className !== nextProps.className) {
      return false;
    }
    
    // 忽略message的比较（按要求忽略message不一致）
    // 只专注于part内容的深度比较
    return arePartsContentEqual(prevProps.part, nextProps.part);
  }
);

MemoizedPartRenderer.displayName = 'MemoizedPartRenderer';