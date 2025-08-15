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

  // 处理万、亿单位的数值转换
  const parseNumberWithUnit = (value: string): number => {
    if (!value || typeof value !== 'string') return 0;
    
    const cleanValue = value.toString().trim();
    
    // 处理万、亿单位
    if (cleanValue.includes('万')) {
      const num = parseFloat(cleanValue.replace('万', ''));
      return isNaN(num) ? 0 : num * 10000;
    }
    if (cleanValue.includes('亿')) {
      const num = parseFloat(cleanValue.replace('亿', ''));
      return isNaN(num) ? 0 : num * 100000000;
    }
    
    // 处理普通数值（移除可能的逗号）
    const num = parseFloat(cleanValue.replace(/,/g, ''));
    return isNaN(num) ? 0 : num;
  };

  // 解析K线数据用于图表显示
  const parseKlineData = (tableMarkdown: string) => {
    try {
      const lines = tableMarkdown.split('\n').filter(line => line.trim() && !line.includes('|----'));
      const dataLines = lines.slice(1); // 跳过表头
      
      return dataLines.map(line => {
        const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell);
        if (cells.length >= 7) {
          return {
            date: cells[1],
            open: parseNumberWithUnit(cells[3]),
            close: parseNumberWithUnit(cells[4]),
            high: parseNumberWithUnit(cells[5]),
            low: parseNumberWithUnit(cells[6]),
            changePercent: parseFloat(cells[10]?.replace('%', '')) || 0
          };
        }
        return null;
      }).filter(Boolean).slice(0, 20); // 最多显示20个数据点
    } catch {
      return [];
    }
  };

  // 渲染迷你K线图
  const renderMiniKlineChart = (klineData: any[]) => {
    if (!klineData || klineData.length === 0) return null;

    const maxPrice = Math.max(...klineData.map(d => d.high));
    const minPrice = Math.min(...klineData.map(d => d.low));
    const priceRange = maxPrice - minPrice || 1; // 防止除零
    const chartHeight = 120;
    const chartPadding = 40;
    const totalWidth = 800; // 固定总宽度用于viewBox

    return (
      <div className="mb-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
          <h6 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center space-x-2">
            <BarChart3 size={16} />
            <span>价格走势图</span>
          </h6>
          
          <div className="w-full">
            <svg
              width="100%"
              height="100%"
              viewBox={`0 0 ${totalWidth} ${chartHeight + 40}`}
              className="overflow-visible"
              preserveAspectRatio="none"
            >
              {/* 网格线 */}
              <defs>
                <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 30" fill="none" stroke="rgb(229 231 235)" strokeWidth="0.5" className="dark:stroke-gray-600"/>
                </pattern>
              </defs>
              <rect width="100%" height={chartHeight} fill="url(#grid)" />
              
              {/* K线柱 */}
              {klineData.map((data, index) => {
                const x = chartPadding + index * (totalWidth - chartPadding * 2) / Math.max(klineData.length - 1, 1);
                const highY = 10 + ((maxPrice - data.high) / priceRange) * (chartHeight - 20);
                const lowY = 10 + ((maxPrice - data.low) / priceRange) * (chartHeight - 20);
                const openY = 10 + ((maxPrice - data.open) / priceRange) * (chartHeight - 20);
                const closeY = 10 + ((maxPrice - data.close) / priceRange) * (chartHeight - 20);
                
                const isUp = data.close >= data.open;
                const bodyTop = Math.min(openY, closeY);
                const bodyHeight = Math.abs(closeY - openY);
                const bodyColor = isUp ? '#ef4444' : '#22c55e'; // 红涨绿跌
                const wickColor = isUp ? '#ef4444' : '#22c55e';
                
                // 根据数据点数量动态调整K线宽度
                const candleWidth = Math.min(12, Math.max(3, (totalWidth - chartPadding * 2) / klineData.length * 0.6));
                const halfWidth = candleWidth / 2;
                
                return (
                  <g key={index}>
                    {/* 上下影线 */}
                    <line
                      x1={x}
                      y1={highY}
                      x2={x}
                      y2={lowY}
                      stroke={wickColor}
                      strokeWidth="1"
                    />
                    {/* K线实体 */}
                    <rect
                      x={x - halfWidth}
                      y={bodyTop}
                      width={candleWidth}
                      height={Math.max(bodyHeight, 1)}
                      fill={isUp ? bodyColor : 'none'}
                      stroke={bodyColor}
                      strokeWidth="1"
                    />
                  </g>
                );
              })}
              
              {/* 价格标签 */}
              <text x="5" y="15" fontSize="10" fill="rgb(107 114 128)" className="dark:fill-gray-400">
                {maxPrice.toFixed(2)}
              </text>
              <text x="5" y={chartHeight - 5} fontSize="10" fill="rgb(107 114 128)" className="dark:fill-gray-400">
                {minPrice.toFixed(2)}
              </text>
            </svg>
            
            {/* 日期标签 */}
            <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
              <span>{klineData[0]?.date}</span>
              <span>{klineData[klineData.length - 1]?.date}</span>
            </div>
          </div>
          
          {/* 统计信息 */}
          <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-gray-500 dark:text-gray-400">最高</div>
              <div className="font-medium text-red-600 dark:text-red-400">{maxPrice.toFixed(2)}</div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-gray-500 dark:text-gray-400">最低</div>
              <div className="font-medium text-green-600 dark:text-green-400">{minPrice.toFixed(2)}</div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-gray-500 dark:text-gray-400">期间涨跌</div>
              <div className={`font-medium ${klineData[klineData.length - 1]?.changePercent >= 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                {klineData[klineData.length - 1]?.changePercent >= 0 ? '+' : ''}{klineData[klineData.length - 1]?.changePercent.toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-gray-500 dark:text-gray-400">数据点数</div>
              <div className="font-medium text-blue-600 dark:text-blue-400">{klineData.length}</div>
            </div>
          </div>
        </div>
      </div>
    );
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
        
        {/* K线图表 */}
        {historicalData.kline_markdown_table && renderMiniKlineChart(parseKlineData(historicalData.kline_markdown_table))}
        
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
