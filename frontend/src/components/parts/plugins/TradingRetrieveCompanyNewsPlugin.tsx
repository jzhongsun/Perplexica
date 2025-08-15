'use client';

import React, { useState } from 'react';
import { 
  Building2, 
  Newspaper, 
  Calendar,
  ExternalLink,
  ChevronDown, 
  ChevronRight,
  CheckCircle,
  Loader2,
  XCircle,
  Clock,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { PartPlugin } from './index';
import { MemoizedMarkdown } from '../../ui/MemoizedMarkdown';
import { MarkdownToJSX } from 'markdown-to-jsx';

interface NewsItem {
  title: string;
  url: string;
  publish_date: string;
  source: string;
  snippet: string;
  content_markdown?: string;
}

interface CompanyNewsOutput {
  success: boolean;
  error_message?: string;
  company_name: string;
  symbol: string;
  num_results: number;
  news: NewsItem[];
}

const TradingRetrieveCompanyNewsRenderer: React.FC<PartRendererProps<any>> = ({ part, partIndex, message }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedNews, setExpandedNews] = useState<Set<number>>(new Set());
  
  // Markdown 配置选项，禁止渲染外部图片
  const markdownOptions: MarkdownToJSX.Options = {
    overrides: {
      img: {
        component: ({ src, alt, ...props }: any) => {
          // 如果是外部链接，不渲染图片，只显示 alt 文本
          if (src && (src.startsWith('http://') || src.startsWith('https://'))) {
            return (<></>)
            // return alt ? <span className="text-gray-500 italic">[图片: {alt}]</span> : <span className="text-gray-500 italic">[图片]</span>;
          }
          // 本地图片正常渲染
          return <img src={src} alt={alt} {...props} />;
        }
      },
      a: {
        component: ({ href, children, ...props }: any) => {
            return (<>{children}</>)
        //   return (
        //     <a 
        //       href={href} 
        //       target="_blank" 
        //       rel="noopener noreferrer"
        //       className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
        //       {...props}
        //     >
        //       {children}
        //     </a>
        //   );
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
        return <Newspaper size={16} />;
    }
  };

  const getStateText = () => {
    switch (part.state) {
      case 'input-streaming':
        return 'Fetching company news...';
      case 'input-available':
        return 'Company info received';
      case 'output-available':
        return 'News data ready';
      case 'output-error':
        return 'Failed to fetch news';
      default:
        return 'Ready';
    }
  };

  const toggleNewsExpansion = (index: number) => {
    const newExpanded = new Set(expandedNews);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedNews(newExpanded);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const stripHtmlTags = (html: string) => {
    return html.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ');
  };

  const renderNewsData = () => {
    if (!part.output) {
      return <div className="text-gray-500 dark:text-gray-400">No news data available</div>;
    }

    const finalOutput = part.output[0]

    let newsData: CompanyNewsOutput;
    try {
      newsData = JSON.parse(finalOutput.text);
    } catch {
      return <div className="text-red-500">Invalid news data format</div>;
    }

    if (!newsData.success) {
      return (
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <AlertCircle size={16} />
          <span>{newsData.error_message || 'Failed to retrieve news'}</span>
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
                  {newsData.company_name}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  股票代码: {newsData.symbol}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {newsData.num_results}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                条资讯
              </div>
            </div>
          </div>
        </div>
        
        {/* 新闻列表 */}
        {newsData.news && newsData.news.length > 0 && (
          <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center space-x-2">
              <TrendingUp size={16} />
              <span>最新资讯</span>
            </h5>
            
            {newsData.news.map((newsItem, index) => (
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
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center flex-1 min-w-0">
                          <div 
                            className="font-medium text-gray-900 dark:text-gray-100 leading-snug cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 truncate mr-3"
                            onClick={() => toggleNewsExpansion(index)}
                          >
                            {stripHtmlTags(newsItem.title)}
                          </div>
                          <div className="flex items-center gap-x-3 text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                            <div className="flex items-center space-x-1">
                              <Calendar size={10} />
                              <span>{formatDate(newsItem.publish_date)}</span>
                            </div>
                            <span>{newsItem.source}</span>
                            <a 
                              href={newsItem.url}
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
                          onClick={() => toggleNewsExpansion(index)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex-shrink-0 ml-2"
                        >
                          {expandedNews.has(index) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>
                      </div>
                      
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed line-clamp-2 mt-2">
                        {stripHtmlTags(newsItem.snippet)}
                      </p>
                    </div>
                  </div>
                  
                  {expandedNews.has(index) && newsItem.content_markdown && (
                    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 ml-5">
                      <MemoizedMarkdown
                        content={newsItem.content_markdown}
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
    <div className="border border-orange-200 dark:border-orange-700 rounded-lg p-4 bg-orange-50 dark:bg-orange-900/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStateIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            公司资讯检索
          </span>
          {part.input && (
            <div className="text-medium text-gray-700 dark:text-gray-300 ml-4">
                <span> : {part.input.company_name} ({part.input.symbol})</span>
            </div>
          )}
          {/* <span className="text-sm text-gray-500 dark:text-gray-400">
            {getStateText()}
          </span> */}
        </div>
        {part.state === 'output-available' && part.output && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-orange-200 dark:hover:bg-orange-800 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>

      {part.state === 'output-available' && isExpanded && (
        <div className="mt-4">
          {renderNewsData()}
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

export const TradingRetrieveCompanyNewsPlugin: PartPlugin = {
  type: 'tool-trading-retrieve_company_news',
  displayName: 'Trading Company News',
  description: 'Renders trading company news retrieval tool calls and displays news data',
  canHandle: (partType: string) => partType === 'tool-trading-retrieve_company_news',
  renderer: ({ part, partIndex, message }: PartRendererProps<any>): PartRenderResult => {
    return {
      shouldRender: true,
      content: <TradingRetrieveCompanyNewsRenderer part={part} partIndex={0} message={message} />
    };
  }
};
