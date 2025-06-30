'use client';

import React from 'react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { ToolUIPart, UITools } from 'ai';

interface WebSearchTool extends UITools {
  "web_search-web_search": {
    input: {
      query: string;
    };
    output: {
      results: any[];
    };
  }
}

const WebSearchAndFetchRenderer: React.FC<PartRendererProps<ToolUIPart<WebSearchTool>>> = ({
  part,
  partIndex,
  message,
}) => {

  return (
    <></>
  );
};

export const WebSearchAndFetchPlugin: PartPlugin = {
  type: 'tool-web_search-search_and_fetch',
  displayName: 'Web Search',
  description: 'Performs web searches and fetch results',
  canHandle: (partType: string) => partType === 'tool-web_search-search_and_fetch',
  renderer: ({ part, partIndex, message }: PartRendererProps<ToolUIPart>): PartRenderResult => {
    return {
      shouldRender: false,
      content: null
    };
  }
}; 