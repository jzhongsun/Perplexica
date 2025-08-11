import asyncio
import httpx
from novas_mcp.utils import format_pd_dataframe_to_markdown
from novas_mcp.trading_core import MarketType, ReportPeriodType
import pandas as pd
from datetime import datetime
import json
import os

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
    async with httpx.AsyncClient(
        headers=EM_HTTP_HEADERS_DEFAULT
    ) as client:
        analysis_type = "0"
        if report_period_type == ReportPeriodType.PERIODICALLY:
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


if __name__ == "__main__":

    async def main():
        os.makedirs("./logs", exist_ok=True)
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
        await em_retrieve_company_financial_analysis_indicators(
            market_type=MarketType.B_SHARE,
            symbol="002240",
            report_period_type=ReportPeriodType.PERIODICALLY,
            look_back_years=2,
        )
        await em_retrieve_company_financial_analysis_indicators(
            market_type=MarketType.B_SHARE,
            symbol="002240",
            report_period_type=ReportPeriodType.QUARTERLY,
            look_back_years=2,
        )
        await em_retrieve_company_financial_analysis_indicators(
            market_type=MarketType.B_SHARE,
            symbol="002240",
            report_period_type=ReportPeriodType.YEARLY,
            look_back_years=2,
        )

    # asyncio.run(akshare_retrieve_company_cash_flow_statement(
    #     market_type=MarketType.A_SHARE,
    #     symbol="SH600519",
    #     report_type=ReportType.YEARLY,
    #     look_back_years=3
    # ))
    asyncio.run(main())
