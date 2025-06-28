'use client';

import React from 'react';
import { PartRenderer } from './PartRenderer';
import { getAllPartPlugins } from './plugins';

const mockUIMessage = {
  id: 'test-message',
  role: 'assistant' as const,
  parts: [],
  metadata: {}
};

const testParts = [
  {
    type: 'text',
    text: 'This is a **test message** with markdown support and <think>thinking process</think> content.'
  },
  {
    type: 'tool-web_search',
    toolCallId: 'call-123',
    state: 'output-available',
    input: { query: 'test search query' },
    output: [
      {
        title: 'Test Search Result 1',
        snippet: 'This is a test search result snippet.',
        url: 'https://example.com/result1'
      },
      {
        title: 'Test Search Result 2',
        snippet: 'Another test search result snippet.',
        url: 'https://example.com/result2'
      }
    ]
  },
  {
    type: 'tool-image_search',
    toolCallId: 'call-456',
    state: 'output-available',
    input: { query: 'test images' },
    output: [
      {
        title: 'Test Image 1',
        img_src: 'https://picsum.photos/200/200?random=1',
        source_url: 'https://example.com/image1'
      },
      {
        title: 'Test Image 2',
        img_src: 'https://picsum.photos/200/200?random=2',
        source_url: 'https://example.com/image2'
      }
    ]
  },
  {
    type: 'tool-weather',
    toolCallId: 'call-789',
    state: 'output-available',
    input: { location: 'San Francisco, CA' },
    output: {
      location: 'San Francisco, CA',
      condition: 'Partly Cloudy',
      temperature: 18,
      feels_like: 20,
      humidity: 75,
      wind_speed: 8,
      high: 22,
      low: 14,
      forecast: [
        {
          date: 'Tomorrow',
          condition: 'Sunny',
          high: 24,
          low: 16
        },
        {
          date: 'Day 2',
          condition: 'Foggy',
          high: 19,
          low: 13
        },
        {
          date: 'Day 3',
          condition: 'Partly Cloudy',
          high: 21,
          low: 15
        }
      ]
    }
  },
  {
    type: 'tool-unknown_tool',
    toolCallId: 'call-999',
    state: 'output-available',
    input: { 
      query: 'test unknown tool',
      parameters: { param1: 'value1', param2: 'value2' }
    },
    output: {
      result: 'This is an unknown tool that will use the default renderer',
      data: [1, 2, 3, 4, 5],
      metadata: {
        processingTime: '1.5s',
        source: 'unknown-api'
      }
    }
  },
  {
    type: 'reasoning',
    text: 'This is a reasoning section showing the AI\'s thought process.'
  },
  {
    type: 'source-url',
    sourceId: 'src-1',
    title: 'Example Source Document',
    url: 'https://example.com/source'
  },
  {
    type: 'file',
    filename: 'test-document.pdf',
    mediaType: 'application/pdf',
    url: 'https://example.com/files/test-document.pdf'
  },
  {
    type: 'data-test',
    id: 'data-123',
    data: {
      key1: 'value1',
      key2: 'value2',
      nested: {
        subkey: 'subvalue'
      }
    }
  },
  {
    type: 'unknown-type',
    someProperty: 'someValue'
  }
];

export const PluginTestPage: React.FC = () => {
  const allPlugins = getAllPartPlugins();

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Plugin System Test Page
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Testing all {allPlugins.length} registered part plugins
        </p>
      </div>

      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Rendered Parts
        </h2>
        
        {testParts.map((part, index) => (
          <div key={index} className="space-y-2">
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300">
              {index + 1}. Part Type: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-sm">{part.type}</code>
            </h3>
            <PartRenderer
              part={part}
              partIndex={index}
              message={mockUIMessage}
            />
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Available Plugins
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {allPlugins.map((plugin, index) => (
            <div 
              key={index}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800"
            >
              <div className="flex items-center space-x-2 mb-2">
                {plugin.icon}
                <h3 className="font-medium text-gray-900 dark:text-gray-100">
                  {plugin.displayName}
                </h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {plugin.description}
              </p>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <strong>Type:</strong> {plugin.type}
              </div>
              {plugin.priority && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  <strong>Priority:</strong> {plugin.priority}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 