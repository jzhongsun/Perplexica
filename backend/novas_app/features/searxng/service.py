from typing import Optional
import httpx
from urllib.parse import urljoin
from fastapi import HTTPException

from novas_app.core.config import get_settings
from .schemas import SearchResponse, SearchResult

class SearxngService:
    """Service for interacting with SearXNG."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.SEARXNG_API_URL

    async def search(
        self,
        query: str,
        categories: Optional[str] = None,
        engines: Optional[str] = None,
        language: Optional[str] = None,
        pageno: Optional[int] = None
    ) -> SearchResponse:
        """
        Perform a search using SearXNG API.
        
        Args:
            query: Search query
            categories: Comma-separated list of categories
            engines: Comma-separated list of engines
            language: Search language
            pageno: Page number
        
        Returns:
            SearchResponse object containing results and suggestions
        
        Raises:
            HTTPException: If the API call fails
        """
        # Prepare search parameters
        params = {"q": query, "format": "json"}
        
        if categories:
            params["categories"] = categories
        if engines:
            params["engines"] = engines
        if language:
            params["language"] = language
        if pageno:
            params["pageno"] = str(pageno)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    urljoin(self.base_url, "search"),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return SearchResponse(
                    results=[
                        SearchResult(**result)
                        for result in data.get("results", [])
                    ],
                    suggestions=data.get("suggestions", [])
                )
                
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calling SearXNG API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            ) 