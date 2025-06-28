'use client';

import React, { useState } from 'react';
import { 
  Settings, 
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock
} from 'lucide-react';
import { PartPlugin, PartRendererProps, PartRenderResult } from './index';

const DefaultToolRenderer: React.FC<{ part: any }> = ({ part }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // 从 tool-xxx 中提取工具名称
  const toolName = part.type.startsWith('tool-') 
    ? part.type.substring(5) 
    : part.type;
  
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
  
  const formatData = (data: any): string => {
    if (typeof data === 'string') {
      return data;
    }
    return JSON.stringify(data, null, 2);
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-800/50">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {toolName.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
        >
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>
      
      {isExpanded && (
        <div className="mt-4 space-y-3">
          {part.input && Object.keys(part.input).length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Input:
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                {formatData(part.input)}
              </pre>
            </div>
          )}
          
          {part.output && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Output:
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                {formatData(part.output)}
              </pre>
            </div>
          )}
          
          {part.errorText && (
            <div>
              <h4 className="text-sm font-semibold text-red-700 dark:text-red-300 mb-2">
                Error:
              </h4>
              <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                {part.errorText}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const DefaultToolPlugin: PartPlugin = {
  type: 'tool-default',
  displayName: 'Default Tool',
  description: 'Renders generic tool calls when no specific plugin is available',
  canHandle: (partType: string) => partType.startsWith('tool-'),
  priority: -1, // 最低优先级，作为兜底方案
  renderer: ({ part }: PartRendererProps): PartRenderResult => {
    return {
      shouldRender: true,
      content: <DefaultToolRenderer part={part} />
    };
  }
}; 