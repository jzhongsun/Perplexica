'use client';

import React, { useState } from 'react';
import { 
  DollarSign, 
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
  Calculator
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';

interface FinancialReport {
  name: string;
  report_markdown_table: string;
}

interface IncomeStatementOutput {
  success: boolean;
  error_message?: string;
  market_code: string;
  symbol: string;
  report_date_type: string;
  look_back_years: number;
  reports: FinancialReport[];
}

const TradingRetrieveIncomeStatementRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
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
        return <DollarSign size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching income statement...';
      case 'input-available':
        return 'Parameters received';
      case 'output-available':
        return 'Income statement data ready';
      case 'output-error':
        return 'Failed to fetch income statement';
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
    if (reportName.includes('收入') || reportName.includes('营业') || reportName.includes('Revenue')) {
      return <DollarSign size={16} className="text-green-500" />;
    } else if (reportName.includes('成本') || reportName.includes('费用') || reportName.includes('Cost') || reportName.includes('Expense')) {
      return <Calculator size={16} className="text-red-500" />;
    } else if (reportName.includes('利润') || reportName.includes('净利') || reportName.includes('Profit') || reportName.includes('Income')) {
      return <TrendingUp size={16} className="text-blue-500" />;
    } else if (reportName.includes('税前') || reportName.includes('税后') || reportName.includes('Tax')) {
      return <BarChart3 size={16} className="text-purple-500" />;
    } else {
      return <DollarSign size={16} className="text-gray-500" />;
    }
  };

  const renderIncomeStatementData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No income statement data available</div>;
    }

    const finalOutput = part.output[0];

    let incomeStatementData: IncomeStatementOutput;
    try {
      incomeStatementData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid income statement data format</div>;
    }

    if (!incomeStatementData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{incomeStatementData.error_message || 'Failed to retrieve income statement'}</span>
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
                  {incomeStatementData.market_code}.{incomeStatementData.symbol}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  利润表 ({incomeStatementData.report_date_type === 'annual' ? '年报' : '季报'})
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {incomeStatementData.look_back_years}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                年回看
              </div>
            </div>
          </div>
        </div>
        
        {/* 利润表列表 */}
        {incomeStatementData.reports && incomeStatementData.reports.length > 0 && (
          <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center space-x-2">
              <DollarSign size={16} />
              <span>利润表</span>
            </h5>
            
            {incomeStatementData.reports.map((report, index) => (
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
    <div className="border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 bg-yellow-50 dark:bg-yellow-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
          财务报表-利润表
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
            className="p-1 hover:bg-yellow-200 dark:hover:bg-yellow-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderIncomeStatementData()}
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

export const TradingRetrieveIncomeStatementPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_financial_income_statement',
  displayName: 'Trading Income Statement',
  description: 'Renders trading financial income statement tool calls and displays income statement data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_financial_income_statement',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveIncomeStatementRenderer part={part} partIndex={0} message={message} />
    };
  }
};
