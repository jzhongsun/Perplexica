'use client';

import React from 'react';
import { UIMessage } from '@ai-sdk/react';
import { partPlugins } from './plugins';
import { DefaultPartRenderer } from './plugins/DefaultPartRenderer';

export interface UIMessagePart {
  type: string;
  [key: string]: any;
}

export interface PartRendererProps {
  part: UIMessagePart;
  partIndex: number;
  message: UIMessage;
}

export interface PartRenderResult {
  shouldRender: boolean;
  content?: React.ReactNode;
  skipNext?: number; // 跳过接下来的N个部分
}

export const PartRenderer: React.FC<PartRendererProps> = ({
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

    return <>{renderResult.content}</>;
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