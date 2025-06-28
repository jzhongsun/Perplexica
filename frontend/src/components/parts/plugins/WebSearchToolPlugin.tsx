'use client';

import React, { useState } from 'react';
import { 
  Search, 
  ExternalLink, 
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock
} from 'lucide-react';
import { PartPlugin, PartRendererProps, PartRenderResult } from './index';

const WebSearchToolRenderer: React.FC<{ part: any }> = ({ part }) => {
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
        return <Search size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Searching...';
      case 'input-available':
        return 'Query received';
      case 'output-available':
        return 'Search completed';
      case 'output-error':
        return 'Search failed';
      default:
        return 'Ready';
    }
  };

  const renderSearchResults = () => {
    if (!part.output || !Array.isArray(part.output)) {
      return <div className="text-gray-500 dark:text-gray-400">No results found</div>;
    }

    return (
      <div className="space-y-3">
        {part.output.slice(0, 5).map((result: any, index: number) => (
          <div 
            key={index}
            className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1 line-clamp-2">
                  {result.title || 'Untitled'}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-3">
                  {result.content || result.description || 'No description available'}
                </p>
                <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                  <span className="truncate">
                    {result.url ? new URL(result.url).hostname : 'Unknown source'}
                  </span>
                </div>
              </div>
              {result.url && (
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900 rounded"
                >
                  <ExternalLink size={14} />
                </a>
              )}
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
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Web Search
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {part.state === 'output-available' && part.output && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {Array.isArray(part.output) ? part.output.length : 0} results
            </span>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-blue-200 dark:hover:bg-blue-800 rounded"
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
          </div>
        )}
      </div>
      
      {part.input?.query && (
        <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
          <strong>Query:</strong> "{part.input.query}"
        </div>
      )}
      
      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Search Results:
          </h4>
          {renderSearchResults()}
        </div>
      )}
    </div>
  );
};

export const WebSearchToolPlugin: PartPlugin = {
  type: 'tool-web_search',
  displayName: 'Web Search',
  description: 'Renders web search tool calls and results',
  canHandle: (partType: string) => partType === 'tool-web_search',
  renderer: ({ part }: PartRendererProps): PartRenderResult => {
    return {
      shouldRender: true,
      content: <WebSearchToolRenderer part={part} />
    };
  }
}; 