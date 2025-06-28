# Part Plugin System

这是一个可扩展的消息部分渲染插件系统，用于在聊天界面中渲染不同类型的消息部分，包括文本、工具调用、推理过程、源文档等。

## 概述

插件系统允许为不同的消息部分类型创建专用的渲染组件，提供更好的用户体验和视觉展示。系统支持所有类型的UIMessage部分，并允许插件决定是否渲染以及如何处理多个相关部分。

## 架构

```
tools/
├── PartRenderer.tsx        # 主渲染器，路由到对应插件
├── ToolManager.tsx         # 插件管理器组件（弃用）
├── PluginTestPage.tsx      # 插件测试页面
├── plugins/
│   ├── index.ts                 # 插件注册表和接口定义
│   ├── DefaultPartRenderer.tsx  # 默认渲染器
│   ├── TextPartPlugin.tsx       # 文本部分插件
│   ├── ReasoningPartPlugin.tsx  # 推理部分插件
│   ├── SourcePartPlugin.tsx     # 源文档部分插件
│   ├── FilePartPlugin.tsx       # 文件部分插件
│   ├── DataPartPlugin.tsx       # 数据部分插件
│   ├── WebSearchToolPlugin.tsx  # 网络搜索工具插件
│   ├── ImageSearchToolPlugin.tsx # 图像搜索工具插件
│   ├── WeatherToolPlugin.tsx    # 天气工具插件
│   └── DefaultToolPlugin.tsx    # 默认工具插件（兜底方案）
└── README.md              # 本文档
```

## 部分插件接口

每个部分插件都需要实现 `PartPlugin` 接口：

```typescript
interface PartPlugin {
  type: string;                    // 部分类型，如 'text', 'tool-*', 'reasoning' 等
  displayName: string;             // 显示名称
  description: string;             // 插件描述
  renderer: (props: PartRendererProps) => PartRenderResult;  // 渲染函数
  icon?: React.ReactNode;          // 可选图标
  priority?: number;               // 优先级，数字越大优先级越高
  canHandle?: (partType: string) => boolean;  // 自定义匹配函数
}

interface PartRenderResult {
  shouldRender: boolean;           // 是否应该渲染
  content?: React.ReactNode;       // 渲染内容
  skipNext?: number;               // 跳过接下来的N个部分
}
```

## 工具状态

工具支持以下状态：

- `input-streaming`: 输入流式传输中
- `input-available`: 输入可用
- `output-available`: 输出可用
- `output-error`: 输出错误

## 创建新工具插件

### 1. 创建工具插件文件

创建新的工具插件文件（例如 `MyToolPlugin.tsx`）：

```typescript
'use client';

import React, { useState } from 'react';
import { 
  Settings,  // 替换为合适的图标
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock
} from 'lucide-react';
import { PartPlugin, PartRendererProps, PartRenderResult } from './index';

const MyToolRenderer: React.FC<{ part: any }> = ({ part }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const getStateIcon = () => {
    switch (part.state) {
      case 'input-streaming':
        return <Loader2 className="animate-spin" size={16} />;
      case 'input-available':
        return <Clock size={16} />;
      case 'output-available':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'output-error':
        return <XCircle size={16} className="text-red-500" />;
      default:
        return <Settings size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Processing...';
      case 'input-available':
        return 'Input received';
      case 'output-available':
        return 'Completed';
      case 'output-error':
        return 'Error occurred';
      default:
        return 'Ready';
    }
  };

  // 根据你的工具输出格式自定义渲染逻辑
  const renderToolOutput = () => {
    if (!part.output) return null;
    
    // 在这里实现你的自定义渲染逻辑
    return (
      <div className="mt-4">
        {/* 你的工具输出渲染内容 */}
      </div>
    );
  };

  return (
    <div className="border border-purple-200 dark:border-purple-700 rounded-lg p-4 bg-purple-50 dark:bg-purple-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            My Tool
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {part.state === 'output-available' && part.output && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-purple-200 dark:hover:bg-purple-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      
      {part.input && (
        <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
          {/* 显示输入参数 */}
        </div>
      )}
      
      {part.state === 'output-available' && isExpanded && renderToolOutput()}
    </div>
  );
};

export const MyToolPlugin: PartPlugin = {
  type: 'tool-my_tool',
  displayName: 'My Tool',
  description: 'Description of what this tool does',
  canHandle: (partType: string) => partType === 'tool-my_tool',
  renderer: ({ part }: PartRendererProps): PartRenderResult => {
    return {
      shouldRender: true,
      content: <MyToolRenderer part={part} />
    };
  }
};
```

