'use client';

import React from 'react';
import { PartPlugin } from './index';
import { FileIcon, ExternalLink } from 'lucide-react';

export const FilePartPlugin: PartPlugin = {
  type: 'file',
  displayName: 'File',
  description: 'Renders file attachments',
  icon: <FileIcon size={16} />,
  renderer: ({ part, partIndex, message }) => {
    if (part.type !== 'file') {
      return { shouldRender: false };
    }

    const filePart = part as any;

    return {
      shouldRender: true,
      content: (
        <div className="border border-green-200 dark:border-green-700 rounded-lg p-3 bg-green-50 dark:bg-green-900/20 my-2">
          <div className="flex items-center space-x-2">
            <FileIcon size={16} className="text-green-600 dark:text-green-400" />
            <div className="flex-1">
              <div className="font-medium text-green-900 dark:text-green-100 text-sm">
                {filePart.filename || 'File'}
              </div>
              <div className="text-xs text-green-700 dark:text-green-300">
                {filePart.mediaType}
              </div>
            </div>
            {filePart.url && (
              <a
                href={filePart.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                <ExternalLink size={12} />
              </a>
            )}
          </div>
        </div>
      )
    };
  }
}; 