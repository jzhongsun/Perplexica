from enum import Enum
from typing import Annotated, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReportDateType(str, Enum):
    BY_PERIOD = "by_period"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MarketType(str, Enum):
    A_SHARE = "a_share"  # 上海证券交易所
    B_SHARE = "b_share"  # 深圳证券交易所
    H_SHARE = "h_share"  # 深圳证券交易所
    US_STOCKS = "us_stocks"  # 美国股票


class RetrieveCompanyNewsRequest(BaseModel):
    company_name: str
    language: str = "en"
    num_results: int = 10
    start_date: Optional[str] = Field(
        default=datetime.now().isoformat(),
        description="The start date of the news to retrieve, format: YYYY-mm-dd",
    )
    end_date: Optional[str] = Field(
        default=datetime.now().isoformat(),
        description="The end date of the news to retrieve, format: YYYY-mm-dd",
    )


class RetrieveCompanyNewsResponse(BaseModel):
    news: List[str]


async def _retrieve_company_news(
    request: RetrieveCompanyNewsRequest,
) -> RetrieveCompanyNewsResponse:
    logger.info(f"Retrieving financial news for {request}")
    return RetrieveCompanyNewsResponse(news=["Financial news"])


class RetrieveStockPriceDataRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str = Field(
        default=datetime.now().isoformat(),
        description="The end date of the price data to retrieve, format: YYYY-mm-dd",
    )


class RetrieveStockPriceDataResponse(BaseModel):
    price: float


async def _retrieve_stock_price_data(
    request: RetrieveStockPriceDataRequest,
) -> RetrieveStockPriceDataResponse:
    logger.info(f"Retrieving stock price data for {request}")
    return RetrieveStockPriceDataResponse(price=100)


class RetrieveStockStatsIndicatorsReportRequest(BaseModel):
    market_type: MarketType = Annotated[
        MarketType, "The market type of provided stock symbol"
    ]
    symbol: str
    report_period_type: ReportDateType
    look_back_years: int


class RetrieveNamedReportItem(BaseModel):
    indicator_name: str = Field(description="The name of the indicator")
    indicator_report_markdown_table: str = Field(
        description="The markdown table of the indicator report"
    )


class RetrieveStockStatsIndicatorsReportResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    reports: List[RetrieveNamedReportItem] = Field(
        description="A list of indicator names and their reports"
    )


async def _retrieve_stock_stats_indicators_report(
    request: RetrieveStockStatsIndicatorsReportRequest,
) -> RetrieveStockStatsIndicatorsReportResponse:
    logger.info(f"Retrieving stock stats indicators report for {request}")
    from novas_mcp.trading.trading_em import em_retrieve_company_financial_analysis_indicators

    reports = await em_retrieve_company_financial_analysis_indicators(
        request.market_type,
        request.symbol,
        request.report_period_type,
        request.look_back_years,
    )
    return RetrieveStockStatsIndicatorsReportResponse(
        success=reports["success"],
        reports=[
            RetrieveNamedReportItem(
                indicator_name=indicator_name, indicator_report_markdown_table=report
            )
            for indicator_name, report in reports["reports"].items()
        ],
    )


class RetrieveCompanyInsiderSentimentRequest(BaseModel):
    symbol: str
    current_date: str


class RetrieveCompanyInsiderSentimentResponse(BaseModel):
    sentiment: str


async def _retrieve_company_insider_sentiment(
    request: RetrieveCompanyInsiderSentimentRequest,
) -> RetrieveCompanyInsiderSentimentResponse:
    logger.info(f"Retrieving company insider sentiment for {request}")
    return RetrieveCompanyInsiderSentimentResponse(
        sentiment="Company insider sentiment"
    )


class RetrieveCompanyInsiderTransactionsRequest(BaseModel):
    symbol: str
    current_date: str


class RetrieveCompanyInsiderTransactionsResponse(BaseModel):
    transactions: str


async def _retrieve_company_insider_transactions(
    request: RetrieveCompanyInsiderTransactionsRequest,
) -> RetrieveCompanyInsiderTransactionsResponse:
    logger.info(f"Retrieving company insider transactions for {request}")
    return RetrieveCompanyInsiderTransactionsResponse(
        transactions="Company insider transactions"
    )


class RetrieveCompanyBalanceSheetRequest(BaseModel):
    symbol: str
    current_date: str


class RetrieveCompanyBalanceSheetResponse(BaseModel):
    balance_sheet: str


async def _retrieve_company_balance_sheet(
    request: RetrieveCompanyBalanceSheetRequest,
) -> RetrieveCompanyBalanceSheetResponse:
    logger.info(f"Retrieving company balance sheet for {request}")
    return RetrieveCompanyBalanceSheetResponse(balance_sheet="Company balance sheet")


class RetrieveCompanyIncomeStatementRequest(BaseModel):
    symbol: str
    current_date: str


class RetrieveCompanyIncomeStatementResponse(BaseModel):
    income_statement: str


