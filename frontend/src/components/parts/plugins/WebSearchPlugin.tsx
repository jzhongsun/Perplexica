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
import { tool, ToolUIPart, UITools, InferToolInput, InferToolOutput, InferUITool } from 'ai';
import { z } from 'zod';

// 强类型定义搜索结果
interface SearchResult {
  title: string;
  url?: string;
  content?: string;
  snippet?: string;
}

// 本地强类型接口 - 避免 AI SDK 联合类型的复杂性
interface WebSearchToolPart {
  type: 'tool-web_search' | 'tool-web_search-web_search';
  toolCallId: string;
  providerExecuted?: boolean;
  state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
  input: {
    query: string;
  };
  output?: {
    results: SearchResult[];
  };
  errorText?: string;
}

// 类型守卫函数
function isWebSearchToolPart(part: any): part is WebSearchToolPart {
  return part && 
         typeof part === 'object' && 
         'type' in part && 
         (part.type === 'tool-web_search' || part.type === 'tool-web_search-web_search') &&
         'state' in part &&
         ['input-streaming', 'input-available', 'output-available', 'output-error'].includes(part.state);
}

const WebSearchRenderer: React.FC<PartRendererProps<WebSearchToolPart>> = ({
  part,
  partIndex,
  message,
}) => {

  const [isExpanded, setIsExpanded] = useState(true);
  
  // 类型守卫确保我们有正确的类型
  if (!isWebSearchToolPart(part)) {
    return null;
  }
  
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
    
    // 现在可以安全访问 output
    if (!part.output?.results || !Array.isArray(part.output.results)) {
      return (
        <div className="text-sm text-gray-500 dark:text-gray-400 italic">
          No search results available
        </div>
      );
    }

    const results = part.output.results;

    return (
      <div className="">
        {results.map((result: SearchResult, index: number) => (
          <div 
            key={`search-result-${index}`}
            className="pl-4"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="text-xs text-gray-900 dark:text-gray-100 mb-2">
                  <span className="font-medium">
                    {index + 1}. {result.title}
                  </span>
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pl-4 inline-flex items-center text-xs text-blue-600 dark:text-blue-400 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {(() => {
                        try {
                          return new URL(result.url).hostname;
                        } catch {
                          return result.url;
                        }
                      })()}
                      <ExternalLink size={12} className="ml-1" />
                    </a>
                  )}
                </div>
                {(result.content || result.snippet) && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 my-2">
                    {result.content || result.snippet}
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
            {part.input?.query && (
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
      
      {part.state === 'output-error' && part.errorText && (
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
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    // 使用类型守卫确保类型安全
    if (!isWebSearchToolPart(part)) {
      return { shouldRender: false };
    }
    
    return {
      shouldRender: true,
      content: <WebSearchRenderer part={part} partIndex={partIndex} message={message} />
    };
  }
}; 