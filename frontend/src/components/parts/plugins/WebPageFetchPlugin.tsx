'use client';

import React, { useState } from 'react';
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
import { PartRendererProps } from '../PartRenderer';
import { PartPlugin } from './index';
import { ToolUIPart } from 'ai';

const WebPageFetchRenderer: React.FC<PartRendererProps<ToolUIPart>> = ({
  part,
  partIndex,
  message,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
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
        return <Download size={16} />;
    }
  };
  
  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Starting fetch...';
      case 'input-available':
        return 'Fetching...';
      case 'output-available':
        return 'Fetched';
      case 'output-error':
        return 'Fetch failed';
      default:
        return 'Fetch';
    }
  };

  const renderPageContent = () => {
    if (!part.output) {
      return null;
    }

    const output = part.output;
    return (
      <div className="space-y-3">
        {/* {output.title && (
          <div>
            <p className="text-xs text-gray-900 dark:text-gray-100">{output.title}</p>
          </div>
        )} */}        
        {output.text_content && (
          <div>
            <div className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 p-3 rounded max-h-40 overflow-y-auto">
              {output.text_content}
              {/* {output.text_content.length > 500 && '...'} */}
            </div>
          </div>
        )}
        
        {/* {output.metadata && (
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
        )} */}
      </div>
    );
  };

  return (
    <div className="border-l-4 border-green-600 dark:border-green-900 pl-3 py-2 bg-green-50/50 dark:bg-green-900/10">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <Globe size={12} className="text-green-600 dark:text-green-400" />
          {/* <span className="text-xs text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span> */}
          <span className="text-sm text-gray-900 dark:text-gray-100">
            {part.input?.title}
          </span>
          {part.input?.url && (
              <a
                href={part.input.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-xs pl-2 text-blue-600 dark:text-blue-400 hover:underline"
              >
                {/* <Globe size={12} className="mr-1" /> */}
                {new URL(part.input.url).hostname}
                <ExternalLink size={12} className="ml-1" />
              </a>
          )}          
        </div>
        {part.state === 'output-available' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-green-100 dark:hover:bg-green-900/30 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
            
      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderPageContent()}
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

export const WebPageFetchPlugin: PartPlugin = {
  type: 'tool-page_fetch',
  displayName: 'Web Page Fetch',
  description: 'Fetches and processes web page content',
  priority: 100,
  renderer: (props: PartRendererProps<ToolUIPart>) => {
    return {
      shouldRender: true,
      content: <WebPageFetchRenderer {...props} />
    };
  },
  icon: <FileText size={16} />,
  canHandle: (partType: string) => partType === 'tool-web_search-web_page_fetch' || partType === 'tool-web_page_fetch',
}; 