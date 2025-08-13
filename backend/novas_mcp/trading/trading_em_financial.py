import asyncio
import httpx
from novas_mcp.utils import format_pd_dataframe_to_markdown
from novas_mcp.trading_core import MarketCode, ReportDateType, TradingReportResultPack
import pandas as pd
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

EM_HTTP_HEADERS_DEFAULT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

async def em_retrieve_company_financial_analysis_indicators(
    market_code: MarketCode,
    symbol: str,
    report_period_type: ReportDateType,
    look_back_years: int,
) -> dict[str, TradingReportResultPack]:
    """
    获取股票财务分析指标，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#zyzb-0
    Args:
        market_code: 市场类型
        symbol: 股票代码
        report_period_type: 报告期类型
        look_back_years: 回溯年数

    """

    security_code = symbol.replace(".", "").replace("SH", "").replace("SZ", "")
    if market_code == MarketCode.SH:
        symbol = "SH" + security_code
    elif market_code == MarketCode.SZ:
        symbol = "SZ" + security_code

    def get_financial_indicator_mapping(report_period_type: ReportDateType) -> dict[str, str]:
        return {
            # 每股指标
            "EPSJB": (
                "摊薄每股收益(元)"
                if report_period_type == ReportDateType.QUARTERLY
                else "基本每股收益(元)"
            ),
            "EPSKCJB": "扣非每股收益(元)",
            "EPSXS": "稀释每股收益(元)",
            "BPS": "每股净资产(元)",
            "MGZBGJ": "每股公积金(元)",
            "MGWFPLR": "每股未分配利润(元)",
            "MGJYXJJE": "每股经营现金流(元)",
            "PER_CAPITAL_RESERVE": "每股公积金(元)",
            "PER_UNASSIGN_PROFIT": "每股未分配利润(元)",
            "PER_NETCASH": "每股经营现金流(元)",
            # 成长能力指标
            "TOTALOPERATEREVE": "营业总收入(元)",
            "MLR": "毛利润(元)",
            "GROSS_PROFIT": "毛利润(元)",
            "PARENTNETPROFIT": "归属净利润(元)",
            "KCFJCXSYJLR": "扣非净利润(元)",
            "DEDU_PARENT_PROFIT": "扣非净利润(元)",
            "TOTALOPERATEREVETZ": "营业总收入同比增长(%)",
            "PARENTNETPROFITTZ": "归属净利润同比增长(%)",
            "KCFJCXSYJLRTZ": "扣非净利润同比增长(%)",
            "DPNP_YOY_RATIO": "扣非净利润同比增长(%)",
            "YYZSRGDHBZC": "营业总收入滚动环比增长(%)",
            "NETPROFITRPHBZC": "归属净利润滚动环比增长(%)",
            "KFJLRGDHBZC": "扣非净利润滚动环比增长(%)",
            # 盈利能力指标
            "ROEJQ": "净资产收益率(加权)(%)",
            "ROE_DILUTED": "摊薄净资产收益率(%)",
            "ROEKCJQ": "净资产收益率(扣非/加权)(%)",
            "ZZCJLL": "总资产收益率(加权)(%)",
            "XSMLL": "毛利率(%)",
            "XSJLL": "净利率(%)",
            "JROA": "摊薄总资产收益率(%)",
            "GROSS_PROFIT_RATIO": "毛利率(%)",
            "NET_PROFIT_RATIO": "净利率(%)",
            # 收益质量指标
            "YSZKYYSR": "预收账款/营业总收入",
            "XSJXLYYSR": "销售净现金流/营业总收入",
            "JYXJLYYSR": "经营净现金流/营业总收入",
            "TAXRATE": "实际税率(%)",
            # 财务风险指标
            "LD": "流动比率",
            "SD": "速动比率",
            "XJLLB": "现金流量比率",
            "ZCFZL": "资产负债率(%)",
            "QYCS": "权益乘数",
            "CQBL": "产权比率",
            # 营运能力指标
            "ZZCZZTS": "总资产周转天数(天)",
            "CHZZTS": "存货周转天数(天)",
            "YSZKZZTS": "应收账款周转天数(天)",
            "TOAZZL": "总资产周转率(次)",
            "CHZZL": "存货周转率(次)",
            "YSZKZZL": "应收账款周转率(次)",
        }

    def get_financial_indicator_categories() -> dict[str, list[str]]:
        """财务指标分类 - 基于akshare实际列名"""
        return {
            "每股指标": [
                "EPSJB",
                "EPSKCJB",
                "EPSXS",
                "BPS",
                "MGZBGJ",
                "MGWFPLR",
                "MGJYXJJE",
                "PER_CAPITAL_RESERVE",
                "PER_UNASSIGN_PROFIT",
                "PER_NETCASH",
            ],
            "成长能力指标": [
                "TOTALOPERATEREVE",
                "MLR",
                "GROSS_PROFIT",
                "PARENTNETPROFIT",
                "KCFJCXSYJLR",
                "DEDU_PARENT_PROFIT",
                "TOTALOPERATEREVETZ",
                "PARENTNETPROFITTZ",
                "KCFJCXSYJLRTZ",
                "DPNP_YOY_RATIO",
                "YYZSRGDHBZC",
                "NETPROFITRPHBZC",
                "KFJLRGDHBZC",
            ],
            "盈利能力指标": [
                "ROEJQ",
                "ROEKCJQ",
                "ZZCJLL",
                "XSMLL",
                "XSJLL",
                "ROE_DILUTED",
                "JROA",
                "GROSS_PROFIT_RATIO",
                "NET_PROFIT_RATIO",
            ],
            "收益质量指标": ["YSZKYYSR", "XSJXLYYSR", "JYXJLYYSR", "TAXRATE"],
            "财务风险指标": ["LD", "SD", "XJLLB", "ZCFZL", "QYCS", "CQBL"],
            "营运能力指标": [
                "ZZCZZTS",
                "CHZZTS",
                "YSZKZZTS",
                "TOAZZL",
                "CHZZL",
                "YSZKZZL",
            ],
        }

    def create_category_dataframes(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """将财务数据按分类分拆成多个DataFrame"""
        categories = get_financial_indicator_categories()
        category_dataframes = {}
        for category_name, indicators in categories.items():
            # 获取该分类下存在的指标
            available_indicators = [
                indicator for indicator in indicators if indicator in df.columns
            ]
            # print(f'{category_name} - \n{indicators} - \n{available_indicators}')
            if available_indicators:
                # 创建该分类的DataFrame
                final_columns = ["REPORT_DATE_NAME"] + available_indicators
                category_df = df[final_columns].copy()
                category_df.set_index("REPORT_DATE_NAME", inplace=True)
                category_dataframes[category_name] = category_df
            # print(f'{category_name} - \n{indicators} - \n{available_indicators}')

        return category_dataframes

    ak_df: pd.DataFrame = None
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        analysis_type = "0"
        if report_period_type == ReportDateType.BY_PERIOD:
            analysis_type = "0"
        elif report_period_type == ReportDateType.ANNUAL:
            analysis_type = "1"
        elif report_period_type == ReportDateType.QUARTERLY:
            analysis_type = "2"
        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type={analysis_type}&code={symbol}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        if data["data"]:
            ak_df = pd.DataFrame(data["data"])
        else:
            return {}

    ak_df.to_json(
        f"./logs/em_retrieve_company_financial_analysis_indicators_{market_code.value}_{symbol}_{report_period_type.value}_raw.json",
        force_ascii=False,
        indent=2,
    )

    # 筛选指定年份内的数据
    if "REPORT_DATE" in ak_df.columns:
        ak_df["REPORT_DATE_T"] = pd.to_datetime(ak_df["REPORT_DATE"])
        cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)
        ak_df = ak_df[ak_df["REPORT_DATE_T"] >= cutoff_date].copy()
        ak_df = ak_df.sort_values("REPORT_DATE_T", ascending=False)
        
    if "REPORT_DATE_NAME" not in ak_df.columns:
        ak_df["REPORT_DATE_NAME"] = ak_df["REPORT_DATE_T"].dt.strftime("%Y-%m-%d")
    print(ak_df)
    # 按分类分拆数据
    category_dataframes = create_category_dataframes(ak_df)

    # 格式化每个分类的表格
    indicator_mapping = get_financial_indicator_mapping(report_period_type)        
    final_reports : dict[str, TradingReportResultPack] = {}
    for category_name, category_df in category_dataframes.items():
        table_str = format_pd_dataframe_to_markdown(category_df, include_index=True, transpose=True, column_mapping=indicator_mapping)
        final_reports[category_name] = TradingReportResultPack(
            dataframe=category_df,
            markdown_table=table_str,
            json_dict=json.loads(category_df.to_json(force_ascii=False, indent=2)),
        )

    with open(
        f"./logs/em_retrieve_company_financial_analysis_indicators_{market_code.value}_{symbol}_{report_period_type.value}_reports.json",
        "w",
    ) as f:
        r = {}
        for k, v in final_reports.items():
            r[k] = v.json_dict
        json.dump(r, f, ensure_ascii=False, indent=2)

    with open(
        f"./logs/em_retrieve_company_financial_analysis_indicators_{market_code.value}_{symbol}_{report_period_type.value}_reports.md",
        "w",
    ) as f:
        for category_name, report_item in final_reports.items():
            f.write(f"\n\n## {category_name}\n")
            f.write(report_item.markdown_table)
            f.write("\n")

    return final_reports

