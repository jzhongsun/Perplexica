'use client';

import React, { useState } from 'react';
import { 
  FileText, 
  Building2, 
  Calendar,
  ExternalLink,
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock,
  TrendingUp,
  AlertCircle,
  Users,
  Star
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';
import { MarkdownToJSX } from 'markdown-to-jsx';

interface ResearchReport {
  title: string;
  url: string;
  publish_date: string;
  organization: string;
  researcher: string;
  rating: string;
  industry: string;
  content_markdown?: string;
}

interface CompanyResearchReportOutput {
  success: boolean;
  error_message?: string;
  market_code: string;
  symbol: string;
  num_results: number;
  start_date: string;
  end_date: string;
  reports: ResearchReport[];
}

const TradingRetrieveCompanyResearchReportRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedReports, setExpandedReports] = useState<Set<number>>(new Set());
  
  // Markdown 配置选项，禁止渲染外部图片
  const markdownOptions: MarkdownToJSX.Options = {
    overrides: {
      img: {
        component: ({ src, alt, ...props }: any) => {
          // 如果是外部链接，不渲染图片，只显示 alt 文本
          if (src && (src.startsWith('http://') || src.startsWith('https://'))) {
            return (<></>)
          }
          // 本地图片正常渲染
          return <img src={src} alt={alt} {...props} />;
        }
      },
      a: {
        component: ({ href, children, ...props }: any) => {
            return (<>{children}</>)
        }
      }
    }
  };
  
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
        return <FileText size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching research reports...';
      case 'input-available':
        return 'Company info received';
      case 'output-available':
        return 'Reports data ready';
      case 'output-error':
        return 'Failed to fetch reports';
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

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString.split(' ')[0]; // 提取日期部分
    }
  };

  const getRatingColor = (rating: string) => {
    const lowerRating = rating.toLowerCase();
    if (lowerRating.includes('强烈推荐') || lowerRating.includes('买入')) {
      return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
    } else if (lowerRating.includes('推荐') || lowerRating.includes('增持')) {
      return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
    } else if (lowerRating.includes('优于大市')) {
      return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
    } else {
      return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const stripHtmlTags = (html: string) => {
    return html.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ');
  };

  const renderReportsData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No research reports available</div>;
    }

    const finalOutput = part.output[0]

    let reportsData: CompanyResearchReportOutput;
    try {
      reportsData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid research reports data format</div>;
    }

    if (!reportsData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{reportsData.error_message || 'Failed to retrieve research reports'}</span>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        {/* 公司信息 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <Building2 size={20} className="text-blue-500" />
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100">
                  {reportsData.market_code}.{reportsData.symbol}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  研究报告 ({formatDate(reportsData.start_date)} ~ {formatDate(reportsData.end_date)})
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {reportsData.num_results}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                份报告
              </div>
            </div>
          </div>
        </div>
        
        {/* 研究报告列表 */}
        {reportsData.reports && reportsData.reports.length > 0 && (
          <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center space-x-2">
              <FileText size={16} />
              <span>研究报告</span>
            </h5>
            
            {reportsData.reports.map((report, index) => (
              <div 
                key={index}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden"
              >
                <div className="p-3">
                  <div className="flex items-start space-x-2">
                    <span className="flex-shrink-0 text-sm font-medium text-gray-500 dark:text-gray-400 mt-0.5">
                      {index + 1}.
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center flex-1 min-w-0">
                          <div 
                            className="font-medium text-gray-900 dark:text-gray-100 leading-snug cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 mr-3"
                            onClick={() => toggleReportExpansion(index)}
                          >
                            {stripHtmlTags(report.title)}
                          </div>
                          <div className="flex items-center gap-x-2 text-xs flex-shrink-0">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getRatingColor(report.rating)}`}>
                              {report.rating}
                            </span>
                            <a 
                              href={report.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center space-x-1 text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                            >
                              <ExternalLink size={10} />
                              <span>查看原文</span>
                            </a>
                          </div>
                        </div>
                        <button
                          onClick={() => toggleReportExpansion(index)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex-shrink-0 ml-2"
                        >
                          {expandedReports.has(index) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>
                      </div>
                      
                      {/* 报告元信息 */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
                        <div className="flex items-center space-x-1">
                          <Calendar size={10} />
                          <span>{formatDate(report.publish_date)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Building2 size={10} />
                          <span className="truncate">{report.organization}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Users size={10} />
                          <span className="truncate">{report.researcher}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Star size={10} />
                          <span className="truncate">{report.industry}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {expandedReports.has(index) && report.content_markdown && (
                    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 ml-5">
                      <MemoizedMarkdown
                        content={report.content_markdown}
                        className="prose prose-sm max-w-none dark:prose-invert text-sm text-gray-700 dark:text-gray-300"
                        options={markdownOptions}
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
    <div className="border border-cyan-200 dark:border-cyan-700 rounded-lg p-4 bg-cyan-50 dark:bg-cyan-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            研究报告检索
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
            className="p-1 hover:bg-cyan-200 dark:hover:bg-cyan-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderReportsData()}
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

export const TradingRetrieveCompanyResearchReportPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_company_research_report',
  displayName: 'Trading Company Research Report',
  description: 'Renders trading company research report tool calls and displays research reports data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_company_research_report',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveCompanyResearchReportRenderer part={part} partIndex={0} message={message} />
    };
  }
};
