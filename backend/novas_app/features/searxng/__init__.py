"""
SearXNG search feature module
"""

from .router import router
from .service import SearxngService
from .schemas import SearchResponse, SearchResult, SearchOptions

__all__ = ["router", "SearxngService", "SearchResponse", "SearchResult", "SearchOptions"]

from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx

from novas_app.core.config import get_settings

async def search_searxng(
    query: str,
    engines: Optional[List[str]] = None,
    language: str = "en",
    page: int = 1
) -> Dict[str, Any]:
    """Search using SearxNG.
    
    Args:
        query: Search query
        engines: List of search engines to use
        language: Search language
        page: Page number
        
    Returns:
        Search results
    """
    settings = get_settings()
    if not settings.SEARXNG_API_ENDPOINT:
        return {"results": [], "suggestions": []}

    params = {
        "q": query,
        "format": "json",
        "language": language,
        "pageno": page
    }

    if engines:
        params["engines"] = ",".join(engines)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                urljoin(settings.SEARXNG_API_ENDPOINT, "search"),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "results": data.get("results", []),
                "suggestions": data.get("suggestions", [])
            }
    except Exception as e:
        print(f"Error searching with SearxNG: {e}")
        return {"results": [], "suggestions": []} 