async def em_retrieve_company_financial_analysis_cash_flow_statement(
    market_code: MarketCode,
    symbol: str,
    report_date_type: ReportDateType,
    include_yoy: bool,
    include_qoq: bool,
    look_back_years: int,
) -> dict[str, TradingReportResultPack]:
    """
    获取股票财务分析现金流量表，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#xjll-0
    Args:
        market_code: 市场类型
        symbol: 股票代码
        report_date_type: 报告期类型
        include_yoy: 是否包含同比
        include_qoq: 是否包含环比
        look_back_years: 回溯年数
    """

    def create_category_cash_flow_statement_dataframes(
        df: pd.DataFrame, include_yoy: bool, include_qoq: bool
    ) -> dict[str, pd.DataFrame]:
        """格式化现金流量表DataFrame，在转置前按分类分拆并返回分类后的字典"""

        # 现金流量表主要项目列名
        main_cash_flow_columns = [
            # 基本信息
            "REPORT_DATE",  # 报告期
            "REPORT_DATE_NAME",  # 报告期名称
            # 经营活动现金流量 - 现金流入
            "SALES_SERVICES",  # 销售商品、提供劳务收到的现金
            "DEPOSIT_INTERBANK_ADD",  # 客户存款和同业存放款项净增加额
            "RECEIVE_INTEREST_COMMISSION",  # 收取利息、手续费及佣金的现金
            "RECEIVE_TAX_REFUND",  # 收到的税费返还
            "RECEIVE_OTHER_OPERATE",  # 收到其他与经营活动有关的现金
            "TOTAL_OPERATE_INFLOW",  # 经营活动现金流入小计
            # 经营活动现金流量 - 现金流出
            "BUY_SERVICES",  # 购买商品、接受劳务支付的现金
            "LOAN_ADVANCE_ADD",  # 客户贷款及垫款净增加额
            "PBC_INTERBANK_ADD",  # 存放中央银行和同业款项净增加额
            "PAY_INTEREST_COMMISSION",  # 支付利息、手续费及佣金的现金
            "PAY_STAFF_CASH",  # 支付给职工以及为职工支付的现金
            "PAY_ALL_TAX",  # 支付的各项税费
            "PAY_OTHER_OPERATE",  # 支付其他与经营活动有关的现金
            "OPERATE_OUTFLOW_OTHER",  # 经营活动现金流出的其他项目
            "TOTAL_OPERATE_OUTFLOW",  # 经营活动现金流出小计
            "NETCASH_OPERATE",  # 经营活动产生的现金流量净额
            # 投资活动现金流量
            "WITHDRAW_INVEST",  # 收回投资收到的现金
            "RECEIVE_INVEST_INCOME",  # 取得投资收益收到的现金
            "DISPOSAL_LONG_ASSET",  # 处置固定资产、无形资产和其他长期资产收回的现金净额
            "RECEIVE_OTHER_INVEST",  # 收到的其他与投资活动有关的现金
            "TOTAL_INVEST_INFLOW",  # 投资活动现金流入小计
            "CONSTRUCT_LONG_ASSET",  # 购建固定资产、无形资产和其他长期资产支付的现金
            "INVEST_PAY_CASH",  # 投资支付的现金
            "PAY_OTHER_INVEST",  # 支付其他与投资活动有关的现金
            "TOTAL_INVEST_OUTFLOW",  # 投资活动现金流出小计
            "NETCASH_INVEST",  # 投资活动产生的现金流量净额
            # 筹资活动现金流量
            "ASSIGN_DIVIDEND_PORFIT",  # 分配股利、利润或偿付利息支付的现金
            "SUBSIDIARY_PAY_DIVIDEND",  # 其中:子公司支付给少数股东的股利、利润
            "PAY_OTHER_FINANCE",  # 支付的其他与筹资活动有关的现金
            "TOTAL_FINANCE_OUTFLOW",  # 筹资活动现金流出小计
            "NETCASH_FINANCE",  # 筹资活动产生的现金流量净额
            # 汇率变动及现金净增加额
            "RATE_CHANGE_EFFECT",  # 汇率变动对现金及现金等价物的影响
            "CCE_ADD",  # 现金及现金等价物净增加额
            "BEGIN_CCE",  # 加:期初现金及现金等价物余额
            "END_CCE",  # 期末现金及现金等价物余额
        ]

        # 现金流量表分类及对应的列名
        cash_flow_categories = {
            "经营活动现金流量": [
                "SALES_SERVICES",
                "DEPOSIT_INTERBANK_ADD",
                "RECEIVE_INTEREST_COMMISSION",
                "RECEIVE_TAX_REFUND",
                "RECEIVE_OTHER_OPERATE",
                "TOTAL_OPERATE_INFLOW",
                "BUY_SERVICES",
                "LOAN_ADVANCE_ADD",
                "PBC_INTERBANK_ADD",
                "PAY_INTEREST_COMMISSION",
                "PAY_STAFF_CASH",
                "PAY_ALL_TAX",
                "PAY_OTHER_OPERATE",
                "OPERATE_OUTFLOW_OTHER",
                "TOTAL_OPERATE_OUTFLOW",
                "NETCASH_OPERATE",
            ],
            "投资活动现金流量": [
                "WITHDRAW_INVEST",
                "RECEIVE_INVEST_INCOME",
                "DISPOSAL_LONG_ASSET",
                "RECEIVE_OTHER_INVEST",
                "TOTAL_INVEST_INFLOW",
                "CONSTRUCT_LONG_ASSET",
                "INVEST_PAY_CASH",
                "PAY_OTHER_INVEST",
                "TOTAL_INVEST_OUTFLOW",
                "NETCASH_INVEST",
            ],
            "筹资活动现金流量": [
                "ASSIGN_DIVIDEND_PORFIT",
                "SUBSIDIARY_PAY_DIVIDEND",
                "PAY_OTHER_FINANCE",
                "TOTAL_FINANCE_OUTFLOW",
                "NETCASH_FINANCE",
            ],
            "汇率变动及现金净增加额": [
                "RATE_CHANGE_EFFECT",
                "CCE_ADD",
                "BEGIN_CCE",
                "END_CCE",
            ],
        }

        # 1. 筛选现金流量表主要项目相关的列
        available_columns = []
        for col in main_cash_flow_columns:
            if col in df.columns:
                available_columns.append(col)
            if include_yoy:
                if col + "_YOY" in df.columns:
                    available_columns.append(col + "_YOY")
            if include_qoq:
                if col + "_QOQ" in df.columns:
                    available_columns.append(col + "_QOQ")

        # 筛选数据，只保留主要现金流量列
        if available_columns:
            df = df[available_columns].copy()

        # 2. 处理报告期名称，转换为简化格式
        if "REPORT_DATE" in df.columns:

            def format_date_name(date_obj):
                if pd.isna(date_obj):
                    return str(date_obj)
                if isinstance(date_obj, str):
                    return date_obj[0:10]
                return date_obj

            # 创建报告期名称列
            df["REPORT_DATE_NAME"] = df["REPORT_DATE"].apply(format_date_name)

        # 3. 在重命名前按分类分拆数据
        category_dataframes = {}

        for category_name, indicators in cash_flow_categories.items():
            # 获取该分类下存在的指标
            available_indicators = {
                "NORMAL": [],
            }
            for indicator in indicators:
                if indicator in df.columns:
                    available_indicators["NORMAL"].append(indicator)
                    
            if include_yoy:
                available_indicators["YOY"] = []
                for indicator in indicators:
                    indicator_yoy = indicator + "_YOY"
                    if indicator_yoy in df.columns:
                        available_indicators["YOY"].append(indicator_yoy)
            if include_qoq:
                available_indicators["QOQ"] = []
                for indicator in indicators:
                    indicator_qoq = indicator + "_QOQ"
                    if indicator_qoq in df.columns:
                        available_indicators["QOQ"].append(indicator_qoq)
            # print(f"available_indicators: \n{json.dumps(available_indicators, indent=2, ensure_ascii=False)}")

            for _type, _indicators in available_indicators.items():
                if len(_indicators) == 0:
                    continue
                
                final_category_name = category_name
                if _type == "YOY":
                    final_category_name = final_category_name + "-同比"
                elif _type == "QOQ":
                    final_category_name = final_category_name + "-环比"
                
                # 创建该分类的DataFrame，包含报告期名称列
                category_columns = ["REPORT_DATE_NAME"] + _indicators
                category_data = df[category_columns].copy()
                category_data.set_index("REPORT_DATE_NAME", inplace=True)
                category_dataframes[final_category_name] = category_data

        return category_dataframes

    # 现金流量表主要项目列名映射字典
    cash_flow_statement_column_mapping = {
        # 基本信息
        "REPORT_DATE": "报告期",
        "REPORT_DATE_NAME": "报告期名称",
        # 经营活动现金流量 - 现金流入
        "SALES_SERVICES": "销售商品提供劳务收到的现金",
        "DEPOSIT_INTERBANK_ADD": "客户存款和同业存放款项净增加额",
        "RECEIVE_INTEREST_COMMISSION": "收取利息手续费及佣金的现金",
        "RECEIVE_TAX_REFUND": "收到的税收返还",
        "RECEIVE_OTHER_OPERATE": "收到其他与经营活动有关的现金",
        "TOTAL_OPERATE_INFLOW": "经营活动现金流入小计",
        # 经营活动现金流量 - 现金流出
        "BUY_SERVICES": "购买商品接受劳务支付的现金",
        "LOAN_ADVANCE_ADD": "客户贷款及垫款净增加额",
        "PBC_INTERBANK_ADD": "存放中央银行和同业款项净增加额",
        "PAY_INTEREST_COMMISSION": "支付利息手续费及佣金的现金",
        "PAY_STAFF_CASH": "支付给职工以及为职工支付的现金",
        "PAY_ALL_TAX": "支付的各项税费",
        "PAY_OTHER_OPERATE": "支付其他与经营活动有关的现金",
        "OPERATE_OUTFLOW_OTHER": "经营活动现金流出的其他项目",
        "TOTAL_OPERATE_OUTFLOW": "经营活动现金流出小计",
        "NETCASH_OPERATE": "经营活动产生的现金流量净额",
        # 投资活动现金流量
        "WITHDRAW_INVEST": "收回投资收到的现金",
        "RECEIVE_INVEST_INCOME": "取得投资收益收到的现金",
        "DISPOSAL_LONG_ASSET": "处置固定资产无形资产和其他长期资产收回的现金净额",
        "RECEIVE_OTHER_INVEST": "收到的其他与投资活动有关的现金",
        "TOTAL_INVEST_INFLOW": "投资活动现金流入小计",
        "CONSTRUCT_LONG_ASSET": "购建固定资产无形资产和其他长期资产支付的现金",
        "INVEST_PAY_CASH": "投资支付的现金",
        "PAY_OTHER_INVEST": "支付其他与投资活动有关的现金",
        "TOTAL_INVEST_OUTFLOW": "投资活动现金流出小计",
        "NETCASH_INVEST": "投资活动产生的现金流量净额",
        # 筹资活动现金流量
        "ASSIGN_DIVIDEND_PORFIT": "分配股利利润或偿付利息支付的现金",
        "SUBSIDIARY_PAY_DIVIDEND": "其中子公司支付给少数股东的股利利润",
        "PAY_OTHER_FINANCE": "支付的其他与筹资活动有关的现金",
        "TOTAL_FINANCE_OUTFLOW": "筹资活动现金流出小计",
        "NETCASH_FINANCE": "筹资活动产生的现金流量净额",
        # 汇率变动及现金净增加额
        "RATE_CHANGE_EFFECT": "汇率变动对现金及现金等价物的影响",
        "CCE_ADD": "现金及现金等价物净增加额",
        "BEGIN_CCE": "加期初现金及现金等价物余额",
        "END_CCE": "期末现金及现金等价物余额",
    }
    if include_yoy:
        cash_flow_statement_column_mapping = {
            **cash_flow_statement_column_mapping,
            **{
                key + "_YOY": value + "(%)" for key, value in cash_flow_statement_column_mapping.items()
            }
        }
    if include_qoq:
        cash_flow_statement_column_mapping = {
            **cash_flow_statement_column_mapping,
            **{
                key + "_QOQ": value + "(%)" for key, value in cash_flow_statement_column_mapping.items()
            }
        }
        
    
    em_company_type = "4"
    em_code = symbol.replace(".", "").replace("SH", "").replace("SZ", "")
    if market_code == MarketCode.SH:
        em_code = "SH" + em_code
    elif market_code == MarketCode.SZ:
        em_code = "SZ" + em_code
    cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        if report_date_type == ReportDateType.BY_PERIOD:
            em_report_date_type = "0"
        elif report_date_type == ReportDateType.ANNUAL:
            em_report_date_type = "1"
        elif report_date_type == ReportDateType.QUARTERLY:
            em_report_date_type = "2"
        else:
            raise ValueError(f"Invalid report period type: {report_date_type}")

        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/xjllbDateAjaxNew?companyType={em_company_type}&reportDateType={em_report_date_type}&code={em_code}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        avalible_reports = data["data"]
        filtered_reports = []
        for report in avalible_reports:
            report_date = datetime.fromisoformat(report["REPORT_DATE"])
            if report_date >= cutoff_date:
                filtered_reports.append(report)
        if len(filtered_reports) == 0:
            return {}
        else:
            logger.info(f"Found {len(filtered_reports)} reports: {filtered_reports}")
            if report_date_type == ReportDateType.BY_PERIOD:
                em_report_date_type = "0"
                em_report_type = "1"
            elif report_date_type == ReportDateType.ANNUAL:
                em_report_date_type = "1"
                em_report_type = "1"
            elif report_date_type == ReportDateType.QUARTERLY:
                em_report_date_type = "0"
                em_report_type = "2"
            else:
                raise ValueError(f"Invalid report period type: {report_date_type}")   
                     
            all_data = []
            for i in range(0, len(filtered_reports), 5):
                batch_reports = filtered_reports[i : i + 5]
                em_dates = ",".join(
                    [report["REPORT_DATE"][0:10] for report in batch_reports]
                )
                data_url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/xjllbAjaxNew?companyType={em_company_type}&reportDateType={em_report_date_type}&reportType={em_report_type}&dates={em_dates}&code={em_code}"
                response = await client.get(data_url)
                response.raise_for_status()
                data = response.json()
                logger.info(f"response size: {len(data['data'])}")
                if data["data"]:
                    all_data.extend(data["data"])

            if all_data:
                em_df = pd.DataFrame(all_data)
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_cash_flow_statement_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_{include_qoq}_raw.json",
                    "w",
                ) as f:
                    em_df.to_json(f, force_ascii=False, indent=2)

                # 格式化现金流量表数据
                em_dfs = create_category_cash_flow_statement_dataframes(em_df, include_yoy, include_qoq)

                # 生成分类后的markdown报告
                final_reports : dict[str, TradingReportResultPack] = {}
                for category_name, category_df in em_dfs.items():
                    table_str = format_pd_dataframe_to_markdown(
                        category_df, include_index=True, transpose=True, column_mapping=cash_flow_statement_column_mapping
                    )
                    final_reports[category_name] = TradingReportResultPack(
                        dataframe=category_df,
                        markdown_table=table_str,
                        json_dict=json.loads(category_df.to_json(force_ascii=False, indent=2)),
                    )

                # 保存分类后的markdown报告
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_cash_flow_statement_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_{include_qoq}_reports.md",
                    "w",
                ) as f:
                    for category_name, report_item in final_reports.items():
                        f.write(f"\n\n## {category_name}\n")
                        f.write(report_item.markdown_table)
                        f.write("\n")

                # 保存分类后的JSON报告
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_cash_flow_statement_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_{include_qoq}_reports.json",
                    "w",
                ) as f:
                    r = {}
                    for k, v in final_reports.items():
                        r[k] = v.json_dict
                    json.dump(r, f, ensure_ascii=False, indent=2)
                return final_reports
            else:
                return {}
    return {}

