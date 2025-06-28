'use client';

import React from 'react';
import { PartPlugin } from './index';
import { Brain } from 'lucide-react';

export const ReasoningPartPlugin: PartPlugin = {
  type: 'reasoning',
  displayName: 'Reasoning',
  description: 'Renders reasoning/thinking content',
  icon: <Brain size={16} />,
  renderer: ({ part, partIndex, message }) => {
    if (part.type !== 'reasoning') {
      return { shouldRender: false };
    }

    const reasoningPart = part as any;

    return {
      shouldRender: true,
      content: (
        <div className="border border-indigo-200 dark:border-indigo-700 rounded-lg p-4 bg-indigo-50 dark:bg-indigo-900/20 my-2">
          <div className="flex items-center space-x-2 mb-2">
            <Brain size={16} className="text-indigo-600 dark:text-indigo-400" />
            <span className="font-medium text-indigo-900 dark:text-indigo-100">
              Reasoning
            </span>
          </div>
          <div className="text-sm text-indigo-800 dark:text-indigo-200 whitespace-pre-wrap">
            {reasoningPart.text}
          </div>
        </div>
      )
    };
  }
}; 