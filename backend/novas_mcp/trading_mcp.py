from typing import Annotated
from datetime import datetime

from .trading_core import (
    MarketType,
    ReportPeriodType,
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
    RetrieveStockPriceDataRequest,
    RetrieveStockPriceDataResponse,
    RetrieveStockStatsIndicatorsReportRequest,
    RetrieveStockStatsIndicatorsReportResponse,
    _retrieve_company_cash_flow_statement,
    _retrieve_company_fundamentals,
    _retrieve_company_balance_sheet,
    _retrieve_company_income_statement,
    _retrieve_company_insider_transactions,
    _retrieve_company_insider_sentiment,
    _retrieve_company_news,
    _retrieve_stock_price_data,
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
            str, "The name of the company to retrieve financial news for"
        ],
        language: Annotated[
            str, "The language of the news to retrieve, e.g. en, fr, de, etc."
        ] = "en",
        num_results: Annotated[int, "The number of results to retrieve"] = 10,
        start_date: Annotated[
            str, "The start date of the news to retrieve, format: YYYY-mm-dd"
        ] = datetime.now().isoformat(),
        end_date: Annotated[
            str, "The end date of the news to retrieve, format: YYYY-mm-dd"
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
        name="retrieve_stock_price_data",
        description="Retrieve stock price data for a company",
    )
    async def retrieve_stock_price_data(
        symbol: Annotated[str, "The symbol of the stock to retrieve price data for"],
        start_date: Annotated[
            str, "The start date of the price data to retrieve, format: YYYY-mm-dd"
        ] = datetime.now().isoformat(),
        end_date: Annotated[
            str, "The end date of the price data to retrieve, format: YYYY-mm-dd"
        ] = datetime.now().isoformat(),
    ) -> RetrieveStockPriceDataResponse:
        logger.info(
            f"Retrieving stock price data for {symbol} from {start_date} to {end_date}"
        )
        request = RetrieveStockPriceDataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        return await _retrieve_stock_price_data(request)

    @mcp.tool(
        name="retrieve_stockstats_indicators_report",
        description="Retrieve stock stats indicators report for a company",
    )
    async def retrieve_stockstats_indicators_report(
        market_type: Annotated[MarketType, "The market type of the stock symbol"],
        symbol: Annotated[str, "The symbol of the stock to retrieve price data for"],
        report_period_type: Annotated[ReportPeriodType, "The type of the report to retrieve, such as 'quarterly', 'yearly' or 'report_period'"],
        look_back_years: Annotated[int, "how many years to look back, default is 3"] = Field(default=3, description="how many years to look back, default is 3"),
    ) -> RetrieveStockStatsIndicatorsReportResponse:
        logger.info(f"Retrieving stock stats indicators report for {symbol}")
        request = RetrieveStockStatsIndicatorsReportRequest(
            market_type=market_type,
            symbol=symbol,
            report_period_type=report_period_type,
            look_back_years=look_back_years,
        )
        return await _retrieve_stock_stats_indicators_report(request)

    @mcp.tool(
        name="retrieve_company_insider_sentiment",
        description="Retrieve company insider sentiment for a company",
    )
    async def retrieve_company_insider_sentiment(
        symbol: Annotated[
            str, "The symbol of the stock to retrieve insider sentiment for"
        ],
        current_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
    ) -> RetrieveCompanyInsiderSentimentResponse:
        logger.info(f"Retrieving company insider sentiment for {symbol}")
        request = RetrieveCompanyInsiderSentimentRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_insider_sentiment(request)

    @mcp.tool(
        name="retrieve_company_insider_transactions",
        description="Retrieve company insider transactions for a company",
    )
    async def retrieve_company_insider_transactions(
        symbol: Annotated[
            str, "The symbol of the stock to retrieve insider transactions for"
        ],
        current_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
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
        symbol: Annotated[str, "The symbol of the stock to retrieve balance sheet for"],
        current_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
    ) -> RetrieveCompanyBalanceSheetResponse:
        logger.info(f"Retrieving company balance sheet for {symbol}")
        request = RetrieveCompanyBalanceSheetRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_balance_sheet(request)

    @mcp.tool(
        name="retrieve_financial_income_statement",
        description="Retrieve company financial income statement for a company",
    )
    async def retrieve_financial_income_statement(
        symbol: Annotated[
            str, "The symbol of the stock to retrieve income statement for"
        ],
        current_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
    ) -> RetrieveCompanyIncomeStatementResponse:
        logger.info(f"Retrieving company income statement for {symbol}")
        request = RetrieveCompanyIncomeStatementRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_income_statement(request)

    @mcp.tool(
        name="retrieve_financial_cash_flow_statement",
        description="Retrieve company financial cash flow statement for a company",
    )
    async def retrieve_financial_cash_flow_statement(
        symbol: Annotated[
            str, "The symbol of the stock to retrieve cash flow statement for"
        ],
        current_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
    ) -> RetrieveCompanyCashFlowStatementResponse:
        logger.info(f"Retrieving company cash flow statement for {symbol}")
        request = RetrieveCompanyCashFlowStatementRequest(
            symbol=symbol,
            date=current_date,
        )
        return await _retrieve_company_cash_flow_statement(request)
    
    @mcp.tool(
        name="retrieve_financial_analysis_indicators",
        description="Retrieve company financial analysis indicators for a company",
    )
    async def retrieve_financial_analysis_indicators(
        market_type: Annotated[MarketType, "The market type of the stock symbol"],
        symbol: Annotated[str, "The symbol of the stock to retrieve financial analysis indicators for"],
        report_period_type: Annotated[ReportPeriodType, "The type of the financial analysis indicators to retrieve, such as 'quarterly', 'yearly' or 'report_period'"],
        look_back_years: Annotated[
            int, "The number of years to look back for the financial analysis indicators, default is 2"
        ],
    ) -> RetrieveCompanyFinancialAnalysisIndicatorsResponse:
        logger.info(f"Retrieving company financial analysis indicators for {symbol}")
        request = RetrieveCompanyFinancialAnalysisIndicatorsRequest(
            market_type=market_type,
            symbol=symbol,
            report_period_type=report_period_type,
            look_back_years=look_back_years,
        )
        return await _retrieve_company_financial_analysis_indicators(request)

    @mcp.tool(
        name="retrieve_company_fundamentals",
        description="Retrieve company fundamentals for a company",
    )
    async def retrieve_company_fundamentals(
        symbol: Annotated[str, "The symbol of the stock to retrieve fundamentals for"],
        current_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
    ) -> RetrieveCompanyFundamentalsResponse:
        logger.info(f"Retrieving company fundamentals for {symbol}")
        request = RetrieveCompanyFundamentalsRequest(
            symbol=symbol,
            current_date=current_date,
        )
        return await _retrieve_company_fundamentals(request)