async def em_retrieve_company_financial_analysis_balance_sheet(
    market_code: MarketCode,
    symbol: str,
    report_date_type: ReportDateType,
    include_yoy: bool,
    look_back_years: int,
) -> dict[str, TradingReportResultPack]:
    """
    获取股票财务分析指标，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#zyzb-0
    Args:
        market_code: 市场类型
        symbol: 股票代码
        report_date_type: 报告期类型
        include_yoy: 是否包含同比
        look_back_years: 回溯年数
    """
    def create_category_balance_sheet_dataframes(df: pd.DataFrame, include_yoy: bool) -> dict[str, pd.DataFrame]:
        """格式化资产负债表DataFrame，按分类分拆并返回分类后的字典，不进行转置"""
        
        # 资产负债表主要项目列名
        main_balance_sheet_columns = [
            # 基本信息
            "REPORT_DATE",  # 报告期
            "REPORT_DATE_NAME",  # 报告期名称
            # 流动资产
            "MONETARYFUNDS",  # 货币资金
            "LEND_FUND",  # 拆出资金
            "TRADE_FINASSET",  # 交易性金融资产
            "TRADE_FINASSET_NOTFVTPL",  # 交易性金融资产
            "NOTE_ACCOUNTS_RECE",  # 应收票据及应收账款
            "NOTE_RECE",  # 其中:应收票据
            "ACCOUNTS_RECE",  # 应收账款
            "PREPAYMENT",  # 预付款项
            "OTHER_RECE",  # 其他应收款合计
            "BUY_RESALE_FINASSET",  # 买入返售金融资产
            "INVENTORY",  # 存货
            "NONCURRENT_ASSET_1YEAR",  # 一年内到期的非流动资产
            "OTHER_CURRENT_ASSET",  # 其他流动资产
            "TOTAL_CURRENT_ASSETS",  # 流动资产合计
            # 非流动资产
            "LOAN_ADVANCE",  # 发放贷款及垫款
            "CREDITOR_INVEST",  # 债权投资
            "OTHER_NONCURRENT_FINASSET",  # 其他非流动金融资产
            "INVEST_REALESTATE",  # 投资性房地产
            "FIXED_ASSET",  # 固定资产
            "CIP",  # 在建工程
            "LEASE_LIAB",  # 使用权资产
            "INTANGIBLE_ASSET",  # 无形资产
            "DEVELOP_EXPENSE",  # 开发支出
            "LONG_PREPAID_EXPENSE",  # 长期待摊费用
            "DEFER_TAX_ASSET",  # 递延所得税资产
            "OTHER_NONCURRENT_ASSET",  # 其他非流动资产
            "TOTAL_NONCURRENT_ASSETS",  # 非流动资产合计
            "TOTAL_ASSETS",  # 资产总计
            # 流动负债
            "NOTE_ACCOUNTS_PAYABLE",  # 应付票据及应付账款
            "ACCOUNTS_PAYABLE",  # 其中:应付账款
            "CONTRACT_LIAB",  # 合同负债
            "STAFF_SALARY_PAYABLE",  # 应付职工薪酬
            "TAX_PAYABLE",  # 应交税费
            "TOTAL_OTHER_PAYABLE",  # 其他应付款合计
            "NONCURRENT_LIAB_1YEAR",  # 一年内到期的非流动负债
            "OTHER_CURRENT_LIAB",  # 其他流动负债
            "TOTAL_CURRENT_LIAB",  # 流动负债合计
            # 所有者权益
            "SHARE_CAPITAL",  # 实收资本（或股本）
            "CAPITAL_RESERVE",  # 资本公积
            "TREASURY_SHARES",  # 减:库存股
            "OTHER_COMPRE_INCOME",  # 其他综合收益
            "SURPLUS_RESERVE",  # 盈余公积
            "GENERAL_RISK_RESERVE",  # 一般风险准备
            "UNASSIGN_RPOFIT",  # 未分配利润
            "TOTAL_PARENT_EQUITY",  # 归属于母公司股东权益总计
            "MINORITY_EQUITY",  # 少数股东权益
            "TOTAL_EQUITY",  # 股东权益合计
            "TOTAL_LIAB_EQUITY",  # 负债和股东权益总计
            # 审计意见
            "OPINION_TYPE",  # 审计意见(境内)
        ]

        # 资产负债表分类及对应的列名
        balance_sheet_categories = {
            "流动资产": [
                "MONETARYFUNDS",
                "LEND_FUND",
                "TRADE_FINASSET",
                "TRADE_FINASSET_NOTFVTPL",
                "NOTE_ACCOUNTS_RECE",
                "NOTE_RECE",
                "ACCOUNTS_RECE",
                "PREPAYMENT",
                "OTHER_RECE",
                "BUY_RESALE_FINASSET",
                "INVENTORY",
                "NONCURRENT_ASSET_1YEAR",
                "OTHER_CURRENT_ASSET",
                "TOTAL_CURRENT_ASSETS",
            ],
            "非流动资产": [
                "LOAN_ADVANCE",
                "CREDITOR_INVEST",
                "OTHER_NONCURRENT_FINASSET",
                "INVEST_REALESTATE",
                "FIXED_ASSET",
                "CIP",
                "LEASE_LIAB",
                "INTANGIBLE_ASSET",
                "DEVELOP_EXPENSE",
                "LONG_PREPAID_EXPENSE",
                "DEFER_TAX_ASSET",
                "OTHER_NONCURRENT_ASSET",
                "TOTAL_NONCURRENT_ASSETS",
                "TOTAL_ASSETS",
            ],
            "流动负债": [
                "NOTE_ACCOUNTS_PAYABLE",
                "ACCOUNTS_PAYABLE",
                "CONTRACT_LIAB",
                "STAFF_SALARY_PAYABLE",
                "TAX_PAYABLE",
                "TOTAL_OTHER_PAYABLE",
                "NONCURRENT_LIAB_1YEAR",
                "OTHER_CURRENT_LIAB",
                "TOTAL_CURRENT_LIAB",
            ],
            "所有者权益(或股东权益)": [
                "SHARE_CAPITAL",
                "CAPITAL_RESERVE",
                "TREASURY_SHARES",
                "OTHER_COMPRE_INCOME",
                "SURPLUS_RESERVE",
                "GENERAL_RISK_RESERVE",
                "UNASSIGN_RPOFIT",
                "TOTAL_PARENT_EQUITY",
                "MINORITY_EQUITY",
                "TOTAL_EQUITY",
                "TOTAL_LIAB_EQUITY",
            ],
        }

        # 筛选资产负债表主要项目相关的列
        available_columns = []
        for col in main_balance_sheet_columns:
            if col in df.columns:
                available_columns.append(col)
            if include_yoy:
                if col + "_YOY" in df.columns:
                    available_columns.append(col + "_YOY")

        # 筛选数据，只保留主要资产负债表列
        if available_columns:
            df = df[available_columns].copy()
            
        # 按分类分拆数据
        category_dataframes = {}
        for category_name, indicators in balance_sheet_categories.items():
            # 获取该分类下存在的指标
            available_indicators = {
                "NORMAL": [],
            }
            for indicator in indicators:
                if indicator in df.columns:
                    available_indicators["NORMAL"].append(indicator)                    
                    
            if include_yoy:
                available_indicators["YOY"] = []
                for indicator in indicators:
                    indicator_yoy = indicator + "_YOY"
                    if indicator_yoy in df.columns:
                        available_indicators["YOY"].append(indicator_yoy)

            for _type, _indicators in available_indicators.items():
                if len(_indicators) == 0:
                    continue
                
                final_category_name = category_name
                if _type == "YOY":
                    final_category_name = final_category_name + "-同比"
                
                # 创建该分类的DataFrame，包含报告期名称列
                category_columns = ["REPORT_DATE_NAME"] + _indicators
                category_data = df[category_columns].copy()
                category_data.set_index("REPORT_DATE_NAME", inplace=True)
                category_dataframes[final_category_name] = category_data

        return category_dataframes

    # 资产负债表主要项目列名映射字典
    balance_sheet_column_mapping = {
        # 基本信息
        "REPORT_DATE": "报告期",
        "REPORT_DATE_NAME": "报告期名称",
        # 流动资产
        "MONETARYFUNDS": "货币资金",
        "LEND_FUND": "拆出资金",
        "TRADE_FINASSET": "交易性金融资产",
        "TRADE_FINASSET_NOTFVTPL": "交易性金融资产",
        "NOTE_ACCOUNTS_RECE": "应收票据及应收账款",
        "NOTE_RECE": "其中:应收票据",
        "ACCOUNTS_RECE": "应收账款",
        "PREPAYMENT": "预付款项",
        "OTHER_RECE": "其他应收款合计",
        "BUY_RESALE_FINASSET": "买入返售金融资产",
        "INVENTORY": "存货",
        "NONCURRENT_ASSET_1YEAR": "一年内到期的非流动资产",
        "OTHER_CURRENT_ASSET": "其他流动资产",
        "TOTAL_CURRENT_ASSETS": "流动资产合计",
        # 非流动资产
        "LOAN_ADVANCE": "发放贷款及垫款",
        "CREDITOR_INVEST": "债权投资",
        "OTHER_NONCURRENT_FINASSET": "其他非流动金融资产",
        "INVEST_REALESTATE": "投资性房地产",
        "FIXED_ASSET": "固定资产",
        "CIP": "在建工程",
        "LEASE_LIAB": "使用权资产",
        "INTANGIBLE_ASSET": "无形资产",
        "DEVELOP_EXPENSE": "开发支出",
        "LONG_PREPAID_EXPENSE": "长期待摊费用",
        "DEFER_TAX_ASSET": "递延所得税资产",
        "OTHER_NONCURRENT_ASSET": "其他非流动资产",
        "TOTAL_NONCURRENT_ASSETS": "非流动资产合计",
        "TOTAL_ASSETS": "资产总计",
        # 流动负债
        "NOTE_ACCOUNTS_PAYABLE": "应付票据及应付账款",
        "ACCOUNTS_PAYABLE": "其中:应付账款",
        "CONTRACT_LIAB": "合同负债",
        "STAFF_SALARY_PAYABLE": "应付职工薪酬",
        "TAX_PAYABLE": "应交税费",
        "TOTAL_OTHER_PAYABLE": "其他应付款合计",
        "NONCURRENT_LIAB_1YEAR": "一年内到期的非流动负债",
        "OTHER_CURRENT_LIAB": "其他流动负债",
        "TOTAL_CURRENT_LIAB": "流动负债合计",
        # 所有者权益
        "SHARE_CAPITAL": "实收资本（或股本）",
        "CAPITAL_RESERVE": "资本公积",
        "TREASURY_SHARES": "减:库存股",
        "OTHER_COMPRE_INCOME": "其他综合收益",
        "SURPLUS_RESERVE": "盈余公积",
        "GENERAL_RISK_RESERVE": "一般风险准备",
        "UNASSIGN_RPOFIT": "未分配利润",
        "TOTAL_PARENT_EQUITY": "归属于母公司股东权益总计",
        "MINORITY_EQUITY": "少数股东权益",
        "TOTAL_EQUITY": "股东权益合计",
        "TOTAL_LIAB_EQUITY": "负债和股东权益总计",
        # 审计意见
        "OPINION_TYPE": "审计意见(境内)",
    }
    if include_yoy:
        balance_sheet_column_mapping = {
            **balance_sheet_column_mapping,
            **{
                key + "_YOY": value + "(%)" for key, value in balance_sheet_column_mapping.items()
            }
        }    
    
    em_company_type = "4"
    em_code = symbol.replace(".", "").replace("SH", "").replace("SZ", "")
    if market_code == MarketCode.SH:
        em_code = "SH" + em_code
    elif market_code == MarketCode.SZ:
        em_code = "SZ" + em_code
    cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        if report_date_type == ReportDateType.BY_PERIOD:
            em_report_date_type = "0"
        elif report_date_type == ReportDateType.ANNUAL:
            em_report_date_type = "1"
        else:
            raise ValueError(f"Invalid report period type: {report_date_type}")

        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/zcfzbDateAjaxNew?companyType={em_company_type}&reportDateType={em_report_date_type}&code={em_code}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        avalible_reports = data["data"]
        filtered_reports = []
        for report in avalible_reports:
            report_date = datetime.fromisoformat(report["REPORT_DATE"])
            if report_date >= cutoff_date:
                filtered_reports.append(report)
        if len(filtered_reports) == 0:
            return {}
        else:
            logger.info(f"Found {len(filtered_reports)} reports: {filtered_reports}")
            em_report_type = "1"
            if report_date_type == ReportDateType.BY_PERIOD:
                em_report_date_type = "0"
            elif report_date_type == ReportDateType.ANNUAL:
                em_report_date_type = "1"
            else:
                raise ValueError(f"Invalid report period type: {report_date_type}")   
    
            all_data = []
            for i in range(0, len(filtered_reports), 5):
                batch_reports = filtered_reports[i : i + 5]
                em_dates = ",".join(
                    [report["REPORT_DATE"][0:10] for report in batch_reports]
                )
                data_url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/zcfzbAjaxNew?companyType={em_company_type}&reportDateType={em_report_date_type}&reportType={em_report_type}&dates={em_dates}&code={em_code}"
                response = await client.get(data_url)
                response.raise_for_status()
                data = response.json()
                logger.info(f"response size: {len(data['data'])}")
                if data["data"]:
                    all_data.extend(data["data"])

            if all_data:
                em_df = pd.DataFrame(all_data)
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_balance_sheet_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_raw.json",
                    "w",
                ) as f:
                    em_df.to_json(f, force_ascii=False, indent=2)
                    
                em_dfs = create_category_balance_sheet_dataframes(em_df, include_yoy)
                final_reports : dict[str, TradingReportResultPack] = {}
                for category_name, category_df in em_dfs.items():
                    table_str = format_pd_dataframe_to_markdown(category_df, include_index=True, transpose=True, column_mapping=balance_sheet_column_mapping)
                    final_reports[category_name] = TradingReportResultPack(
                        dataframe=category_df,
                        markdown_table=table_str,
                        json_dict=json.loads(category_df.to_json(force_ascii=False, indent=2)),
                    )
                    
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_balance_sheet_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_reports.json",
                    "w",
                ) as f:
                    r = {}
                    for k, v in final_reports.items():
                        r[k] = v.json_dict
                    json.dump(r, f, ensure_ascii=False, indent=2)
                    
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_balance_sheet_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_reports.md",
                    "w",
                ) as f:
                    for category_name, report_item in final_reports.items():
                        f.write(f"\n\n## {category_name}\n")
                        f.write(report_item.markdown_table)
                        f.write("\n")
                
                return final_reports
            return {}

