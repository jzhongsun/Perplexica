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
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { ToolUIPart, UITools } from 'ai';

interface WebSearchTool extends UITools {
  "web_search-web_search": {
    input: {
      query: string;
    };
    output: {
      results: any[];
    };
  }
}

const WebSearchRenderer: React.FC<PartRendererProps<ToolUIPart<WebSearchTool>>> = ({
  part,
  partIndex,
  message,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const getStateIcon = () => {
    switch (part.state) {
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
    switch (part.state) {
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
    if (part.state !== "output-available") {
      return null;
    }
    if (!part.output || !Array.isArray(part.output.results)) {
      return null;
    }

    return (
      <div className="space-y-3">
        {part.output.results?.map((result: any, index: number) => (
          <div 
            key={index}
            className="pl-4"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <span className="text-xs text-gray-900 dark:text-gray-100 mb-2">
                  {`${index + 1}. ${result.title}`}
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pl-4 inline-flex items-center text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {/* <Globe size={12} className="mr-1" /> */}
                      {new URL(result.url).hostname}
                      <ExternalLink size={12} className="ml-1" />
                    </a>
                  )}

                </span>
                {result.content && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 my-2">
                    {result.content}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="border-l-4 border-blue-600 dark:border-blue-900 pl-3 py-2 bg-blue-50/50 dark:bg-blue-900/10">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <Search size={16} className="text-blue-600 dark:text-blue-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {part.input.query && (
            <div className="text-sm text-gray-700 dark:text-gray-300">
              <strong>Search:</strong> "{part.input.query}"
            </div>
          )}
          </span>
          {/* <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span> */}
        </div>
        {part.state === 'output-available' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      
      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {/* <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Search Results:
          </h4> */}
          {renderSearchResults()}
        </div>
      )}
      
      {part.errorText && (
        <div className="mt-3">
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            {part.errorText}
          </div>
        </div>
      )}
    </div>
  );
};

export const WebSearchPlugin: PartPlugin = {
  type: 'tool-web_search',
  displayName: 'Web Search',
  description: 'Performs web searches and displays results',
  canHandle: (partType: string) => partType === 'tool-web_search' || partType === 'tool-web_search-web_search',
  renderer: ({ part, partIndex, message }: PartRendererProps<ToolUIPart>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <WebSearchRenderer part={part} partIndex={partIndex} message={message} />
    };
  }
}; 