### 2. 注册插件

在 `plugins/index.ts` 中导入并注册插件：

```typescript
import { MyToolPlugin } from './MyToolPlugin';

// 在 partPlugins 对象中添加
export const partPlugins: Record<string, PartPlugin> = {
  // ...其他插件
  'tool-my_tool': MyToolPlugin,
};
```

### 3. 工具类型判断

插件系统会根据 `part.type` 来匹配插件：

- **直接匹配**: `part.type === 'tool-my_tool'` 会直接匹配到你的插件
- **canHandle 函数**: 如果需要处理多个工具类型，使用 `canHandle` 函数
- **兜底方案**: 如果没有匹配的插件，会使用 `DefaultToolPlugin`

### 4. 优先级系统

如果多个插件都能处理同一个类型，系统会按优先级选择：

```typescript
export const MyToolPlugin: PartPlugin = {
  // ...其他属性
  priority: 10, // 数字越大优先级越高
  canHandle: (partType: string) => partType.startsWith('tool-my_'),
};
```

## 现有插件

### 工具插件

#### WebSearchToolPlugin
- **工具类型**: `tool-web_search`
- **功能**: 渲染网络搜索结果
- **特色**: 搜索结果卡片，可点击链接，域名显示

#### ImageSearchToolPlugin
- **工具类型**: `tool-image_search`
- **功能**: 渲染图像搜索结果
- **特色**: 响应式图片网格，悬停效果，源链接

#### WeatherToolPlugin
- **工具类型**: `tool-weather`, `tool-get_weather`
- **功能**: 渲染天气数据和预报
- **特色**: 天气图标，详细数据展示，多日预报

#### DefaultToolPlugin
- **工具类型**: 所有 `tool-*` 类型（兜底方案）
- **功能**: 为没有专用插件的工具提供通用渲染
- **特色**: 可展开的JSON数据显示，状态指示器
- **优先级**: -1（最低，作为兜底方案）

### 其他插件

#### TextPartPlugin
- **类型**: `text`
- **功能**: 渲染文本内容，支持Markdown和thinking标签

#### ReasoningPartPlugin
- **类型**: `reasoning`
- **功能**: 渲染AI推理过程

#### SourcePartPlugin
- **类型**: `source-url`, `source-document`
- **功能**: 渲染源文档和URL引用

#### FilePartPlugin
- **类型**: `file`
- **功能**: 渲染文件附件

#### DataPartPlugin
- **类型**: `data-*`
- **功能**: 渲染数据部分，支持可折叠JSON显示

## 使用方法

插件系统会自动根据 `tool-{name}` 类型路由到对应的插件。如果没有找到专用插件，会使用默认渲染器。

在 `MessageBox.tsx` 中：

```typescript
{part.type.startsWith('tool-') && (
  <ToolRenderer
    toolPart={part}
    isLast={isLast}
    loading={loading}
  />
)}
```

## 样式指南

- 使用一致的边框样式和颜色主题
- 支持明暗主题
- 包含状态指示器（加载、成功、错误）
- 提供可折叠的详细信息
- 使用适当的图标和视觉层次

## 扩展性

系统设计为高度可扩展：

1. **动态注册**: 可以在运行时注册新插件
2. **状态管理**: 支持复杂的工具状态
3. **类型安全**: 完整的TypeScript支持
4. **组件复用**: 共享通用组件和工具函数

## 最佳实践

1. **命名一致性**: 插件名称应与后端工具名称匹配
2. **错误处理**: 优雅地处理缺失或错误的数据
3. **性能**: 大数据集应分页或虚拟化
4. **可访问性**: 包含适当的ARIA标签和键盘导航
5. **响应式**: 在不同屏幕尺寸下良好展示 