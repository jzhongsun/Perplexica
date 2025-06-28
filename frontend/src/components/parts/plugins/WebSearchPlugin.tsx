'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Search, 
  ExternalLink, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader2,
  Globe,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { ToolRendererProps, ToolUIPart } from '../ToolRenderer';
import { ToolPlugin } from './index';

const WebSearchRenderer: React.FC<ToolRendererProps> = ({
  toolPart,
  isLast,
  loading,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const getStateIcon = () => {
    switch (toolPart.state) {
      case 'input-streaming':
      case 'input-available':
        return <Loader2 className="animate-spin" size={16} />;
      case 'output-available':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'output-error':
        return <XCircle size={16} className="text-red-500" />;
      default:
        return <Search size={16} />;
    }
  };
  
  const getStateText = () => {
    switch (toolPart.state) {
      case 'input-streaming':
        return 'Starting search...';
      case 'input-available':
        return 'Searching...';
      case 'output-available':
        return 'Search completed';
      case 'output-error':
        return 'Search failed';
      default:
        return 'Search';
    }
  };

  const renderSearchResults = () => {
    if (!toolPart.output || !Array.isArray(toolPart.output)) {
      return null;
    }

    return (
      <div className="space-y-3">
        {toolPart.output.map((result: any, index: number) => (
          <div 
            key={index}
            className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 bg-white dark:bg-gray-800"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                  {result.title || `Result ${index + 1}`}
                </h4>
                {result.snippet && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {result.snippet}
                  </p>
                )}
                {result.url && (
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <Globe size={12} className="mr-1" />
                    {new URL(result.url).hostname}
                    <ExternalLink size={12} className="ml-1" />
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="border border-blue-200 dark:border-blue-700 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <Search size={16} className="text-blue-600 dark:text-blue-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Web Search
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {toolPart.state === 'output-available' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-blue-200 dark:hover:bg-blue-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      
      {toolPart.input?.query && (
        <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
          <strong>Query:</strong> "{toolPart.input.query}"
        </div>
      )}
      
      {toolPart.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Search Results:
          </h4>
          {renderSearchResults()}
        </div>
      )}
      
      {toolPart.errorText && (
        <div className="mt-3">
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            {toolPart.errorText}
          </div>
        </div>
      )}
    </div>
  );
};

export const WebSearchPlugin: ToolPlugin = {
  name: 'web_search',
  displayName: 'Web Search',
  description: 'Performs web searches and displays results',
  component: WebSearchRenderer,
  icon: <Search size={16} />,
  supportedStates: ['input-streaming', 'input-available', 'output-available', 'output-error'],
}; 