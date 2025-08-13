import akshare as ak
import pandas as pd
from datetime import datetime
import asyncio
import json


if __name__ == "__main__":
    import asyncio

    stock_balance_sheet_by_report_em_df = ak.stock_zh_a_hist(
        symbol="SH600519"
    )
    print(stock_balance_sheet_by_report_em_df)

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
