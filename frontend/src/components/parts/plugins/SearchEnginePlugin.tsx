'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Search, 
  ExternalLink, 
  CheckCircle, 
  XCircle, 
  Loader2,
  Globe,
  ChevronDown,
  ChevronRight,
  Star,
  Calendar
} from 'lucide-react';
import { ToolRendererProps } from '../ToolRenderer';
import { ToolPlugin } from './index';

const SearchEngineRenderer: React.FC<ToolRendererProps> = ({
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
        return 'Initializing search...';
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
    if (!toolPart.output) {
      return null;
    }

    const results = Array.isArray(toolPart.output) ? toolPart.output : [toolPart.output];
    
    return (
      <div className="space-y-3">
        {results.map((result: any, index: number) => (
          <div 
            key={index}
            className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 bg-white dark:bg-gray-800"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                  {result.title || `Result ${index + 1}`}
                </h4>
                {result.content && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {result.content}
                  </p>
                )}
                <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      <Globe size={10} className="mr-1" />
                      {new URL(result.url).hostname}
                      <ExternalLink size={10} className="ml-1" />
                    </a>
                  )}
                  {result.score && (
                    <div className="inline-flex items-center">
                      <Star size={10} className="mr-1" />
                      Score: {result.score.toFixed(2)}
                    </div>
                  )}
                  {result.publishedDate && (
                    <div className="inline-flex items-center">
                      <Calendar size={10} className="mr-1" />
                      {new Date(result.publishedDate).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="border border-purple-200 dark:border-purple-700 rounded-lg p-4 bg-purple-50 dark:bg-purple-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <Search size={16} className="text-purple-600 dark:text-purple-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Search Engine
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {toolPart.state === 'output-available' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-purple-200 dark:hover:bg-purple-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        {toolPart.input?.query && (
          <span className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-gray-700 dark:text-gray-300">
            <strong>Query:</strong> "{toolPart.input.query}"
          </span>
        )}
        {toolPart.input?.engines && (
          <span className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-gray-700 dark:text-gray-300">
            <strong>Engines:</strong> {Array.isArray(toolPart.input.engines) ? toolPart.input.engines.join(', ') : toolPart.input.engines}
          </span>
        )}
        {toolPart.input?.lang && (
          <span className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-gray-700 dark:text-gray-300">
            <strong>Language:</strong> {toolPart.input.lang}
          </span>
        )}
      </div>
      
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

export const SearchEnginePlugin: ToolPlugin = {
  name: 'searxng_search',
  displayName: 'Search Engine',
  description: 'Performs searches using various search engines',
  component: SearchEngineRenderer,
  icon: <Search size={16} />,
  supportedStates: ['input-streaming', 'input-available', 'output-available', 'output-error'],
}; 