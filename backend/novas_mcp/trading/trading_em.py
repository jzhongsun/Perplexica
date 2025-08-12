import asyncio
import httpx
from novas_mcp.utils import format_pd_dataframe_to_markdown
from novas_mcp.trading_core import MarketType, ReportPeriodType
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
    market_type: MarketType,
    symbol: str,
    report_period_type: ReportPeriodType,
    look_back_years: int,
) -> dict[str, str]:
    """
    获取股票财务分析指标，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#zyzb-0
    Args:
        market_type: 市场类型
        symbol: 股票代码
        report_period_type: 报告期类型
        look_back_years: 回溯年数

    """

    security_code = symbol.replace(".", "").replace("SH", "").replace("SZ", "")
    if market_type == MarketType.A_SHARE:
        symbol = "SH" + security_code
    elif market_type == MarketType.B_SHARE:
        symbol = "SZ" + security_code

    def get_financial_indicator_mapping(report_period_type: ReportPeriodType):
        """财务分析指标中文映射字典 - 基于akshare实际列名"""
        return {
            # 每股指标
            "EPSJB": (
                "摊薄每股收益(元)"
                if report_period_type == ReportPeriodType.QUARTERLY
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

    def get_financial_indicator_categories():
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

    def create_category_dataframes(df, report_period_type: ReportPeriodType):
        """将财务数据按分类分拆成多个DataFrame"""
        indicator_mapping = get_financial_indicator_mapping(report_period_type)
        categories = get_financial_indicator_categories()

        def format_large_numbers(value):
            """格式化大数字为中文格式（如：514.4亿）"""
            if pd.isna(value) or value == 0:
                return value

            # 对于绝对值大于1亿的数字，转换为"亿"为单位
            if abs(value) >= 100000000:
                return f"{value / 100000000:.2f}亿"
            # 对于绝对值大于1万的数字，转换为"万"为单位
            elif abs(value) >= 10000:
                return f"{value / 10000:.2f}万"
            else:
                return f"{value:.2f}"

        category_dataframes = {}

        for category_name, indicators in categories.items():
            # 获取该分类下存在的指标
            available_indicators = [
                indicator for indicator in indicators if indicator in df.index
            ]

            if available_indicators:
                # 创建该分类的DataFrame
                category_df = df.loc[available_indicators].copy()

                # 将指标名称映射为中文
                chinese_names = []
                for indicator in available_indicators:
                    chinese_name = indicator_mapping.get(indicator, indicator)
                    chinese_names.append(chinese_name)

                # 设置中文指标名称为索引
                category_df.index = chinese_names
                category_df.index.name = category_name

                # 格式化数值：对于收入、利润等大数字使用中文格式
                for col in category_df.columns:
                    for indicator in available_indicators:
                        if indicator in [
                            "TOTALOPERATEREVE",
                            "GROSS_PROFIT",
                            "PARENTNETPROFIT",
                            "DEDU_PARENT_PROFIT",
                        ]:
                            # 这些是大数字指标，需要格式化
                            if indicator in df.index:
                                row_idx = chinese_names[
                                    available_indicators.index(indicator)
                                ]
                                if row_idx in category_df.index:
                                    category_df.loc[row_idx, col] = (
                                        format_large_numbers(
                                            category_df.loc[row_idx, col]
                                        )
                                    )

                category_dataframes[category_name] = category_df

        return category_dataframes

    ak_df: pd.DataFrame = None
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        analysis_type = "0"
        if report_period_type == ReportPeriodType.BY_PERIOD:
            analysis_type = "0"
        elif report_period_type == ReportPeriodType.YEARLY:
            analysis_type = "1"
        elif report_period_type == ReportPeriodType.QUARTERLY:
            analysis_type = "2"
        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type={analysis_type}&code={symbol}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        if data["data"]:
            ak_df = pd.DataFrame(data["data"])
        else:
            return {"success": False, "error": "No data found"}

    ak_df.to_json(
        f"./logs/em_retrieve_company_financial_analysis_indicators_{market_type.value}_{symbol}_{report_period_type.value}_raw.json",
        force_ascii=False,
        indent=2,
    )

    # 筛选指定年份内的数据
    if "REPORT_DATE" in ak_df.columns:
        ak_df["REPORT_DATE"] = pd.to_datetime(ak_df["REPORT_DATE"])
        cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)
        ak_df = ak_df[ak_df["REPORT_DATE"] >= cutoff_date].copy()
        ak_df = ak_df.sort_values("REPORT_DATE", ascending=False)

    # 处理报告期名称，转换为简化格式 (如 "25-03-31")
    if "REPORT_DATE" in ak_df.columns:

        def format_date_name(date_obj):
            if pd.isna(date_obj):
                return str(date_obj)
            # 将datetime对象转换为 "YY-MM-DD" 格式
            year = str(date_obj.year)[-2:]  # 取年份后两位
            month = f"{date_obj.month:02d}"  # 月份补零
            day = f"{date_obj.day:02d}"  # 日期补零
            return f"{year}-{month}-{day}"

        # 创建报告期名称列
        ak_df["REPORT_DATE_NAME"] = ak_df["REPORT_DATE"].apply(format_date_name)

    # 设置索引并转置
    if "REPORT_DATE_NAME" in ak_df.columns and len(ak_df) > 0:
        # 使用报告期名称作为列标识
        ak_df_transposed = ak_df.set_index("REPORT_DATE_NAME").T

        # 删除不需要的行
        rows_to_drop = [
            "REPORT_DATE",
            "SECUCODE",
            "SECURITY_CODE",
            "SECURITY_NAME_ABBR",
        ]
        for row in rows_to_drop:
            if row in ak_df_transposed.index:
                ak_df_transposed = ak_df_transposed.drop(row)

        # 按分类分拆数据
        category_dataframes = create_category_dataframes(
            ak_df_transposed, report_period_type
        )

        # 格式化每个分类的表格
        reports = {}
        for category_name, category_df in category_dataframes.items():
            table_str = format_pd_dataframe_to_markdown(category_df, include_index=True)
            reports[category_name] = table_str

        with open(
            f"./logs/em_retrieve_company_financial_analysis_indicators_{market_type.value}_{symbol}_{report_period_type.value}_reports.json",
            "w",
        ) as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)

        with open(
            f"./logs/em_retrieve_company_financial_analysis_indicators_{market_type.value}_{symbol}_{report_period_type.value}_reports.md",
            "w",
        ) as f:
            for category_name, table_str in reports.items():
                f.write(f"\n\n## {category_name}\n")
                f.write(table_str)
                f.write("\n")

        return {"success": True, "reports": reports}
    else:
        # 如果没有合适的数据，返回原始格式
        return {}


