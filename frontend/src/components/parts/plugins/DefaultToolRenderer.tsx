'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  ChevronDown, 
  ChevronRight, 
  Settings, 
  CheckCircle, 
  XCircle, 
  Clock,
  Loader2
} from 'lucide-react';
import { ToolRendererProps } from '../ToolRenderer';

export const DefaultToolRenderer: React.FC<ToolRendererProps> = ({
  toolPart,
  isLast,
  loading,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const toolName = toolPart.type.startsWith('tool-') 
    ? toolPart.type.substring(5) 
    : toolPart.type;
  
  const getStateIcon = () => {
    switch (toolPart.state) {
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
    switch (toolPart.state) {
      case 'input-streaming':
        return 'Processing...';
      case 'input-available':
        return 'Input received';
      case 'output-available':
        return 'Completed';
      case 'output-error':
        return 'Error occurred';
      default:
        return 'Unknown state';
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
            {toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
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
          {toolPart.input && Object.keys(toolPart.input).length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Input:
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                {formatData(toolPart.input)}
              </pre>
            </div>
          )}
          
          {toolPart.output && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Output:
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                {formatData(toolPart.output)}
              </pre>
            </div>
          )}
          
          {toolPart.errorText && (
            <div>
              <h4 className="text-sm font-semibold text-red-700 dark:text-red-300 mb-2">
                Error:
              </h4>
              <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                {toolPart.errorText}
              </div>
            </div>
          )}
          
          {toolPart.metadata && Object.keys(toolPart.metadata).length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Metadata:
              </h4>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                {formatData(toolPart.metadata)}
              </pre>
            </div>
          )}
          
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Tool Call ID: {toolPart.toolCallId}
          </div>
        </div>
      )}
    </div>
  );
}; 