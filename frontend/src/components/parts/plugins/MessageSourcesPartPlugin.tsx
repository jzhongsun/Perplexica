'use client';

import React from 'react';
import { PartPlugin } from './index';
import { BookOpen, ExternalLink, FileText } from 'lucide-react';
import { PartRendererProps } from '../PartRenderer';

interface MessageSourcesPart {
  part: any;
  partIndex: number;
  message: any;
}

export const MessageSourcesPartRenderer: React.FC<PartRendererProps<MessageSourcesPart>> = ({ part, partIndex, message }) => {
  return <div></div>;
};

export const MessageSourcesPartPlugin: PartPlugin = {
  type: 'data_sources',
  displayName: 'Data Sources',
  description: 'Renders data sources',
  icon: <BookOpen size={16} />,
  canHandle: (partType: string) => partType === 'tool-web_search-search_and_fetch',
  renderer: ({ part, partIndex, message }: MessageSourcesPartProps) => {
    if (!part.type.startsWith('tool-web_search-search_and_fetch')) {
      return { shouldRender: false };
    }

    const sourcePart = part as any;
    const isUrl = part.type === 'source-url';
    const isDocument = part.type === 'source-document';

    return {
      shouldRender: true,
      content: (
        <div className="border border-amber-200 dark:border-amber-700 rounded-lg p-3 bg-amber-50 dark:bg-amber-900/20 my-2">
          <div className="flex items-center space-x-2 mb-2">
            {isUrl ? (
              <ExternalLink size={14} className="text-amber-600 dark:text-amber-400" />
            ) : (
              <FileText size={14} className="text-amber-600 dark:text-amber-400" />
            )}
            <span className="font-medium text-amber-900 dark:text-amber-100 text-sm">
              {isUrl ? 'Source URL' : 'Source Document'}
            </span>
          </div>

          <div className="text-sm">
            <h4 className="font-medium text-amber-900 dark:text-amber-100 mb-1">
              {sourcePart.title}
            </h4>

            {isUrl && sourcePart.url && (
              <a
                href={sourcePart.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                {sourcePart.url}
                <ExternalLink size={10} className="ml-1" />
              </a>
            )}

            {isDocument && (
              <div className="text-xs text-amber-700 dark:text-amber-300">
                {sourcePart.filename && (
                  <div><strong>File:</strong> {sourcePart.filename}</div>
                )}
                {sourcePart.mediaType && (
                  <div><strong>Type:</strong> {sourcePart.mediaType}</div>
                )}
              </div>
            )}
          </div>
        </div>
      )
    };
  }
}; 