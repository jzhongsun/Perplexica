from typing import Optional
from fastapi import APIRouter, Depends

from .schemas import SearchResponse
from .service import SearxngService

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/", response_model=SearchResponse)
async def search(
    q: str,
    categories: Optional[str] = None,
    engines: Optional[str] = None,
    language: Optional[str] = None,
    pageno: Optional[int] = None,
    searxng_service: SearxngService = Depends(SearxngService)
) -> SearchResponse:
    """
    Search endpoint using SearXNG.
    """
    return await searxng_service.search(
        query=q,
        categories=categories,
        engines=engines,
        language=language,
        pageno=pageno
    ) 