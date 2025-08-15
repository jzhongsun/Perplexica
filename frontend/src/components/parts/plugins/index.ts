import React from 'react';
import { PartRendererProps, PartRenderResult } from '../PartRenderer';
import { TextPartPlugin } from './TextPartPlugin';
import { ImageSearchToolPlugin } from './ImageSearchToolPlugin';
import { WeatherToolPlugin } from './WeatherToolPlugin';
import { DefaultToolPlugin } from './DefaultToolPlugin';
import { ReasoningPartPlugin } from './ReasoningPartPlugin';
import { SourcePartPlugin } from './SourcePartPlugin';
import { FilePartPlugin } from './FilePartPlugin';
import { DataPartPlugin } from './DataPartPlugin';
import { WebPageFetchPlugin } from './WebPageFetchPlugin';
import { WebSearchPlugin } from './WebSearchPlugin';
import { WebSearchAndFetchPlugin } from './WebSearchAndFetchPlugin';
import { TradingRetrieveCompanyNewsPlugin } from './TradingRetrieveCompanyNewsPlugin';
import { TradingRetrieveFinancialAnalysisPlugin } from './TradingRetrieveFinancialAnalysisPlugin';
import { TradingRetrieveBalanceSheetPlugin } from './TradingRetrieveBalanceSheetPlugin';
import { TradingRetrieveCashFlowPlugin } from './TradingRetrieveCashFlowPlugin';
import { TradingRetrieveIncomeStatementPlugin } from './TradingRetrieveIncomeStatementPlugin';
import { TradingRetrieveStockHistoricalDataPlugin } from './TradingRetrieveStockHistoricalDataPlugin';
import { TradingRetrieveCompanyResearchReportPlugin } from './TradingRetrieveCompanyResearchReportPlugin';
import { TradingRetrieveStockstatsIndicatorsReportPlugin } from './TradingRetrieveStockstatsIndicatorsReportPlugin';

export interface PartPlugin {
  type: string;                    // 部分类型，如 'text', 'tool-*', 'reasoning' 等
  displayName: string;             // 显示名称
  description: string;             // 插件描述
  renderer: (props: PartRendererProps<any>) => PartRenderResult;  // 渲染函数
  icon?: React.ReactNode;          // 可选图标
  priority?: number;               // 优先级，数字越大优先级越高
  canHandle?: (partType: string) => boolean;  // 自定义匹配函数
}

// 部分插件注册表
export const partPlugins: Record<string, PartPlugin> = {
  'text': TextPartPlugin,
  'reasoning': ReasoningPartPlugin,
  'source-url': SourcePartPlugin,
  'source-document': SourcePartPlugin,
  'file': FilePartPlugin,
  'step-start': {
    type: 'step-start',
    displayName: 'Step Start',
    description: 'Renders step start markers',
    renderer: () => ({
      shouldRender: true,
      content: React.createElement('div', { className: "h-px w-full bg-gray-200 dark:bg-gray-700 my-4" })
    })
  },
  // 具体工具插件
  'tool-image_search': ImageSearchToolPlugin,
  'tool-weather': WeatherToolPlugin,
  'tool-get_weather': WeatherToolPlugin,
  'tool-web_search-web_page_fetch': WebPageFetchPlugin,
  'tool-web_page_fetch': WebPageFetchPlugin,
  'tool-web_search-web_search': WebSearchPlugin,
  'tool-web_search': WebSearchPlugin,
  'tool-web_search-search_and_fetch': WebSearchAndFetchPlugin,
  'tool-web_search_and_fetch': WebSearchAndFetchPlugin,
  'tool-trading-retrieve_company_news': TradingRetrieveCompanyNewsPlugin,
  'tool-trading-retrieve_financial_analysis_indicators': TradingRetrieveFinancialAnalysisPlugin,
  'tool-trading-retrieve_financial_balance_sheet': TradingRetrieveBalanceSheetPlugin,
  'tool-trading-retrieve_financial_cash_flow_statement': TradingRetrieveCashFlowPlugin,
  'tool-trading-retrieve_financial_income_statement': TradingRetrieveIncomeStatementPlugin,
  'tool-trading-retrieve_stock_historical_data': TradingRetrieveStockHistoricalDataPlugin,
  'tool-trading-retrieve_company_research_report': TradingRetrieveCompanyResearchReportPlugin,
  'tool-trading-retrieve_stockstats_indicators_report': TradingRetrieveStockstatsIndicatorsReportPlugin,
  // 通用工具插件匹配器（兜底方案）
  '__tool__': DefaultToolPlugin,
  '__data__': DataPartPlugin,
};

// 获取所有已注册的部分插件
export const getAllPartPlugins = (): PartPlugin[] => {
  return Object.values(partPlugins);
};

// 根据部分类型获取插件
export const getPartPlugin = (partType: string): PartPlugin | undefined => {
  // 1. 首先尝试直接匹配
  if (partPlugins[partType]) {
    return partPlugins[partType];
  }
  
  // 2. 收集所有可以处理该类型的插件
  const candidates: PartPlugin[] = [];
  
  // 检查所有插件的 canHandle 函数
  for (const plugin of Object.values(partPlugins)) {
    if (plugin.canHandle && plugin.canHandle(partType)) {
      candidates.push(plugin);
    }
  }
  
  // 3. 如果有候选插件，按优先级排序并返回最高优先级的
  if (candidates.length > 0) {
    candidates.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    return candidates[0];
  }
  
  // 4. 兜底方案：模式匹配
  if (partType.startsWith('tool-')) {
    return partPlugins['__tool__'];
  }
  
  if (partType.startsWith('data-')) {
    return partPlugins['__data__'];
  }
  
  return undefined;
};

// 注册新的部分插件
export const registerPartPlugin = (type: string, plugin: PartPlugin): void => {
  partPlugins[type] = plugin;
};

// 注销插件
export const unregisterPartPlugin = (type: string): void => {
  delete partPlugins[type];
};

// 检查是否有插件可以处理特定类型
export const canHandlePartType = (partType: string): boolean => {
  return getPartPlugin(partType) !== undefined;
}; 