'use client';

import React, { useState } from 'react';
import { 
  Image, 
  ExternalLink, 
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock
} from 'lucide-react';
import { PartPlugin, PartRendererProps, PartRenderResult } from './index';

const ImageSearchToolRenderer: React.FC<{ part: any }> = ({ part }) => {
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
        return <Image size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Searching images...';
      case 'input-available':
        return 'Query received';
      case 'output-available':
        return 'Images found';
      case 'output-error':
        return 'Search failed';
      default:
        return 'Ready';
    }
  };

  const renderImageResults = () => {
    if (!part.output || !Array.isArray(part.output)) {
      return <div className="text-gray-500 dark:text-gray-400">No images found</div>;
    }

    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {part.output.slice(0, 9).map((image: any, index: number) => (
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
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Image Search
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span>
        </div>
        {part.state === 'output-available' && part.output && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {Array.isArray(part.output) ? part.output.length : 0} images
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
      
      {part.input?.query && (
        <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
          <strong>Query:</strong> "{part.input.query}"
        </div>
      )}
      
      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Found Images:
          </h4>
          {renderImageResults()}
        </div>
      )}
    </div>
  );
};

export const ImageSearchToolPlugin: PartPlugin = {
  type: 'tool-image_search',
  displayName: 'Image Search',
  description: 'Renders image search tool calls and results',
  canHandle: (partType: string) => partType === 'tool-image_search',
  renderer: ({ part }: PartRendererProps): PartRenderResult => {
    return {
      shouldRender: true,
      content: <ImageSearchToolRenderer part={part} />
    };
  }
}; 