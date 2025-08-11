from typing import Annotated
from datetime import datetime

from .web_core import (
    WebSearchRequest,
    WebSearchResponse,
    _web_search,
)
from mcp.server.fastmcp import FastMCP
import logging
def setup_web_mcp(mcp: FastMCP):
    @mcp.tool(name="web_search", description="Search the web for information")
    async def web_search(request: WebSearchRequest) -> WebSearchResponse:
        return await _web_search(request)