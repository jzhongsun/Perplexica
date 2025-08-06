from semantic_kernel.functions import kernel_function, KernelFunction
from typing import Annotated


@kernel_function(
    name="get_yfin_data",
    description="Get the YFin data for a given company",
    input_schema=["symbol", "start_date", "end_date"],
)
async def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    return "YFin data"


@kernel_function(
    name="get_stockstats_indicators_report",
)
async def get_stockstats_indicators_report(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    return "Stockstats indicators report"