async def _retrieve_company_income_statement(
    request: RetrieveCompanyIncomeStatementRequest,
) -> RetrieveCompanyIncomeStatementResponse:
    logger.info(f"Retrieving company income statement for {request}")
    return RetrieveCompanyIncomeStatementResponse(
        income_statement="Company income statement"
    )


class RetrieveCompanyCashFlowStatementRequest(BaseModel):
    market_type: MarketType = Annotated[
        MarketType, "The market type of provided stock symbol"
    ]
    symbol: str = Annotated[
        str, "The symbol of the stock to retrieve cash flow statement for"
    ]
    report_date_type: ReportDateType = Annotated[
        ReportDateType,
        "The type of the cash flow statement to retrieve, such as 'quarterly', 'yearly' or 'report_period'",
    ]
    include_yoy: bool = Annotated[
        bool,
        "Whether to include year-over-year (YOY) indicators, default is False",
    ]
    include_qoq: bool = Annotated[
        bool,
        "Whether to include quarter-over-quarter (QOQ) indicators, default is False",
    ]
    look_back_years: int = Annotated[
        int,
        "The number of years to look back for the cash flow statement, default is 5",
    ]


class RetrieveCompanyCashFlowStatementResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    market_type: MarketType = Field(description="The market type of provided stock symbol")
    symbol: str = Field(description="The symbol of the stock to retrieve cash flow statement for")
    report_date_type: ReportDateType = Field(description="The type of the cash flow statement to retrieve, such as 'quarterly', 'yearly' or 'report_period'")
    look_back_years: int = Field(description="The number of years to look back for the cash flow statement, default is 5")
    reports: List[RetrieveNamedReportItem] = Field(
        description="A list of indicator names and their reports, each report is a markdown table"
    )


async def _retrieve_company_cash_flow_statement(
    request: RetrieveCompanyCashFlowStatementRequest,
) -> RetrieveCompanyCashFlowStatementResponse:
    logger.info(f"Retrieving company cash flow statement for {request}")
    from novas_mcp.trading.trading_em import em_retrieve_company_financial_analysis_cash_flow_statement

    cash_flow_statement = await em_retrieve_company_financial_analysis_cash_flow_statement(
        request.market_type,
        request.symbol,
        request.report_date_type,
        request.include_yoy,
        request.include_qoq,
        request.look_back_years,
    )
    return RetrieveCompanyCashFlowStatementResponse(
        success=cash_flow_statement["success"],
        market_type=request.market_type,
        symbol=request.symbol,
        report_date_type=request.report_date_type,
        look_back_years=request.look_back_years,
        reports=[
            RetrieveNamedReportItem(
                indicator_name=indicator_name, indicator_report_markdown_table=report
            )
            for indicator_name, report in cash_flow_statement.items()
        ],
    )


class RetrieveCompanyFinancialAnalysisIndicatorsRequest(BaseModel):
    market_type: MarketType = Annotated[
        MarketType, "The market type of provided stock symbol"
    ]
    symbol: str
    report_period_type: ReportDateType
    look_back_years: int


class RetrieveCompanyFinancialAnalysisIndicatorsResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    market_type: MarketType = Field(
        description="The market type of provided stock symbol"
    )
    symbol: str = Field(
        description="The symbol of the stock to retrieve financial analysis indicators for"
    )
    report_period_type: ReportDateType = Field(
        description="The type of the financial analysis indicators to retrieve, such as 'quarterly', 'yearly' or 'report_period'"
    )
    look_back_years: int = Field(
        description="The number of years to look back for the financial analysis indicators, default is 2"
    )
    reports: List[RetrieveNamedReportItem] = Field(
        description="A list of indicator names and their reports"
    )


async def _retrieve_company_financial_analysis_indicators(
    request: RetrieveCompanyFinancialAnalysisIndicatorsRequest,
) -> RetrieveCompanyFinancialAnalysisIndicatorsResponse:
    logger.info(f"Retrieving company financial analysis indicators for {request}")
    from novas_mcp.trading.trading_em import em_retrieve_company_financial_analysis_indicators

    reports = await em_retrieve_company_financial_analysis_indicators(
        request.market_type,
        request.symbol,
        request.report_period_type,
        request.look_back_years,
    )
    return RetrieveCompanyFinancialAnalysisIndicatorsResponse(
        success=reports["success"],
        market_type=request.market_type,
        symbol=request.symbol,
        report_period_type=request.report_period_type,
        look_back_years=request.look_back_years,
        reports=[
            RetrieveNamedReportItem(
                indicator_name=indicator_name, indicator_report_markdown_table=report
            )
            for indicator_name, report in reports["reports"].items()
        ],
    )


class RetrieveCompanyFundamentalsRequest(BaseModel):
    market_type: MarketType = Annotated[
        MarketType, "The market type of provided stock symbol"
    ]
    symbol: str
    current_date: str


class RetrieveCompanyFundamentalsResponse(BaseModel):
    fundamentals: str


async def _retrieve_company_fundamentals(
    request: RetrieveCompanyFundamentalsRequest,
) -> RetrieveCompanyFundamentalsResponse:
    logger.info(f"Retrieving company fundamentals for {request}")
    return RetrieveCompanyFundamentalsResponse(fundamentals="Company fundamentals")
