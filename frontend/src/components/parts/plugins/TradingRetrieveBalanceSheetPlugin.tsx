'use client';

import React, { useState } from 'react';
import { 
  PieChart, 
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
  Layers
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';

interface FinancialReport {
  name: string;
  report_markdown_table: string;
}

interface BalanceSheetOutput {
  success: boolean;
  error_message?: string;
  market_code: string;
  symbol: string;
  report_date_type: string;
  look_back_years: number;
  reports: FinancialReport[];
}

const TradingRetrieveBalanceSheetRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedReports, setExpandedReports] = useState<Set<number>>(new Set([0])); // 默认展开第一个报告
  
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
        return <PieChart size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching balance sheet...';
      case 'input-available':
        return 'Parameters received';
      case 'output-available':
        return 'Balance sheet data ready';
      case 'output-error':
        return 'Failed to fetch balance sheet';
      default:
        return 'Ready';
    }
  };

  const toggleReportExpansion = (index: number) => {
    const newExpanded = new Set(expandedReports);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedReports(newExpanded);
  };

  const getReportIcon = (reportName: string) => {
    if (reportName.includes('资产') || reportName.includes('Assets')) {
      return <Layers size={16} className="text-blue-500" />;
    } else if (reportName.includes('负债') || reportName.includes('Liabilities')) {
      return <AlertCircle size={16} className="text-red-500" />;
    } else if (reportName.includes('所有者权益') || reportName.includes('股东权益') || reportName.includes('Equity')) {
      return <TrendingUp size={16} className="text-green-500" />;
    } else {
      return <PieChart size={16} className="text-gray-500" />;
    }
  };

  const renderBalanceSheetData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No balance sheet data available</div>;
    }

    const finalOutput = part.output[0];

    let balanceSheetData: BalanceSheetOutput;
    try {
      balanceSheetData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid balance sheet data format</div>;
    }

    if (!balanceSheetData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{balanceSheetData.error_message || 'Failed to retrieve balance sheet'}</span>
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
                  {balanceSheetData.market_code}.{balanceSheetData.symbol}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  资产负债表 ({balanceSheetData.report_date_type === 'annual' ? '年报' : '季报'})
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {balanceSheetData.look_back_years}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                年回看
              </div>
            </div>
          </div>
        </div>
        
        {/* 资产负债表列表 */}
        {balanceSheetData.reports && balanceSheetData.reports.length > 0 && (
          <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center space-x-2">
              <PieChart size={16} />
              <span>资产负债表</span>
            </h5>
            
            {balanceSheetData.reports.map((report, index) => (
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
                    <button
                      onClick={() => toggleReportExpansion(index)}
                      className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                      {expandedReports.has(index) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </button>
                  </div>
                  
                  {expandedReports.has(index) && (
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
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="border border-green-200 dark:border-green-700 rounded-lg p-4 bg-green-50 dark:bg-green-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
          财务报表-资产负债表
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
            className="p-1 hover:bg-green-200 dark:hover:bg-green-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderBalanceSheetData()}
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

export const TradingRetrieveBalanceSheetPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_financial_balance_sheet',
  displayName: 'Trading Balance Sheet',
  description: 'Renders trading financial balance sheet tool calls and displays balance sheet data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_financial_balance_sheet',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveBalanceSheetRenderer part={part} partIndex={0} message={message} />
    };
  }
};
