'use client';

import React, { useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock,
  AlertCircle,
  Building2,
  Calendar,
  Activity
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';

interface StockHistoricalOutput {
  success: boolean;
  error_message?: string;
  market_code: string;
  symbol: string;
  interval: string;
  start_date: string;
  end_date: string;
  kline_markdown_table: string;
}

const TradingRetrieveStockHistoricalDataRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
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
        return <BarChart3 size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching historical data...';
      case 'input-available':
        return 'Parameters received';
      case 'output-available':
        return 'Historical data ready';
      case 'output-error':
        return 'Failed to fetch historical data';
      default:
        return 'Ready';
    }
  };

  const getIntervalDisplay = (interval: string) => {
    const intervalMap: { [key: string]: string } = {
      'daily': '日线',
      'weekly': '周线',
      'monthly': '月线',
      '1m': '1分钟',
      '5m': '5分钟',
      '15m': '15分钟',
      '30m': '30分钟',
      '60m': '1小时',
      '4h': '4小时'
    };
    return intervalMap[interval] || interval;
  };

  const renderHistoricalData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No historical data available</div>;
    }

    const finalOutput = part.output[0];

    let historicalData: StockHistoricalOutput;
    try {
      historicalData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid historical data format</div>;
    }

    if (!historicalData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{historicalData.error_message || 'Failed to retrieve historical data'}</span>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        {/* 股票信息 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <Building2 size={20} className="text-blue-500" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100">
                  {historicalData.market_code}.{historicalData.symbol}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  股票历史数据 ({getIntervalDisplay(historicalData.interval)})
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <Calendar size={14} />
                <span>{historicalData.start_date} ~ {historicalData.end_date}</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* K线数据表格 */}
        {historicalData.kline_markdown_table && (
          <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center space-x-2">
              <Activity size={16} />
              <span>K线数据</span>
            </h5>
            
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden">
              <div className="p-3">
                <div className="overflow-x-auto">
                  <MemoizedMarkdown
                    content={historicalData.kline_markdown_table}
                    className="prose prose-sm max-w-none dark:prose-invert"
                    options={{
                      overrides: {
                        table: {
                          props: {
                            className: "min-w-full divide-y divide-gray-200 dark:divide-gray-700 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden text-xs"
                          }
                        },
                        thead: {
                          props: {
                            className: "bg-gray-50 dark:bg-gray-800"
                          }
                        },
                        th: {
                          props: {
                            className: "px-2 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-200 dark:border-gray-700 last:border-r-0"
                          }
                        },
                        tbody: {
                          props: {
                            className: "bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700"
                          }
                        },
                        td: {
                          component: ({ children, ...props }: any) => {
                            // 检查是否是涨跌幅列，并应用相应的颜色
                            const content = children?.toString() || '';
                            let className = "px-2 py-1 whitespace-nowrap text-xs text-gray-900 dark:text-gray-100 border-r border-gray-200 dark:border-gray-700 last:border-r-0";
                            
                            // 涨跌幅着色逻辑
                            if (content.includes('%') || (typeof children === 'string' && /^-?\d+\.?\d*$/.test(content.trim()))) {
                              const numValue = parseFloat(content.replace('%', ''));
                              if (!isNaN(numValue)) {
                                if (numValue > 0) {
                                  className += " text-red-600 dark:text-red-400 font-medium"; // 红色表示上涨
                                } else if (numValue < 0) {
                                  className += " text-green-600 dark:text-green-400 font-medium"; // 绿色表示下跌
                                }
                              }
                            }
                            
                            return <td className={className} {...props}>{children}</td>;
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="border border-indigo-200 dark:border-indigo-700 rounded-lg p-4 bg-indigo-50 dark:bg-indigo-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            股票历史数据
          </span>
          {part.input && (
            <div className="text-medium text-gray-700 dark:text-gray-300 ml-4">
              <span> : {part.input.market_code}.{part.input.symbol} ({getIntervalDisplay(part.input.interval)})</span>
            </div>
          )}
        </div>
        {part.state === 'output-available' && part.output && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderHistoricalData()}
        </div>
      )}
      
      {part.state === 'output-error' && part.errorText && (
        <div className="mt-4">
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            {part.errorText}
          </div>
        </div>
      )}
    </div>
  );
};

export const TradingRetrieveStockHistoricalDataPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_stock_historical_data',
  displayName: 'Trading Stock Historical Data',
  description: 'Renders trading stock historical data tool calls and displays K-line data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_stock_historical_data',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveStockHistoricalDataRenderer part={part} partIndex={0} message={message} />
    };
  }
};
