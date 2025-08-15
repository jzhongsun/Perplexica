'use client';

import React, { useState } from 'react';
import { 
  Activity, 
  TrendingUp, 
  BarChart3,
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock,
  AlertCircle,
  Building2,
  Layers,
  Signal,
  Info,
  Zap,
  Target
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';

interface IndicatorReport {
  indicator_name: string;
  indicator_description: string;
  indicator_report_markdown_table: string;
}

interface StockstatsIndicatorsOutput {
  success: boolean;
  error_message?: string;
  reports: IndicatorReport[];
}

const TradingRetrieveStockstatsIndicatorsReportRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [selectedIndicator, setSelectedIndicator] = useState<number | null>(null);
  
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
        return <Activity size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching technical indicators...';
      case 'input-available':
        return 'Parameters received';
      case 'output-available':
        return 'Indicators data ready';
      case 'output-error':
        return 'Failed to fetch indicators';
      default:
        return 'Ready';
    }
  };

  const selectIndicator = (index: number | null) => {
    setSelectedIndicator(index);
  };

  const getIndicatorIcon = (indicatorName: string) => {
    const name = indicatorName.toLowerCase();
    
    // 趋势指标
    if (name.includes('sma') || name.includes('ema') || name.includes('vwma')) {
      return <TrendingUp size={16} className="text-blue-500" />;
    }
    
    // MACD系列指标
    if (name === 'macd') {
      return <BarChart3 size={16} className="text-purple-500" />;
    } else if (name === 'macds') {
      return <Signal size={16} className="text-purple-600" />;
    } else if (name === 'macdh') {
      return <Activity size={16} className="text-purple-400" />;
    }
    
    // 震荡指标
    if (name.includes('rsi')) {
      return <Target size={16} className="text-orange-500" />;
    } else if (name.includes('mfi')) {
      return <Zap size={16} className="text-orange-600" />;
    }
    
    // 布林带系列
    if (name === 'boll') {
      return <Layers size={16} className="text-green-500" />;
    } else if (name === 'boll_ub') {
      return <Layers size={16} className="text-green-600" />;
    } else if (name === 'boll_lb') {
      return <Layers size={16} className="text-green-400" />;
    }
    
    // 波动性指标
    if (name.includes('atr')) {
      return <Activity size={16} className="text-red-500" />;
    }
    
    // 默认图标
    return <Activity size={16} className="text-gray-500" />;
  };

  const getIndicatorDisplayName = (indicatorName: string) => {
    const nameMap: { [key: string]: string } = {
      'close_50_sma': '50日均线 (SMA50)',
      'close_200_sma': '200日均线 (SMA200)',
      'close_10_ema': '10日指数均线 (EMA10)',
      'macd': 'MACD差离值',
      'macds': 'MACD信号线',
      'macdh': 'MACD柱状图',
      'rsi': 'RSI相对强弱指标',
      'boll': '布林带中轨',
      'boll_ub': '布林带上轨',
      'boll_lb': '布林带下轨',
      'atr': 'ATR真实波幅',
      'vwma': 'VWMA量价加权均线',
      'mfi': 'MFI资金流量指标',
      'ema': 'EMA指数均线',
      'sma': 'SMA简单均线',
      'kdj': 'KDJ随机指标',
      'cci': 'CCI顺势指标',
      'obv': 'OBV成交量指标'
    };
    return nameMap[indicatorName] || indicatorName.toUpperCase();
  };

  // 解析表格数据获取最新值
  const getLatestValue = (tableMarkdown: string) => {
    try {
      const lines = tableMarkdown.split('\n').filter(line => line.trim() && !line.includes('|----'));
      const lastDataLine = lines[lines.length - 1];
      if (lastDataLine) {
        const cells = lastDataLine.split('|').map(cell => cell.trim()).filter(cell => cell);
        if (cells.length >= 2) {
          const value = parseFloat(cells[1]);
          return isNaN(value) ? 'N/A' : value.toFixed(2);
        }
      }
    } catch {
      return 'N/A';
    }
    return 'N/A';
  };

  // 获取最新日期
  const getLatestDate = (tableMarkdown: string) => {
    try {
      const lines = tableMarkdown.split('\n').filter(line => line.trim() && !line.includes('|----'));
      const lastDataLine = lines[lines.length - 1];
      if (lastDataLine) {
        const cells = lastDataLine.split('|').map(cell => cell.trim()).filter(cell => cell);
        if (cells.length >= 1) {
          return cells[0];
        }
      }
    } catch {
      return 'N/A';
    }
    return 'N/A';
  };

  const renderOverviewTab = (indicatorsData: StockstatsIndicatorsOutput) => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indicatorsData.reports.map((indicator, index) => {
          const latestValue = getLatestValue(indicator.indicator_report_markdown_table);
          const latestDate = getLatestDate(indicator.indicator_report_markdown_table);
          
          return (
            <div 
              key={index}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => selectIndicator(index)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  {getIndicatorIcon(indicator.indicator_name)}
                  <h6 className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                    {getIndicatorDisplayName(indicator.indicator_name)}
                  </h6>
                </div>
                <ChevronRight size={14} className="text-gray-400" />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 dark:text-gray-400">当前值</span>
                  <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                    {latestValue}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 dark:text-gray-400">更新日期</span>
                  <span className="text-xs text-gray-600 dark:text-gray-300">
                    {latestDate}
                  </span>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                  {indicator.indicator_description.split('.')[0]}...
                </p>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderIndicatorDetail = (indicator: IndicatorReport) => {
    return (
      <div className="space-y-4">
        {/* 指标信息头部 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
          <div className="flex items-center space-x-3 mb-3">
            {getIndicatorIcon(indicator.indicator_name)}
            <div>
              <h6 className="font-medium text-gray-900 dark:text-gray-100">
                {getIndicatorDisplayName(indicator.indicator_name)}
              </h6>
              <div className="flex items-center space-x-2 mt-1">
                <Info size={12} className="text-blue-500" />
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {indicator.indicator_description}
                </p>
              </div>
            </div>
          </div>
          
          {/* 快速概览 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-500 dark:text-gray-400">当前值</div>
              <div className="font-bold text-blue-600 dark:text-blue-400">
                {getLatestValue(indicator.indicator_report_markdown_table)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-500 dark:text-gray-400">指标类型</div>
              <div className="font-medium text-gray-700 dark:text-gray-300 text-sm">
                {(() => {
                  const name = indicator.indicator_name.toLowerCase();
                  if (name.includes('sma') || name.includes('ema') || name.includes('vwma')) return '趋势';
                  if (name.includes('macd')) return '动量';
                  if (name.includes('rsi') || name.includes('mfi')) return '震荡';
                  if (name.includes('boll')) return '波动';
                  if (name.includes('atr')) return '波动性';
                  return '技术';
                })()}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-500 dark:text-gray-400">更新时间</div>
              <div className="font-medium text-gray-700 dark:text-gray-300 text-sm">
                {getLatestDate(indicator.indicator_report_markdown_table)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2">
              <div className="text-xs text-gray-500 dark:text-gray-400">数据点数</div>
              <div className="font-medium text-gray-700 dark:text-gray-300 text-sm">
                {indicator.indicator_report_markdown_table.split('\n').filter(line => line.trim() && !line.includes('|----')).length - 1}
              </div>
            </div>
          </div>
        </div>
        
        {/* 历史数据表格 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
          <h6 className="font-medium text-gray-900 dark:text-gray-100 mb-3">历史数据</h6>
          <div className="overflow-x-auto">
            <MemoizedMarkdown
              content={indicator.indicator_report_markdown_table}
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
                      className: "px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-200 dark:border-gray-700 last:border-r-0"
                    }
                  },
                  tbody: {
                    props: {
                      className: "bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700"
                    }
                  },
                  td: {
                    props: {
                      className: "px-3 py-2 whitespace-nowrap text-xs text-gray-900 dark:text-gray-100 border-r border-gray-200 dark:border-gray-700 last:border-r-0"
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
    );
  };

  const renderIndicatorsData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No technical indicators data available</div>;
    }

    const finalOutput = part.output[0];

    let indicatorsData: StockstatsIndicatorsOutput;
    try {
      indicatorsData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid technical indicators data format</div>;
    }

    if (!indicatorsData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{indicatorsData.error_message || 'Failed to retrieve technical indicators'}</span>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        {/* 输入参数信息 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <Building2 size={20} className="text-blue-500" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100">
                  {part.input?.market_code}.{part.input?.symbol}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  技术指标分析 (回看{part.input?.look_back_days}天)
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {indicatorsData.reports.length}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                个指标
              </div>
            </div>
          </div>
          
          {/* 指标列表 */}
          {part.input?.indicators && (
            <div className="flex flex-wrap gap-2">
              {part.input.indicators.map((indicator: string, index: number) => (
                <span 
                  key={index}
                  className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
                >
                  {getIndicatorDisplayName(indicator)}
                </span>
              ))}
            </div>
          )}
        </div>
        
        {/* 动态标签页切换 */}
        <div className="bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => selectIndicator(null)}
              className={`px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                selectedIndicator === null
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              概览
            </button>
            {indicatorsData.reports.map((indicator, index) => (
              <button
                key={index}
                onClick={() => selectIndicator(index)}
                className={`px-3 py-2 text-xs font-medium rounded-md transition-colors flex items-center space-x-1 ${
                  selectedIndicator === index
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                {getIndicatorIcon(indicator.indicator_name)}
                <span>{getIndicatorDisplayName(indicator.indicator_name).split(' ')[0]}</span>
              </button>
            ))}
          </div>
        </div>
        
        {/* 内容区域 */}
        {selectedIndicator === null ? (
          renderOverviewTab(indicatorsData)
        ) : (
          renderIndicatorDetail(indicatorsData.reports[selectedIndicator])
        )}
      </div>
    );
  };

  return (
    <div className="border border-emerald-200 dark:border-emerald-700 rounded-lg p-4 bg-emerald-50 dark:bg-emerald-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            技术指标分析
          </span>
          {part.input && (
            <div className="text-medium text-gray-700 dark:text-gray-300 ml-4">
              <span> : {part.input.market_code}.{part.input.symbol}</span>
            </div>
          )}
        </div>
        {part.state === 'output-available' && part.output && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-emerald-200 dark:hover:bg-emerald-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderIndicatorsData()}
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

export const TradingRetrieveStockstatsIndicatorsReportPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_stockstats_indicators_report',
  displayName: 'Trading Stockstats Indicators Report',
  description: 'Renders trading stockstats indicators report tool calls and displays technical indicators data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_stockstats_indicators_report',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveStockstatsIndicatorsReportRenderer part={part} partIndex={0} message={message} />
    };
  }
};
