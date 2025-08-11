import akshare as ak
import pandas as pd
from datetime import datetime
from trading_core import MarketType, ReportPeriodType
import asyncio
import json


def get_main_cash_flow_columns():
    """获取现金流量表主要项目的列名"""
    return [
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


def get_main_cash_flow_column_mapping():
    """现金流量表主要项目列名映射字典"""
    return {
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


async def akshare_retrieve_company_cash_flow_statement(
    market_type: MarketType,
    symbol: str,
    report_type: ReportPeriodType,
    look_back_years: int,
) -> str:
    """
    股票-财务分析-现金流量表-获取现金流量表数据
    Args:
        market_type: The market type of the stock symbol
        symbol: The symbol of the stock to retrieve cash flow statement for
        report_type: The type of the cash flow statement to retrieve, such as 'quarterly', 'yearly' or 'report_period'
        look_back_years: The number of years to look back for the cash flow statement, default is 5
    Returns:
        str: The cash flow statement data in markdown format
    """
    loop = asyncio.get_event_loop()
    # 获取现金流量表数据
    if report_type == ReportPeriodType.PERIODICALY:
        ak_df = await loop.run_in_executor(
            None, ak.stock_cash_flow_sheet_by_report_em, symbol
        )
    elif report_type == ReportPeriodType.QUARTERLY:
        ak_df = await loop.run_in_executor(
            None, ak.stock_cash_flow_sheet_by_quarterly_em, symbol
        )
    elif report_type == ReportPeriodType.YEARLY:
        ak_df = await loop.run_in_executor(
            None, ak.stock_cash_flow_sheet_by_yearly_em, symbol
        )
    else:
        raise ValueError(f"Invalid report type: {report_type}")

    # 1. 使用 look_back_years 变量进行数据筛选
    if "REPORT_DATE" in ak_df.columns:
        # 将报告日期转换为datetime类型
        ak_df["REPORT_DATE"] = pd.to_datetime(ak_df["REPORT_DATE"])

        # 计算截止日期
        cutoff_date = datetime(datetime.now().year - look_back_years, 1, 1)

        # 筛选指定年份内的数据
        ak_df = ak_df[ak_df["REPORT_DATE"] >= cutoff_date].copy()

        # 按报告日期降序排列（最新的在前）
        ak_df = ak_df.sort_values("REPORT_DATE", ascending=False)

    # 2. 筛选现金流量表主要项目相关的列
    main_columns = get_main_cash_flow_columns()

    # 只保留存在的主要现金流量相关列
    available_columns = []
    for col in main_columns:
        if col in ak_df.columns:
            available_columns.append(col)

    # 筛选数据，只保留主要现金流量列
    ak_df = ak_df[available_columns].copy()

    # 3. 调整列名为可读的名称
    column_mapping = get_main_cash_flow_column_mapping()

    # 重命名存在的列
    columns_to_rename = {}
    for old_name, new_name in column_mapping.items():
        if old_name in ak_df.columns:
            columns_to_rename[old_name] = new_name

    if columns_to_rename:
        ak_df = ak_df.rename(columns=columns_to_rename)

    # 重置索引
    ak_df = ak_df.reset_index(drop=True)

    # 4. 行列转置：将报告期作为列，财务指标作为行
    if "报告期名称" in ak_df.columns and len(ak_df) > 0:
        # 使用报告期名称作为列标识
        ak_df_transposed = ak_df.set_index("报告期名称").T

        # 重新排列列顺序，最新的期间在最前面
        columns_order = ak_df_transposed.columns.tolist()
        ak_df_transposed = ak_df_transposed[columns_order]

        # 删除报告期行（因为已经作为列名了）
        if "报告期" in ak_df_transposed.index:
            ak_df_transposed = ak_df_transposed.drop("报告期")

        # 重置索引，让财务指标名称作为第一列
        ak_df_transposed = ak_df_transposed.reset_index()
        ak_df_transposed = ak_df_transposed.rename(columns={"index": "财务指标"})

        # 使用转置后的数据
        final_df = ak_df_transposed
    else:
        final_df = ak_df
    # print(final_df)
    markdown_table = final_df.to_markdown(index=False)
    print(f"{markdown_table}")


if __name__ == "__main__":
    import asyncio

    # asyncio.run(akshare_retrieve_company_cash_flow_statement(
    #     market_type=MarketType.A_SHARE,
    #     symbol="SH600519",
    #     report_type=ReportType.YEARLY,
    #     look_back_years=3
    # ))
    asyncio.run(
        akshare_retrieve_company_financial_analysis_indicators(
            market_type=MarketType.A_SHARE,
            symbol="600519.SH",
            report_type=ReportPeriodType.YEARLY,
            look_back_years=3,
        )
    )

    # stock_balance_sheet_by_report_em_df = ak.stock_balance_sheet_by_report_em(
    #     symbol="SH600519"
    # )
    # print(stock_balance_sheet_by_report_em_df)

    # stock_balance_sheet_by_yearly_em_df = ak.stock_balance_sheet_by_yearly_em(
    #     symbol="SH600519"
    # )
    # print(stock_balance_sheet_by_yearly_em_df)

    # stock_profit_sheet_by_report_em_df = ak.stock_profit_sheet_by_report_em(
    #     symbol="SH600519"
    # )
    # print(stock_profit_sheet_by_report_em_df)

    # stock_profit_sheet_by_yearly_em_df = ak.stock_profit_sheet_by_yearly_em(
    #     symbol="SH600519"
    # )
    # print(stock_profit_sheet_by_yearly_em_df)

    # stock_profit_sheet_by_quarterly_em_df = ak.stock_profit_sheet_by_quarterly_em(
    #     symbol="SH600519"
    # )
    # print(stock_profit_sheet_by_quarterly_em_df)

    # stock_cash_flow_sheet_by_report_em_df = ak.stock_cash_flow_sheet_by_report_em(
    #     symbol="SH600519"
    # )
    # print(stock_cash_flow_sheet_by_report_em_df)

    # stock_cash_flow_sheet_by_yearly_em_df = ak.stock_cash_flow_sheet_by_yearly_em(
    #     symbol="SH601398"
    # )
    # print(stock_cash_flow_sheet_by_yearly_em_df)

    # stock_cash_flow_sheet_by_quarterly_em_df = ak.stock_cash_flow_sheet_by_quarterly_em(
    #     symbol="SH601398"
    # )
    # print(stock_cash_flow_sheet_by_quarterly_em_df)

    # stock_balance_sheet_by_report_delisted_em_df = (
    #     ak.stock_balance_sheet_by_report_delisted_em(symbol="SZ000013")
    # )
    # print(stock_balance_sheet_by_report_delisted_em_df)

    # stock_profit_sheet_by_report_delisted_em_df = (
    #     ak.stock_profit_sheet_by_report_delisted_em(symbol="SZ000013")
    # )
    # print(stock_profit_sheet_by_report_delisted_em_df)

    # stock_cash_flow_sheet_by_report_delisted_em_df = (
    #     ak.stock_cash_flow_sheet_by_report_delisted_em(symbol="SZ000013")
    # )
    # print(stock_cash_flow_sheet_by_report_delisted_em_df)
