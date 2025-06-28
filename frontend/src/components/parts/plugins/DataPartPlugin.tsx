'use client';

import React, { useState } from 'react';
import { PartPlugin } from './index';
import { Database, ChevronDown, ChevronRight } from 'lucide-react';

export const DataPartPlugin: PartPlugin = {
  type: 'data',
  displayName: 'Data',
  description: 'Renders data parts',
  icon: <Database size={16} />,
  canHandle: (partType: string) => partType.startsWith('data-'),
  renderer: ({ part, partIndex, message }) => {
    if (!part.type.startsWith('data-')) {
      return { shouldRender: false };
    }

    const dataPart = part as any;
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
        <div className="border border-purple-200 dark:border-purple-700 rounded-lg p-3 bg-purple-50 dark:bg-purple-900/20 my-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Database size={16} className="text-purple-600 dark:text-purple-400" />
              <span className="font-medium text-purple-900 dark:text-purple-100 text-sm">
                Data ({dataPart.type.substring(5)})
              </span>
              {dataPart.id && (
                <span className="text-xs text-purple-700 dark:text-purple-300">
                  ID: {dataPart.id}
                </span>
              )}
            </div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-purple-200 dark:hover:bg-purple-800 rounded"
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          </div>
          
          {isExpanded && dataPart.data && (
            <div className="mt-3">
              <pre className="text-xs bg-purple-100 dark:bg-purple-900 p-2 rounded overflow-x-auto text-purple-900 dark:text-purple-100">
                {formatData(dataPart.data)}
              </pre>
            </div>
          )}
        </div>
      )
    };
  }
}; 