async def em_retrieve_company_financial_analysis_cash_flow_statement(
    market_type: MarketType,
    symbol: str,
    report_period_type: ReportPeriodType,
    report_type: str,
    look_back_years: int,
) -> dict[str, str]:
    """
    获取股票财务分析现金流量表，按中文格式输出, https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#xjll-0
    Args:
        market_type: 市场类型
        symbol: 股票代码
        report_period_type: 报告期类型
        report_type: 报告类型: 按报告期 | 按年度 | 按单季度 | 报告期同比 | 年度同比 | 单季度环比
        look_back_years: 回溯年数
    """
    """
    - 按报告期 | 按年度 | 按单季度 | 报告期同比 | 年度同比 | 单季度环比
    """

    def format_cash_flow_statement_dataframe(
        df: pd.DataFrame, report_period_type: ReportPeriodType
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

        # 现金流量表主要项目列名映射字典
        column_mapping = {
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

        def format_large_numbers(value):
            """格式化大数字为中文格式（如：514.4亿）"""
            if pd.isna(value) or value == 0:
                return value

            # 对于绝对值大于1亿的数字，转换为"亿"为单位
            if abs(value) >= 100000000:
                return f"{value / 100000000:.2f}亿"
            # 对于绝对值大于1万的数字，转换为"万"为单位
            elif abs(value) >= 10000:
                return f"{value / 10000:.2f}万"
            else:
                return f"{value:.2f}"

        # 1. 筛选现金流量表主要项目相关的列
        available_columns = []
        for col in main_cash_flow_columns:
            if col in df.columns:
                available_columns.append(col)

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
            available_indicators = []
            for indicator in indicators:
                if indicator in df.columns:
                    available_indicators.append(indicator)

            if available_indicators:
                # 创建该分类的DataFrame，包含报告期名称列
                category_columns = ["REPORT_DATE_NAME"] + available_indicators
                category_data = df[category_columns].copy()

                # 设置报告期名称作为索引
                category_data = category_data.set_index("REPORT_DATE_NAME")
                category_data.index.name = category_name

                # 在转置前先将英文列名映射为中文
                columns_to_rename = {}
                for old_name, new_name in column_mapping.items():
                    if old_name in category_data.columns:
                        columns_to_rename[old_name] = new_name

                if columns_to_rename:
                    category_data = category_data.rename(columns=columns_to_rename)

                # 转置数据：让报告期作为列，财务指标作为行
                category_data = category_data.T

                # 转置后，原来的列名（财务指标）变成了行索引
                # 原来的行索引（报告期）变成了列名
                # 现在需要重置索引，让财务指标名称作为第一列
                category_data = category_data.reset_index()
                category_data = category_data.rename(columns={"index": category_name})

                # # 格式化数值：对于现金流量相关的大数字使用中文格式
                # for col in category_data.columns:
                #     for idx, value in category_data[col].items():
                #         if pd.notna(value) and isinstance(value, (int, float)):
                #             # 对于现金流量相关的大数字进行格式化
                #             if abs(value) >= 10000:
                #                         category_data.loc[idx, col] = format_large_numbers(value)

                category_dataframes[category_name] = category_data

        return category_dataframes

    if report_type == '按报告期':
        em_report_date_type = "0"
        em_report_type = "1"
    elif report_type == '按年度':
        em_report_date_type = "1"
        em_report_type = "1"
    elif report_type == '按单季度':
        em_report_date_type = "0"
        em_report_type = "2"
    elif report_type == '报告期同比':
        em_report_date_type = "0"
        em_report_type = "1"
    elif report_type == '年度同比':
        em_report_date_type = "1"
        em_report_type = "1"
    elif report_type == '单季度环比':
        em_report_date_type = "0"
        em_report_type = "2"
    else:
        raise ValueError(f"Invalid report type: {report_type}")

    em_company_type = "4"
    em_code = symbol.replace(".", "").replace("SH", "").replace("SZ", "")
    if market_type == MarketType.A_SHARE:
        em_code = "SH" + em_code
    elif market_type == MarketType.B_SHARE:
        em_code = "SZ" + em_code
    cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)
    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
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
            return {"success": False, "error": "No data found"}
        else:
            logger.info(f"Found {len(filtered_reports)} reports: {filtered_reports}")
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
                    f"./logs/em_retrieve_company_financial_analysis_cash_flow_statement_{market_type.value}_{symbol}_{report_period_type.value}_{report_type}_raw.json",
                    "w",
                ) as f:
                    em_df.to_json(f, force_ascii=False, indent=2)

                # 格式化现金流量表数据
                em_df = format_cash_flow_statement_dataframe(em_df, report_period_type)

                # 生成分类后的markdown报告
                reports = {}
                for category_name, category_df in em_df.items():
                    table_str = format_pd_dataframe_to_markdown(
                        category_df, include_index=False
                    )
                    reports[category_name] = table_str

                # 保存分类后的markdown报告
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_cash_flow_statement_{market_type.value}_{symbol}_{report_period_type.value}_{report_type}_reports.md",
                    "w",
                ) as f:
                    for category_name, table_str in reports.items():
                        f.write(f"\n\n## {category_name}\n")
                        f.write(table_str)
                        f.write("\n")

                # 保存分类后的JSON报告
                with open(
                    f"./logs/em_retrieve_company_financial_analysis_cash_flow_statement_{market_type.value}_{symbol}_{report_period_type.value}_{report_type}_reports.json",
                    "w",
                ) as f:
                    json.dump(reports, f, ensure_ascii=False, indent=2)

            else:
                return {"success": False, "error": "No data found"}
        return {"success": True, "reports": reports}


