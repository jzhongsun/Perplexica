'use client';

import React, { useState } from 'react';
import { PartPlugin } from './index';
import { HelpCircle, ChevronDown, ChevronRight } from 'lucide-react';

export const DefaultPartRenderer: PartPlugin = {
  type: 'default',
  displayName: 'Default',
  description: 'Default renderer for unknown part types',
  icon: <HelpCircle size={16} />,
  renderer: ({ part, partIndex, message }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    
    const formatData = (data: any): string => {
      if (typeof data === 'string') {
        return data;
      }
      return JSON.stringify(data, null, 2);
    };

    return {
      shouldRender: true,
      content: (
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50 dark:bg-gray-800/50 my-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <HelpCircle size={16} className="text-gray-500 dark:text-gray-400" />
              <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                Unknown Part Type: {part.type}
              </span>
            </div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          </div>
          
          {isExpanded && (
            <div className="mt-3">
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto text-gray-700 dark:text-gray-300">
                {formatData(part)}
              </pre>
            </div>
          )}
        </div>
      )
    };
  }
}; 