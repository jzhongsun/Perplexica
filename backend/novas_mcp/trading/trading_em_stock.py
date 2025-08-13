import akshare as ak
import pandas as pd
from datetime import datetime
import asyncio
import json
from novas_mcp.trading_core import MarketCode
import httpx

EM_HTTP_HEADERS_DEFAULT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

async def em_retrieve_stock_kline_data(
    market_code: MarketCode,
    symbol: str,
    period: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:    
    code = "0"
    if market_code == MarketCode.SH:
        code = "1"
    elif market_code == MarketCode.SZ:
        code = "0"
    else:
        raise ValueError(f"Invalid market code: {market_code}")
    # ak.stock_zh_a_hist()

    async with httpx.AsyncClient(headers=EM_HTTP_HEADERS_DEFAULT) as client:
        begin_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
        secid = f"{code}.{symbol}"
        adjust = ""
        adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
        adjust_code = adjust_dict[adjust]
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
        period = period_dict[period]
        url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&beg={begin_date}&end={end_date}&ut=fa5fd1943c7b386f172d6893dbfba10b&rtntype=6&secid={secid}&klt={period}&fqt={adjust_code}&cb=jsonp1755016757363"
        response = await client.get(url)
        response.raise_for_status()
        response_text = response.text.replace("jsonp1755016757363(", "").replace(");", "")
        response_json = json.loads(response_text)
        with open(f"./logs/em_retrieve_stock_kline_data_{market_code.value}_{symbol}_{period}_{start_date}_{end_date}_raw.json", "w") as f:
            json.dump(response_json, f, ensure_ascii=False, indent=2)
        # print(json.dumps(response_json, ensure_ascii=False, indent=2))
        if response_json["data"] and response_json["data"]["klines"]:
            formatted_json = []
            for kline in response_json["data"]["klines"]:
                formatted_json.append({
                    "日期": kline.split(",")[0],
                    "股票代码": symbol,
                    "开盘": kline.split(",")[1],
                    "收盘": kline.split(",")[2],
                    "最高": kline.split(",")[3],
                    "最低": kline.split(",")[4],
                    "成交量": kline.split(",")[5],
                    "成交额": kline.split(",")[6],
                    "振幅": kline.split(",")[7],
                    "涨跌幅": kline.split(",")[8],
                    "涨跌额": kline.split(",")[9],
                    "换手率": kline.split(",")[10],
                })
            df = pd.DataFrame(formatted_json)
            df.index = pd.to_datetime(df["日期"])
            df = df.sort_index()
            df = df[start_date:end_date]
            df["开盘"] = pd.to_numeric(df["开盘"], errors="coerce")
            df["收盘"] = pd.to_numeric(df["收盘"], errors="coerce")
            df["最高"] = pd.to_numeric(df["最高"], errors="coerce")
            df["最低"] = pd.to_numeric(df["最低"], errors="coerce")
            df["成交量"] = pd.to_numeric(df["成交量"], errors="coerce")
            df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")
            df["振幅"] = pd.to_numeric(df["振幅"], errors="coerce")
            df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
            df["涨跌额"] = pd.to_numeric(df["涨跌额"], errors="coerce")
            df["换手率"] = pd.to_numeric(df["换手率"], errors="coerce")
            df["日期"] = pd.to_datetime(df["日期"]).astype(str)
            df = df.reset_index(drop=True)
            with open(f"./logs/em_retrieve_stock_kline_data_{market_code.value}_{symbol}_{period}_{start_date}_{end_date}_formatted.json", "w") as f:
                df.to_json(f, force_ascii=False, indent=2)
            return df
        else:
            return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(em_retrieve_stock_kline_data(MarketCode.SH, "603777", "monthly", "2025-07-01", "2050-01-01"))
