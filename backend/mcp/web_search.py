import os
from typing import Dict, Any
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SearXngSearchRequest(BaseModel):
    query: str
    language: str = "en"


class SearXngSearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    thumbnail: str | None = ""
    category: str | None = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearXngSearchResults(BaseModel):
    query: str
    num_results: int = 0
    results: list[SearXngSearchResult]
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def _seaxng_web_search(query: str, language: str = "en") -> SearXngSearchResults:
    import httpx

    searxng_base_url = os.getenv("SEARXNG_BASE_URL")
    logger.info(f"searxng_base_url: {searxng_base_url}")

    # Prepare search parameters
    params = {"q": query, "format": "json"}
    params["language"] = "auto"
    if language and len(language) > 0:
        params["language"] = language
    params["categories"] = "general"
    params["engines"] = "baidu,sogou"

    # if categories:
    #     params["categories"] = categories
    # if engines:
    #     params["engines"] = engines
    # if language:
    #     params["language"] = language
    # if pageno:
    #     params["pageno"] = str(pageno)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            urljoin(searxng_base_url, "search"), params=params, timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"searxng_search_results = {data}")
        results = data["results"] if "results" in data else []
        search_results = SearXngSearchResults(
            query=data["query"],
            num_results=data["number_of_results"],
            results=[],
            metadata={},
        )
        for r in results:
            search_result = SearXngSearchResult(
                url=r["url"],
                title=r["title"],
                snippet=r["content"],
                thumbnail=r["thumbnail"],
                category=r["category"],
            )
            search_results.results.append(search_result)

        logger.info(
            f"search_results = {search_results.model_dump_json(indent=2, exclude_none=True)}"
        )
        return search_results


def setup_web_search(app: FastAPI):
    @app.post(
        "/api/v1/web_search", tags=["web_search"], response_model=SearXngSearchResults
    )
    async def web_search_api(request: SearXngSearchRequest) -> SearXngSearchResults:
        return await _seaxng_web_search(request.query, request.language)

    mcp = FastMCP(name="web_search", version="1.0.0", stateless_http=True)

    @mcp.tool(name="web_search", description="Search the web for information")
    async def web_search_mcp(request: SearXngSearchRequest) -> SearXngSearchResults:
        return await _seaxng_web_search(request.query, request.language)

    return mcp