if __name__ == "__main__":

    async def main():
        os.makedirs("./logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_type=MarketType.A_SHARE,
        #     symbol="600519",
        #     report_period_type=ReportPeriodType.PERIODICALLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_type=MarketType.A_SHARE,
        #     symbol="600519",
        #     report_period_type=ReportPeriodType.QUARTERLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_type=MarketType.A_SHARE,
        #     symbol="600519",
        #     report_period_type=ReportPeriodType.YEARLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_type=MarketType.B_SHARE,
        #     symbol="002240",
        #     report_period_type=ReportPeriodType.PERIODICALLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_type=MarketType.B_SHARE,
        #     symbol="002240",
        #     report_period_type=ReportPeriodType.QUARTERLY,
        #     look_back_years=2,
        # )
        # await em_retrieve_company_financial_analysis_indicators(
        #     market_type=MarketType.B_SHARE,
        #     symbol="002240",
        #     report_period_type=ReportPeriodType.YEARLY,
        #     look_back_years=2,
        # )
        await em_retrieve_company_financial_analysis_cash_flow_statement(
            market_type=MarketType.A_SHARE,
            symbol="600519",
            report_period_type=ReportPeriodType.QUARTERLY,
            report_type="2",
            look_back_years=1,
        )

    # asyncio.run(akshare_retrieve_company_cash_flow_statement(
    #     market_type=MarketType.A_SHARE,
    #     symbol="SH600519",
    #     report_type=ReportType.YEARLY,
    #     look_back_years=3
    # ))
    asyncio.run(main())
