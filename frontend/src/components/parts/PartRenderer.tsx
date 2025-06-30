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