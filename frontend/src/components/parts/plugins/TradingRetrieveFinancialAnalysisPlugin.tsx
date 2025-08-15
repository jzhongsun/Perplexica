'use client';

import React, { useState } from 'react';
import { 
  Calculator, 
  TrendingUp, 
  BarChart3,
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock,
  AlertCircle,
  Building2
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';

interface FinancialReport {
  name: string;
  report_markdown_table: string;
}

interface FinancialAnalysisOutput {
  success: boolean;
  error_message?: string;
  market_code: string;
  symbol: string;
  report_date_type: string;
  look_back_years: number;
  reports: FinancialReport[];
}

const TradingRetrieveFinancialAnalysisRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
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
        return <Calculator size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching financial analysis...';
      case 'input-available':
        return 'Parameters received';
      case 'output-available':
        return 'Analysis data ready';
      case 'output-error':
        return 'Failed to fetch analysis';
      default:
        return 'Ready';
    }
  };

  const getReportIcon = (reportName: string) => {
    if (reportName.includes('每股') || reportName.includes('股指标')) {
      return <BarChart3 size={16} className="text-blue-500" />;
    } else if (reportName.includes('成长') || reportName.includes('增长')) {
      return <TrendingUp size={16} className="text-green-500" />;
    } else if (reportName.includes('盈利') || reportName.includes('收益')) {
      return <Calculator size={16} className="text-purple-500" />;
    } else if (reportName.includes('风险') || reportName.includes('负债')) {
      return <AlertCircle size={16} className="text-red-500" />;
    } else {
      return <BarChart3 size={16} className="text-gray-500" />;
    }
  };

  const renderFinancialData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No financial data available</div>;
    }

    const finalOutput = part.output[0];

    let financialData: FinancialAnalysisOutput;
    try {
      financialData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid financial data format</div>;
    }

    if (!financialData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{financialData.error_message || 'Failed to retrieve financial analysis'}</span>
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
                  {financialData.market_code}.{financialData.symbol}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  财务分析指标 ({financialData.report_date_type === 'annual' ? '年报' : '季报'})
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {financialData.look_back_years}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                年回看
              </div>
            </div>
          </div>
        </div>
        
        {/* 财务报告列表 */}
        {financialData.reports && financialData.reports.length > 0 && (
          <div className="space-y-3">            
            {financialData.reports.map((report, index) => (
              <div 
                key={index}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden"
              >
                <div className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getReportIcon(report.name)}
                      <h6 className="font-medium text-gray-900 dark:text-gray-100">
                        {report.name}
                      </h6>
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <MemoizedMarkdown
                      content={report.report_markdown_table}
                      className="prose prose-sm max-w-none dark:prose-invert"
                      options={{
                        overrides: {
                          table: {
                            props: {
                              className: "min-w-full divide-y divide-gray-200 dark:divide-gray-700 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
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
                              className: "px-3 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 border-r border-gray-200 dark:border-gray-700 last:border-r-0"
                            }
                          }
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="border border-blue-200 dark:border-blue-700 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            财务分析-财务指标
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
            className="p-1 hover:bg-blue-200 dark:hover:bg-blue-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderFinancialData()}
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

export const TradingRetrieveFinancialAnalysisPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_financial_analysis_indicators',
  displayName: 'Trading Financial Analysis',
  description: 'Renders trading financial analysis indicators tool calls and displays financial analysis data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_financial_analysis_indicators',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveFinancialAnalysisRenderer part={part} partIndex={0} message={message} />
    };
  }
};
