'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Image, 
  ExternalLink, 
  CheckCircle, 
  XCircle, 
  Loader2,
  ChevronDown,
  ChevronRight,
  Eye
} from 'lucide-react';
import { ToolRendererProps } from '../ToolRenderer';
import { ToolPlugin } from './index';

const ImageSearchRenderer: React.FC<ToolRendererProps> = ({
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
        return <Image size={16} />;
    }
  };
  
  const getStateText = () => {
    switch (toolPart.state) {
      case 'input-streaming':
        return 'Starting image search...';
      case 'input-available':
        return 'Searching for images...';
      case 'output-available':
        return 'Images found';
      case 'output-error':
        return 'Image search failed';
      default:
        return 'Image Search';
    }
  };

  const renderImageResults = () => {
    if (!toolPart.output || !Array.isArray(toolPart.output)) {
      return null;
    }

    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {toolPart.output.slice(0, 9).map((image: any, index: number) => (
          <div 
            key={index}
            className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden bg-white dark:bg-gray-800 group"
          >
            <div className="relative aspect-square">
              <img
                src={image.img_src || image.thumbnail_url || image.url}
                alt={image.title || `Image ${index + 1}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/api/placeholder/150/150';
                }}
              />
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                <button className="opacity-0 group-hover:opacity-100 bg-white bg-opacity-90 p-2 rounded-full transition-opacity duration-200">
                  <Eye size={16} />
                </button>
              </div>
            </div>
            <div className="p-2">
              <h5 className="text-xs font-medium text-gray-900 dark:text-gray-100 mb-1 line-clamp-2">
                {image.title || `Image ${index + 1}`}
              </h5>
              {image.source_url && (
                <a
                  href={image.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  <ExternalLink size={10} className="mr-1" />
                  View source
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="border border-pink-200 dark:border-pink-700 rounded-lg p-4 bg-pink-50 dark:bg-pink-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <Image size={16} className="text-pink-600 dark:text-pink-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Image Search
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {toolPart.state === 'output-available' && toolPart.output && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {Array.isArray(toolPart.output) ? toolPart.output.length : 0} images
            </span>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-pink-200 dark:hover:bg-pink-800 rounded"
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
          </div>
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
            Found Images:
          </h4>
          {renderImageResults()}
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

export const ImageSearchPlugin: ToolPlugin = {
  name: 'image_search',
  displayName: 'Image Search',
  description: 'Searches for images based on a query',
  component: ImageSearchRenderer,
  icon: <Image size={16} />,
  supportedStates: ['input-streaming', 'input-available', 'output-available', 'output-error'],
}; 