async def em_retrieve_company_financial_analysis_income_statement(
    market_code: MarketCode,
    symbol: str,
    report_date_type: ReportDateType,
    include_yoy: bool,
    include_qoq: bool,
    look_back_years: int,
) -> dict[str, TradingReportResultPack]:
    """
    获取股票财务分析利润表，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#lrb-0
    Args:
        market_code: 市场类型
        symbol: 股票代码
        report_date_type: 报告期类型
        include_yoy: 是否包含同比
        include_qoq: 是否包含环比
        look_back_years: 回溯年数
    """

    def create_category_income_statement_dataframes(
        df: pd.DataFrame, include_yoy: bool, include_qoq: bool
    ) -> dict[str, pd.DataFrame]:
        """格式化利润表DataFrame，在转置前按分类分拆并返回分类后的字典"""

        # 利润表主要项目列名
        main_income_statement_columns = [
            "REPORT_DATE",
            "REPORT_DATE_NAME",
            "TOTAL_OPERATE_INCOME",  # 营业总收入
            "OPERATE_INCOME",  # 营业收入
            "INTEREST_INCOME",  # 利息收入
            "TOTAL_OPERATE_COST",  # 营业总成本
            "OPERATE_COST",  # 营业成本
            "INTEREST_EXPENSE",  # 利息支出
            "FEE_COMMISSION_EXPENSE",  # 手续费及佣金支出
            "OPERATE_TAX_ADD",  # 税金及附加
            "SALE_EXPENSE",  # 销售费用
            "MANAGE_EXPENSE",  # 管理费用
            "RESEARCH_EXPENSE",  # 研发费用
            "FINANCE_EXPENSE",  # 财务费用
            "FE_INTEREST_EXPENSE",  # 其中:利息费用
            "FE_INTEREST_INCOME",  # 利息收入
            "FAIRVALUE_CHANGE_INCOME",  # 加:公允价值变动收益
            "INVEST_INCOME",  # 投资收益
            "ASSET_DISPOSAL_INCOME",  # 资产处置收益
            "CREDIT_IMPAIRMENT_INCOME",  # 信用减值损失(新)
            "OTHER_INCOME",  # 其他收益
            "OPERATE_PROFIT",  # 营业利润
            "NONBUSINESS_INCOME",  # 加:营业外收入
            "NONBUSINESS_EXPENSE",  # 减:营业外支出
            "TOTAL_PROFIT",  # 利润总额
            "INCOME_TAX",  # 减:所得税
            "NETPROFIT",  # 净利润
            "CONTINUED_NETPROFIT",  # 持续经营净利润
            "PARENT_NETPROFIT",  # 归属于母公司股东的净利润
            "MINORITY_INTEREST",  # 少数股东损益
            "DEDUCT_PARENT_NETPROFIT",  # 扣除非经常性损益后的净利润
            "BASIC_EPS",  # 基本每股收益
            "DILUTED_EPS",  # 稀释每股收益
            "OTHER_COMPRE_INCOME",  # 其他综合收益
            "PARENT_OCI",  # 归属于母公司股东的其他综合收益
            "TOTAL_COMPRE_INCOME",  # 综合收益总额
            "PARENT_TCI",  # 归属于母公司股东的综合收益总额
            "MINORITY_TCI",  # 归属于少数股东的综合收益总额
        ]

        # 利润表分类及对应的列名
        income_categories = {
            "营业收入": [
                "TOTAL_OPERATE_INCOME",  # 营业总收入
                "OPERATE_INCOME",  # 营业收入
                "INTEREST_INCOME",  # 利息收入
            ],
            "营业成本": [
                "TOTAL_OPERATE_COST",  # 营业总成本
                "OPERATE_COST",  # 营业成本
                "INTEREST_EXPENSE",  # 利息支出
                "FEE_COMMISSION_EXPENSE",  # 手续费及佣金支出
                "OPERATE_TAX_ADD",  # 税金及附加
                "SALE_EXPENSE",  # 销售费用
                "MANAGE_EXPENSE",  # 管理费用
                "RESEARCH_EXPENSE",  # 研发费用
                "FINANCE_EXPENSE",  # 财务费用
                "FE_INTEREST_EXPENSE",  # 其中:利息费用
                "FE_INTEREST_INCOME",  # 利息收入
            ],
            "其他经营收益": [
                "FAIRVALUE_CHANGE_INCOME",  # 加:公允价值变动收益
                "INVEST_INCOME",  # 投资收益
                "ASSET_DISPOSAL_INCOME",  # 资产处置收益
                "CREDIT_IMPAIRMENT_INCOME",  # 信用减值损失(新)
                "OTHER_INCOME",  # 其他收益
            ],
            "营业利润": [
                "OPERATE_PROFIT",  # 营业利润
                "NONBUSINESS_INCOME",  # 加:营业外收入
                "NONBUSINESS_EXPENSE",  # 减:营业外支出
                "TOTAL_PROFIT",  # 利润总额
                "INCOME_TAX",  # 减:所得税
            ],
            "净利润": [
                "NETPROFIT",  # 净利润
                "CONTINUED_NETPROFIT",  # 持续经营净利润
                "PARENT_NETPROFIT",  # 归属于母公司股东的净利润
                "MINORITY_INTEREST",  # 少数股东损益
                "DEDUCT_PARENT_NETPROFIT",  # 扣除非经常性损益后的净利润
            ],
            "每股收益": [
                "BASIC_EPS",  # 基本每股收益
                "DILUTED_EPS",  # 稀释每股收益
                "OTHER_COMPRE_INCOME",  # 其他综合收益
                "PARENT_OCI",  # 归属于母公司股东的其他综合收益
                "TOTAL_COMPRE_INCOME",  # 综合收益总额
                "PARENT_TCI",  # 归属于母公司股东的综合收益总额
                "MINORITY_TCI",  # 归属于少数股东的综合收益总额
            ],
        }

        # 1. 筛选利润表主要项目相关的列
        available_columns = []
        for col in main_income_statement_columns:
            if col in df.columns:
                available_columns.append(col)
            if include_yoy:
                if col + "_YOY" in df.columns:
                    available_columns.append(col + "_YOY")
            if include_qoq:
                if col + "_QOQ" in df.columns:
                    available_columns.append(col + "_QOQ")

        # 筛选数据，只保留主要利润表列
        if available_columns:
            df = df[available_columns].copy()

        # 2. 处理报告期名称，转换为简化格式
        if "REPORT_DATE_NAME" not in df.columns:
            def format_date_name(date_obj):
                if pd.isna(date_obj):
                    return str(date_obj)
                if isinstance(date_obj, str):
                    return date_obj[0:10]
                return date_obj

            # 创建报告期名称列
            df["REPORT_DATE_NAME"] = df["REPORT_DATE"].apply(format_date_name)

        # 3. 在重命名前按分类分拆数据
        category_dataframes = {}

        for category_name, indicators in income_categories.items():
            # 获取该分类下存在的指标
            available_indicators = {
                "NORMAL": [],
            }
            for indicator in indicators:
                if indicator in df.columns:
                    available_indicators["NORMAL"].append(indicator)
                    
            if include_yoy:
                available_indicators["YOY"] = []
                for indicator in indicators:
                    indicator_yoy = indicator + "_YOY"
                    if indicator_yoy in df.columns:
                        available_indicators["YOY"].append(indicator_yoy)
            if include_qoq:
                available_indicators["QOQ"] = []
                for indicator in indicators:
                    indicator_qoq = indicator + "_QOQ"
                    if indicator_qoq in df.columns:
                        available_indicators["QOQ"].append(indicator_qoq)
            # print(f"available_indicators: \n{json.dumps(available_indicators, indent=2, ensure_ascii=False)}")

            for _type, _indicators in available_indicators.items():
                if len(_indicators) == 0:
                    continue
                
                final_category_name = category_name
                if _type == "YOY":
                    final_category_name = final_category_name + "-同比"
                elif _type == "QOQ":
                    final_category_name = final_category_name + "-环比"
                
                # 创建该分类的DataFrame，包含报告期名称列
                category_columns = ["REPORT_DATE_NAME"] + _indicators
                category_data = df[category_columns].copy()
                category_data.set_index("REPORT_DATE_NAME", inplace=True)
                category_dataframes[final_category_name] = category_data

        return category_dataframes

    # 利润表主要项目列名映射字典
    income_statement_column_mapping = {
        "TOTAL_OPERATE_INCOME": "营业总收入",
        "OPERATE_INCOME": "营业收入",
        "INTEREST_INCOME": "利息收入",
        "TOTAL_OPERATE_COST": "营业总成本",
        "OPERATE_COST": "营业成本",
        "INTEREST_EXPENSE": "利息支出",
        "FEE_COMMISSION_EXPENSE": "手续费及佣金支出",
        "OPERATE_TAX_ADD": "税金及附加",
        "SALE_EXPENSE": "销售费用",
        "MANAGE_EXPENSE": "管理费用",
        "RESEARCH_EXPENSE": "研发费用",
        "FINANCE_EXPENSE": "财务费用",
        "FE_INTEREST_EXPENSE": "其中:利息费用",
        "FE_INTEREST_INCOME": "利息收入",
        "FAIRVALUE_CHANGE_INCOME": "加:公允价值变动收益",
        "INVEST_INCOME": "投资收益",
        "ASSET_DISPOSAL_INCOME": "资产处置收益",
        "CREDIT_IMPAIRMENT_INCOME": "信用减值损失(新)",
        "OTHER_INCOME": "其他收益",
        "OPERATE_PROFIT": "营业利润",
        "NONBUSINESS_INCOME": "加:营业外收入",
        "NONBUSINESS_EXPENSE": "减:营业外支出",
        "TOTAL_PROFIT": "利润总额",
        "INCOME_TAX": "减:所得税",
        "NETPROFIT": "净利润",
        "CONTINUED_NETPROFIT": "持续经营净利润",
        "PARENT_NETPROFIT": "归属于母公司股东的净利润",
        "MINORITY_INTEREST": "少数股东损益",
        "DEDUCT_PARENT_NETPROFIT": "扣除非经常性损益后的净利润",
        "BASIC_EPS": "基本每股收益",
        "DILUTED_EPS": "稀释每股收益",
        "OTHER_COMPRE_INCOME": "其他综合收益",
        "PARENT_OCI": "归属于母公司股东的其他综合收益",
        "TOTAL_COMPRE_INCOME": "综合收益总额",
        "PARENT_TCI": "归属于母公司股东的综合收益总额",
        "MINORITY_TCI": "归属于少数股东的综合收益总额",
    }
    if include_yoy:
        income_statement_column_mapping = {
            **income_statement_column_mapping,
            **{
                key + "_YOY": value + "(%)" for key, value in income_statement_column_mapping.items()
            }
        }
    if include_qoq:
        income_statement_column_mapping = {
            **income_statement_column_mapping,
            **{
                key + "_QOQ": value + "(%)" for key, value in income_statement_column_mapping.items()
            }
        }
    em_company_type = "4"
    em_code = symbol.replace(".", "").replace("SH", "").replace("SZ", "")
    if market_code == MarketCode.SH:
        em_code = "SH" + em_code
    elif market_code == MarketCode.SZ:
        em_code = "SZ" + em_code
    cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        if report_date_type == ReportDateType.BY_PERIOD:
            em_report_date_type = "0"
        elif report_date_type == ReportDateType.ANNUAL:
            em_report_date_type = "1"
        elif report_date_type == ReportDateType.QUARTERLY:
            em_report_date_type = "2"
        else:
            raise ValueError(f"Invalid report period type: {report_date_type}")

        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/lrbDateAjaxNew?companyType={em_company_type}&reportDateType={em_report_date_type}&code={em_code}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        avalible_reports = data["data"]
        filtered_reports = []
        for report in avalible_reports:
            report_date = datetime.fromisoformat(report["REPORT_DATE"])
            if report_date >= cutoff_date:
                filtered_reports.append(report)
        if len(filtered_reports) == 0:
            return {}
        else:
            logger.info(f"Found {len(filtered_reports)} reports: {filtered_reports}")
            if report_date_type == ReportDateType.BY_PERIOD:
                em_report_date_type = "0"
                em_report_type = "1"
            elif report_date_type == ReportDateType.ANNUAL:
                em_report_date_type = "1"
                em_report_type = "1"
            elif report_date_type == ReportDateType.QUARTERLY:
                em_report_date_type = "0"
                em_report_type = "2"
            else:
                raise ValueError(f"Invalid report period type: {report_date_type}")   
                     
            all_data = []
            for i in range(0, len(filtered_reports), 5):
                batch_reports = filtered_reports[i : i + 5]
                em_dates = ",".join(
                    [report["REPORT_DATE"][0:10] for report in batch_reports]
                )
                data_url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/lrbAjaxNew?companyType={em_company_type}&reportDateType={em_report_date_type}&reportType={em_report_type}&dates={em_dates}&code={em_code}"
                response = await client.get(data_url)
                response.raise_for_status()
                data = response.json()
                logger.info(f"response size: {len(data['data'])}")
                if data["data"]:
                    all_data.extend(data["data"])

            if all_data:
                em_df = pd.DataFrame(all_data)
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_income_statement_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_{include_qoq}_raw.json",
                    "w",
                ) as f:
                    em_df.to_json(f, force_ascii=False, indent=2)

                # 格式化利润表数据
                em_dfs = create_category_income_statement_dataframes(em_df, include_yoy, include_qoq)

                # 生成分类后的markdown报告
                final_reports : dict[str, TradingReportResultPack] = {}
                for category_name, category_df in em_dfs.items():
                    table_str = format_pd_dataframe_to_markdown(
                        category_df, include_index=True, transpose=True, column_mapping=income_statement_column_mapping
                    )
                    final_reports[category_name] = TradingReportResultPack(
                        dataframe=category_df,
                        markdown_table=table_str,
                        json_dict=json.loads(category_df.to_json(force_ascii=False, indent=2)),
                    )

                # 保存分类后的markdown报告
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_income_statement_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_{include_qoq}_reports.md",
                    "w",
                ) as f:
                    for category_name, report_item in final_reports.items():
                        f.write(f"\n\n## {category_name}\n")
                        f.write(report_item.markdown_table)
                        f.write("\n")

                # 保存分类后的JSON报告
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_income_statement_{market_code.value}_{symbol}_{report_date_type.value}_{include_yoy}_{include_qoq}_reports.json",
                    "w",
                ) as f:
                    r = {}
                    for k, v in final_reports.items():
                        r[k] = v.json_dict
                    json.dump(r, f, ensure_ascii=False, indent=2)
                return final_reports
            else:
                return {}
    return {}


