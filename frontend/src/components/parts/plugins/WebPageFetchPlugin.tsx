'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  FileText, 
  ExternalLink, 
  CheckCircle, 
  XCircle, 
  Loader2,
  Globe,
  ChevronDown,
  ChevronRight,
  Download
} from 'lucide-react';
import { ToolRendererProps } from '../ToolRenderer';
import { ToolPlugin } from './index';

const WebPageFetchRenderer: React.FC<ToolRendererProps> = ({
  toolPart,
  isLast,
  loading,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
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
        return <Download size={16} />;
    }
  };
  
  const getStateText = () => {
    switch (toolPart.state) {
      case 'input-streaming':
        return 'Starting fetch...';
      case 'input-available':
        return 'Fetching page...';
      case 'output-available':
        return 'Page fetched';
      case 'output-error':
        return 'Fetch failed';
      default:
        return 'Fetch';
    }
  };

  const renderPageContent = () => {
    if (!toolPart.output) {
      return null;
    }

    const output = toolPart.output;
    
    return (
      <div className="space-y-3">
        {output.title && (
          <div>
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Page Title:
            </h5>
            <p className="text-sm text-gray-900 dark:text-gray-100">{output.title}</p>
          </div>
        )}
        
        {output.content && (
          <div>
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Content Preview:
            </h5>
            <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 p-3 rounded max-h-40 overflow-y-auto">
              {output.content.substring(0, 500)}
              {output.content.length > 500 && '...'}
            </div>
          </div>
        )}
        
        {output.metadata && (
          <div>
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Metadata:
            </h5>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {output.metadata.description && (
                <p><strong>Description:</strong> {output.metadata.description}</p>
              )}
              {output.metadata.author && (
                <p><strong>Author:</strong> {output.metadata.author}</p>
              )}
              {output.metadata.publishedDate && (
                <p><strong>Published:</strong> {output.metadata.publishedDate}</p>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="border border-green-200 dark:border-green-700 rounded-lg p-4 bg-green-50 dark:bg-green-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <FileText size={16} className="text-green-600 dark:text-green-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Web Page Fetch
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {toolPart.state === 'output-available' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-green-200 dark:hover:bg-green-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      
      {toolPart.input?.url && (
        <div className="mt-2">
          <a
            href={toolPart.input.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            <Globe size={12} className="mr-1" />
            {new URL(toolPart.input.url).hostname}
            <ExternalLink size={12} className="ml-1" />
          </a>
        </div>
      )}
      
      {toolPart.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Page Content:
          </h4>
          {renderPageContent()}
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

export const WebPageFetchPlugin: ToolPlugin = {
  name: 'web_page_fetch',
  displayName: 'Web Page Fetch',
  description: 'Fetches and processes web page content',
  component: WebPageFetchRenderer,
  icon: <FileText size={16} />,
  supportedStates: ['input-streaming', 'input-available', 'output-available', 'output-error'],
}; 