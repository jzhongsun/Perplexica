from typing import Annotated
from datetime import datetime

from .trading_core import (
    RetrieveCompanyNewsRequest,
    RetrieveCompanyNewsResponse,
    _retrieve_company_news,
)
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def setup_trading_webapi_server(app: FastAPI):
    @app.get("/api/trading/news", response_model=RetrieveCompanyNewsResponse)
    async def retrieve_company_news(
        company_name: Annotated[
            str, "The name of the company to retrieve financial news for"
        ],
        language: str = "en",
        num_results: int = 10,
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