if __name__ == "__main__":

    async def main():
        os.makedirs("./logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        await em_retrieve_company_financial_analysis_indicators(
            market_code=MarketCode.SH,
            symbol="600519",
            report_period_type=ReportDateType.BY_PERIOD,
            look_back_years=2,
        )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_code=MarketType.A_SHARE,
        #     symbol="600519",
        #     report_period_type=ReportPeriodType.QUARTERLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_code=MarketType.A_SHARE,
        #     symbol="600519",
        #     report_period_type=ReportPeriodType.YEARLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_code=MarketType.SZ,
        #     symbol="600519",
        #     report_period_type=ReportDateType.BY_PERIOD,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_code=MarketType.SZ,
        #     symbol="002240",
        #     report_period_type=ReportPeriodType.QUARTERLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_code=MarketType.SZ,
        #     symbol="002240",
        #     report_period_type=ReportPeriodType.YEARLY,
        #     look_back_years=2,
        # # )
        await em_retrieve_company_financial_analysis_cash_flow_statement(
            market_code=MarketCode.SH,
            symbol="600519",
            report_date_type=ReportDateType.ANNUAL,
            include_yoy=True,
            include_qoq=False,
            look_back_years=2,
        )
        await em_retrieve_company_financial_analysis_balance_sheet(
            market_code=MarketCode.SH,
            symbol="600519",
            report_date_type=ReportDateType.BY_PERIOD,
            include_yoy=True,
            look_back_years=2,
        )
        await em_retrieve_company_financial_analysis_income_statement(
            market_code=MarketCode.SH,
            symbol="600519",
            report_date_type=ReportDateType.BY_PERIOD,
            include_yoy=True,
            include_qoq=False,
            look_back_years=2,
        )
    # asyncio.run(akshare_retrieve_company_cash_flow_statement(
    #     market_code=MarketType.A_SHARE,
    #     symbol="SH600519",
    #     report_type=ReportType.YEARLY,
    #     look_back_years=3
    # ))
    asyncio.run(main())
