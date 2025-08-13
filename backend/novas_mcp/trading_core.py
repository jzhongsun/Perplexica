from enum import Enum
from typing import Annotated, List, Optional
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, ConfigDict, field_validator
import logging
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TradingReportResultPack(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    dataframe: Optional[pd.DataFrame] = Field(default=None, description="The dataframe of the report")
    markdown_table: Optional[str] = Field(default=None, description="The markdown of the report")
    json_dict: Optional[dict] = Field(default=None, description="The json of the report")
    
    @field_validator('dataframe')
    @classmethod
    def validate_dataframe(cls, v):
        if v is None:
            return v
        if not isinstance(v, pd.DataFrame):
            raise ValueError("dataframe must be a pandas DataFrame")
        return v

class TradingReportResult(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    reports: dict[str, TradingReportResultPack] = Field(description="A list of indicator names and their reports, each report is a markdown table")

class ReportDateType(str, Enum):
    BY_PERIOD = "by_period"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    
class MarketCode(str, Enum):
    SH = "SH"  # 上海证券交易所
    SZ = "SZ"  # 深圳证券交易所
    HK = "HK"  # 香港证券交易所
    US = "US"  # 美国股票

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
    market_code: MarketCode = Annotated[
        MarketCode, "The market code of provided stock symbol"
    ]
    symbol: str
    indicators: List[str]
    look_back_days: int


class RetrieveNamedReportItem(BaseModel):
    name: str = Field(description="The name of the report category")
    report_markdown_table: str = Field(
        description="The markdown table of the report data"
    )

class RetrieveStockStatsIndicatorsReportItem(BaseModel):
    indicator_name: str = Field(description="The name of the indicator")
    indicator_description: str = Field(description="The description of the indicator")
    indicator_report_markdown_table: str = Field(
        description="The markdown table of the indicator report"
    )

class RetrieveStockStatsIndicatorsReportResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    reports: List[RetrieveStockStatsIndicatorsReportItem] = Field(
        description="A list of indicator names and their reports"
    )


async def _retrieve_stock_stats_indicators_report(
    request: RetrieveStockStatsIndicatorsReportRequest,
) -> RetrieveStockStatsIndicatorsReportResponse:
    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }
        
    logger.info(f"Retrieving stock stats indicators report for {request}")
    from novas_mcp.trading.trading_em_stock import em_retrieve_stock_kline_data
    
    start_date = datetime.now() - timedelta(days=request.look_back_days)
    end_date = datetime.now()

    kline_data = await em_retrieve_stock_kline_data(
        request.market_code,
        request.symbol,
        "daily",
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )
    columns_mapping = {"date": "日期", "amount": "成交额", "close": "收盘", "high": "最高", "low": "最低", "volume": "成交量"}
    from stockstats import wrap
    kdf = kline_data.copy()
    for k, v in columns_mapping.items():
        kdf[k] = kdf[v]
    kdf = kdf[columns_mapping.keys()]
    sdf = wrap(kdf)
    
    reports = []
    for indicator in request.indicators:
        if indicator in best_ind_params:
            indicator_values = sdf[indicator]
            reports.append(
                    RetrieveStockStatsIndicatorsReportItem(
                        indicator_name=indicator, 
                        indicator_description=best_ind_params[indicator], 
                        indicator_report_markdown_table=indicator_values.to_markdown()
                    )
            )
        else:
            logger.warning(f"Indicator {indicator} not found in the data")
            reports.append(
                RetrieveStockStatsIndicatorsReportItem(
                    indicator_name=indicator, indicator_description=f"Indicator {indicator} not found in the data", indicator_report_markdown_table=""
                )
            )
    
    return RetrieveStockStatsIndicatorsReportResponse(
        success=len(reports) > 0,
        reports=reports,
    )
    

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(_retrieve_stock_stats_indicators_report(RetrieveStockStatsIndicatorsReportRequest(
#         market_code=MarketCode.SH,
#         symbol="603777",
#         indicators=["vwma"],
#         look_back_days=365,
#     )))

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
    market_code: MarketCode = Annotated[
        MarketCode, "The market code of provided stock symbol"
    ]
    symbol: str = Annotated[
        str, "The symbol of the stock to retrieve cash flow statement for"
    ]
    report_date_type: ReportDateType = Annotated[
        ReportDateType,
        "The type of the cash flow statement to retrieve, such as 'quarterly', 'annual' or 'by_period'",
    ]
    include_yoy: bool = Annotated[
        bool,
        "Whether to include year-over-year (YOY) indicators, default is False",
    ]
    look_back_years: int = Annotated[
        int,
        "The number of years to look back for the cash flow statement, default is 5",
    ]


class RetrieveCompanyBalanceSheetResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    error_message: Optional[str] = Field(default=None, description="The error message if the request is not successful")
    market_code: MarketCode = Field(description="The market code of provided stock symbol")
    symbol: str = Field(description="The symbol of the stock to retrieve cash flow statement for")
    report_date_type: ReportDateType = Field(description="The type of the cash flow statement to retrieve, such as 'quarterly', 'annual' or 'by_period'")
    look_back_years: int = Field(description="The number of years to look back for the cash flow statement, default is 5")
    reports: List[RetrieveNamedReportItem] = Field(
        description="A list of indicator names and their reports, each report is a markdown table"
    )


async def _retrieve_company_balance_sheet(
    request: RetrieveCompanyBalanceSheetRequest,
) -> RetrieveCompanyBalanceSheetResponse:
    logger.info(f"Retrieving company balance sheet for {request}")
    from novas_mcp.trading.trading_em_financial import em_retrieve_company_financial_analysis_balance_sheet
    try:
        balance_sheet = await em_retrieve_company_financial_analysis_balance_sheet(
            request.market_code,
            request.symbol,
            request.report_date_type,
            request.include_yoy,
            request.look_back_years,
        )
        return RetrieveCompanyBalanceSheetResponse(
            success=True,
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[
                RetrieveNamedReportItem(
                    name=category_name, 
                    report_markdown_table=report.markdown_table
                )
                for category_name, report in balance_sheet.items()
            ],
        )
    except Exception as e:
        logger.error(f"Error retrieving company balance sheet: {e}")
        return RetrieveCompanyBalanceSheetResponse(
            success=False,
            error_message=str(e),
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[],
        )

class RetrieveCompanyIncomeStatementRequest(BaseModel):
    market_code: MarketCode = Annotated[
        MarketCode, "The market code of provided stock symbol"
    ]
    symbol: str = Annotated[
        str, "The symbol of the stock to retrieve cash flow statement for"
    ]
    report_date_type: ReportDateType = Annotated[
        ReportDateType,
        "The type of the cash flow statement to retrieve, such as 'quarterly', 'annual' or 'by_period'",
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


class RetrieveCompanyIncomeStatementResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    error_message: Optional[str] = Field(default=None, description="The error message if the request is not successful")
    market_code: MarketCode = Field(description="The market code of provided stock symbol")
    symbol: str = Field(description="The symbol of the stock to retrieve cash flow statement for")
    report_date_type: ReportDateType = Field(description="The type of the cash flow statement to retrieve, such as 'quarterly', 'annual' or 'by_period'")
    look_back_years: int = Field(description="The number of years to look back for the cash flow statement, default is 5")
    reports: List[RetrieveNamedReportItem] = Field(
        description="A list of indicator names and their reports, each report is a markdown table"
    )

async def _retrieve_company_income_statement(
    request: RetrieveCompanyIncomeStatementRequest,
) -> RetrieveCompanyIncomeStatementResponse:
    logger.info(f"Retrieving company income statement for {request}")
    from novas_mcp.trading.trading_em_financial import em_retrieve_company_financial_analysis_income_statement
    
    try:

        income_statement = await em_retrieve_company_financial_analysis_income_statement(
            request.market_code,
            request.symbol,
            request.report_date_type,
            include_yoy=request.include_yoy,
            include_qoq=request.include_qoq,
            look_back_years=request.look_back_years,
        )
        return RetrieveCompanyIncomeStatementResponse(
            success=True,
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[
                RetrieveNamedReportItem(
                    name=indicator_name, report_markdown_table=report.markdown_table
                )
                for indicator_name, report in income_statement.items()
            ],
        )
    except Exception as e:
        logger.error(f"Error retrieving company income statement: {e}")
        return RetrieveCompanyIncomeStatementResponse(
            success=False,
            error_message=str(e),
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[],
        )


class RetrieveCompanyCashFlowStatementRequest(BaseModel):
    market_code: MarketCode = Annotated[
        MarketCode, "The market code of provided stock symbol"
    ]
    symbol: str = Annotated[
        str, "The symbol of the stock to retrieve cash flow statement for"
    ]
    report_date_type: ReportDateType = Annotated[
        ReportDateType,
        "The type of the cash flow statement to retrieve, such as 'quarterly', 'annual' or 'by_period'",
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
    error_message: Optional[str] = Field(default=None, description="The error message if the request is not successful")
    market_code: MarketCode = Field(description="The market code of provided stock symbol")
    symbol: str = Field(description="The symbol of the stock to retrieve cash flow statement for")
    report_date_type: ReportDateType = Field(description="The type of the cash flow statement to retrieve, such as 'quarterly', 'annual' or 'by_period'")
    look_back_years: int = Field(description="The number of years to look back for the cash flow statement, default is 5")
    reports: List[RetrieveNamedReportItem] = Field(
        description="A list of indicator names and their reports, each report is a markdown table"
    )


async def _retrieve_company_cash_flow_statement(
    request: RetrieveCompanyCashFlowStatementRequest,
) -> RetrieveCompanyCashFlowStatementResponse:
    logger.info(f"Retrieving company cash flow statement for {request}")
    from novas_mcp.trading.trading_em_financial import em_retrieve_company_financial_analysis_cash_flow_statement
    
    try:
        cash_flow_statement = await em_retrieve_company_financial_analysis_cash_flow_statement(
            request.market_code,
            request.symbol,
            request.report_date_type,
            request.include_yoy,
            request.include_qoq,
            request.look_back_years,
        )
        return RetrieveCompanyCashFlowStatementResponse(
            success=True,
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[
                RetrieveNamedReportItem(
                    name=indicator_name, report_markdown_table=report.markdown_table
                )
                for indicator_name, report in cash_flow_statement.items()
            ],
        )
    except Exception as e:
        logger.error(f"Error retrieving company cash flow statement: {e}")
        return RetrieveCompanyCashFlowStatementResponse(
            success=False,
            error_message=str(e),
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[],
        )


class RetrieveCompanyFinancialAnalysisIndicatorsRequest(BaseModel):
    market_code: MarketCode = Annotated[
        MarketCode, "The market code of provided stock symbol"
    ]
    symbol: str
    report_date_type: ReportDateType
    look_back_years: int


class RetrieveCompanyFinancialAnalysisIndicatorsResponse(BaseModel):
    success: bool = Field(description="Whether the request is successful")
    error_message: Optional[str] = Field(default=None, description="The error message if the request is not successful")
    market_code: MarketCode = Field(
        description="The market code of provided stock symbol"
    )
    symbol: str = Field(
        description="The symbol of the stock to retrieve financial analysis indicators for"
    )
    report_date_type: ReportDateType = Field(
        description="The type of the financial analysis indicators to retrieve, such as 'quarterly', 'annual' or 'by_period'"
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
    from novas_mcp.trading.trading_em_financial import em_retrieve_company_financial_analysis_indicators
    
    try:
        reports = await em_retrieve_company_financial_analysis_indicators(
            request.market_code,
            request.symbol,
                request.report_date_type,
                request.look_back_years,
            )
        return RetrieveCompanyFinancialAnalysisIndicatorsResponse(
            success=True,
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[
                RetrieveNamedReportItem(
                    name=indicator_name, 
                    report_markdown_table=report.markdown_table
                )
                for indicator_name, report in reports.items()
            ],
        )
        
    except Exception as e:
        logger.error(f"Error retrieving company financial analysis indicators: {e}")
        return RetrieveCompanyFinancialAnalysisIndicatorsResponse(
            success=False,
            error_message=str(e),
            market_code=request.market_code,
            symbol=request.symbol,
            report_date_type=request.report_date_type,
            look_back_years=request.look_back_years,
            reports=[],
        )
    
    

class RetrieveCompanyFundamentalsRequest(BaseModel):
    market_code: MarketCode = Annotated[
        MarketCode, "The market code of provided stock symbol"
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
