from typing import Annotated
from datetime import datetime

from .trading_core import (
    MarketCode,
    ReportDateType,
    RetrieveCompanyFundamentalsRequest,
    RetrieveCompanyFundamentalsResponse,
    RetrieveCompanyInsiderSentimentRequest,
    RetrieveCompanyInsiderSentimentResponse,
    RetrieveCompanyNewsRequest,
    RetrieveCompanyNewsResponse,
    RetrieveCompanyInsiderTransactionsRequest,
    RetrieveCompanyInsiderTransactionsResponse,
    RetrieveCompanyBalanceSheetRequest,
    RetrieveCompanyBalanceSheetResponse,
    RetrieveCompanyIncomeStatementRequest,
    RetrieveCompanyIncomeStatementResponse,
    RetrieveCompanyCashFlowStatementRequest,
    RetrieveCompanyCashFlowStatementResponse,
    RetrieveStockKlineDataRequest,
    RetrieveStockKlineDataResponse,
    RetrieveStockStatsIndicatorsReportRequest,
    RetrieveStockStatsIndicatorsReportResponse,
    _retrieve_company_cash_flow_statement,
    _retrieve_company_fundamentals,
    _retrieve_company_balance_sheet,
    _retrieve_company_income_statement,
    _retrieve_company_insider_transactions,
    _retrieve_company_insider_sentiment,
    _retrieve_company_news,
    _retrieve_stock_kline_data,
    _retrieve_stock_stats_indicators_report,
    _retrieve_company_financial_analysis_indicators,
    RetrieveCompanyFinancialAnalysisIndicatorsRequest,
    RetrieveCompanyFinancialAnalysisIndicatorsResponse,
)
from mcp.server.fastmcp import FastMCP
import logging
from pydantic import Field, BaseModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_trading_mcp_server(mcp: FastMCP):
    @mcp.tool(
        name="retrieve_company_news",
        description="Retrieve financial news for a company",
    )
    async def retrieve_company_news(
        company_name: Annotated[
            str, Field(description="The name of the company to retrieve financial news for")
        ],
        language: Annotated[
            str, Field(description="The language of the news to retrieve, e.g. en, fr, de, etc.")
        ] = "en",
        num_results: Annotated[int, Field(description="The number of results to retrieve")] = 10,
        start_date: Annotated[
            str, Field(description="The start date of the news to retrieve, format: YYYY-mm-dd")
        ] = datetime.now().isoformat(),
        end_date: Annotated[
            str, Field(description="The end date of the news to retrieve, format: YYYY-mm-dd")
        ] = datetime.now().isoformat(),
    ) -> RetrieveCompanyNewsResponse:
        request = RetrieveCompanyNewsRequest(
            company_name=company_name,
            language=language,
            num_results=num_results,
            start_date=start_date,
            end_date=end_date,
        )
        return await _retrieve_company_news(request)

    @mcp.tool(
        name="retrieve_stock_historical_data",
        description="Retrieve stock historical data for a company",
    )
    async def retrieve_stock_historical_data(
        market_code: Annotated[MarketCode, Field(description="The market code of the stock symbol, available values are 'SH' and 'SZ'")],
        symbol: Annotated[str, Field(description="The ticker symbol of the stock to retrieve price data for")],
        interval: Annotated[str, Field(description="The interval of the historical data to retrieve, available values are 'daily', 'weekly' or 'monthly'")],
        start_date: Annotated[
            str, Field(description="The start date of the historical data to retrieve, format: YYYY-mm-dd")
        ] = datetime.now().isoformat(),
        end_date: Annotated[
            str, Field(description="The end date of the historical data to retrieve, format: YYYY-mm-dd")
        ] = datetime.now().isoformat(),
    ) -> RetrieveStockKlineDataResponse:
        logger.info(
            f"Retrieving stock historical data for {market_code.value}{symbol} from {start_date} to {end_date}"
        )
        request = RetrieveStockKlineDataRequest(
            market_code=market_code,
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
        )
        return await _retrieve_stock_kline_data(request)

    @mcp.tool(
        name="retrieve_stockstats_indicators_report",
        description="Retrieve stock stats indicators report for a company",
    )
    async def retrieve_stockstats_indicators_report(
        market_code: Annotated[MarketCode, Field(description="The market code of the stock symbol, available values are 'SH' and 'SZ'")],
        symbol: Annotated[str, Field(description="The ticker symbol of the stock to retrieve price data for")],
        indicators: Annotated[list[str], Field(description="The indicators to retrieve, only support values: 'close_50_sma', 'close_200_sma', 'close_10_ema', 'macd', 'macds', 'macdh', 'rsi', 'boll', 'boll_ub', 'boll_lb', 'atr', 'vwma', 'mfi'")],
        look_back_days: Annotated[int, Field(description="how many days to look back, default is 180")] = Field(default=180, description="how many days to look back, default is 180"),
    ) -> RetrieveStockStatsIndicatorsReportResponse:
        logger.info(f"Retrieving stock stats indicators report for {symbol}")
        request = RetrieveStockStatsIndicatorsReportRequest(
            market_code=market_code,
            symbol=symbol,
            indicators=indicators,
            look_back_days=look_back_days,
        )
        return await _retrieve_stock_stats_indicators_report(request)

    # @mcp.tool(
    #     name="retrieve_company_insider_sentiment",
    #     description="Retrieve company insider sentiment for a company",
    # )
    async def retrieve_company_insider_sentiment(
        symbol: Annotated[
            str, Field(description="The symbol of the stock to retrieve insider sentiment for")
        ],
        current_date: Annotated[
            str, Field(description="The current trading date you are trading on, YYYY-mm-dd")
        ],
    ) -> RetrieveCompanyInsiderSentimentResponse:
        logger.info(f"Retrieving company insider sentiment for {symbol}")
        request = RetrieveCompanyInsiderSentimentRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_insider_sentiment(request)

    # @mcp.tool(
    #     name="retrieve_company_insider_transactions",
    #     description="Retrieve company insider transactions for a company",
    # )
    async def retrieve_company_insider_transactions(
        symbol: Annotated[
            str, Field(description="The ticker symbol of the stock to retrieve insider transactions for")
        ],
        current_date: Annotated[
            str, Field(description="The current trading date you are trading on, YYYY-mm-dd")
        ],
    ) -> RetrieveCompanyInsiderTransactionsResponse:
        logger.info(f"Retrieving company insider transactions for {symbol}")
        request = RetrieveCompanyInsiderTransactionsRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_insider_transactions(request)

    @mcp.tool(
        name="retrieve_financial_balance_sheet",
        description="Retrieve company balance sheet for a company",
    )
    async def retrieve_financial_balance_sheet(
        market_code: Annotated[MarketCode, Field(description="The market code of the stock symbol, available values are 'SH' and 'SZ'")],
        symbol: Annotated[str, Field(description="The ticker symbol of the stock to retrieve balance sheet for")],
        report_date_type: Annotated[ReportDateType, Field(description="The type of the cash flow statement to retrieve, available values are 'by_period' or 'annual'")],
        include_yoy: Annotated[bool, Field(description="Whether to include year-over-year (YOY) indicators, default is False")] = False,
        look_back_years: Annotated[int, Field(description="The number of years to look back for the cash flow statement, default is 2")] = 2,
    ) -> RetrieveCompanyBalanceSheetResponse:
        logger.info(f"Retrieving company balance sheet for {symbol}")
        request = RetrieveCompanyBalanceSheetRequest(
            market_code=market_code,
            symbol=symbol,
            report_date_type=report_date_type,
            include_yoy=include_yoy,
            look_back_years=look_back_years,
        )
        return await _retrieve_company_balance_sheet(request)

    @mcp.tool(
        name="retrieve_financial_income_statement",
        description="Retrieve company financial income statement for a company",
    )
    async def retrieve_financial_income_statement(
        market_code: Annotated[MarketCode, Field(description="The market code of the stock symbol, available values are 'SH' and 'SZ'")],
        symbol: Annotated[
            str, Field(description="The ticker symbol of the stock to retrieve income statement for")
        ],
        report_date_type: Annotated[ReportDateType, Field(description="The type of the cash flow statement to retrieve, available values are 'by_period', 'quarterly' or 'annual'")],
        include_yoy: Annotated[bool, Field(description="Whether to include year-over-year (YOY) indicators, default is False")],
        include_qoq: Annotated[bool, Field(description="Whether to include quarter-over-quarter (QOQ) indicators, default is False")],
        look_back_years: Annotated[int, Field(description="The number of years to look back for the cash flow statement, default is 5")],
    ) -> RetrieveCompanyIncomeStatementResponse:
        logger.info(f"Retrieving company income statement for {symbol}")
        request = RetrieveCompanyIncomeStatementRequest(
            market_code=market_code,
            symbol=symbol,
            report_date_type=report_date_type,
            include_yoy=include_yoy,
            include_qoq=include_qoq,
            look_back_years=look_back_years,
        )
        return await _retrieve_company_income_statement(request)

    @mcp.tool(
        name="retrieve_financial_cash_flow_statement",
        description="Retrieve company financial cash flow statement for a company",
    )
    async def retrieve_financial_cash_flow_statement(
        market_code: Annotated[MarketCode, Field(description="The market code of the stock symbol, available values are 'SH' and 'SZ'")],
        symbol: Annotated[
            str, Field(description="The ticker symbol of the stock to retrieve cash flow statement for")
        ],
        report_date_type: Annotated[ReportDateType, Field(description="The type of the cash flow statement to retrieve, available values are 'by_period', 'quarterly' or 'annual'")],
        include_yoy: Annotated[bool, Field(description="Whether to include year-over-year (YOY) indicators, only available when report_date_type is 'by_period' or 'annual', default is False")] = False,
        include_qoq: Annotated[bool, Field(description="Whether to include quarter-over-quarter (QOQ) indicators, only available when report_date_type is 'quarterly', default is False")] = False,
        look_back_years: Annotated[int, Field(description="The number of years to look back for the cash flow statement, default is 3")] = 3,
    ) -> RetrieveCompanyCashFlowStatementResponse:
        logger.info(f"Retrieving company cash flow statement for {symbol}")
        request = RetrieveCompanyCashFlowStatementRequest(
            market_code=market_code,
            symbol=symbol,
            report_date_type=report_date_type,
            include_yoy=include_yoy,
            include_qoq=include_qoq,
            look_back_years=look_back_years,
        )
        return await _retrieve_company_cash_flow_statement(request)
    
    @mcp.tool(
        name="retrieve_financial_analysis_indicators",
        description="Retrieve company financial analysis indicators for a company",
    )
    async def retrieve_financial_analysis_indicators(
        market_code: Annotated[MarketCode, Field(description="The market code of the stock symbol, available values are 'SH' and 'SZ'")],
        symbol: Annotated[str, Field(description="The ticker symbol of the stock to retrieve financial analysis indicators for")],
        report_date_type: Annotated[ReportDateType, Field(description="The type of the financial analysis indicators to retrieve, available values are 'by_period', 'quarterly' or 'annual'")],
        look_back_years: Annotated[
            int, Field(description="The number of years to look back for the financial analysis indicators, default is 2")
        ] = 2,
    ) -> RetrieveCompanyFinancialAnalysisIndicatorsResponse:
        logger.info(f"Retrieving company financial analysis indicators for {symbol}")
        request = RetrieveCompanyFinancialAnalysisIndicatorsRequest(
            market_code=market_code,
            symbol=symbol,
            report_date_type=report_date_type,
            look_back_years=look_back_years,
        )
        return await _retrieve_company_financial_analysis_indicators(request)

    # @mcp.tool(
    #     name="retrieve_company_fundamentals",
    #     description="Retrieve company fundamentals for a company",
    # )
    async def retrieve_company_fundamentals(
        symbol: Annotated[str, Field(description="The ticker symbol of the stock to retrieve fundamentals for")],
        current_date: Annotated[
            str, Field(description="The current trading date you are trading on, YYYY-mm-dd")
        ],
    ) -> RetrieveCompanyFundamentalsResponse:
        logger.info(f"Retrieving company fundamentals for {symbol}")
        request = RetrieveCompanyFundamentalsRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_fundamentals(request)

