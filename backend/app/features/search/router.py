"""Search router module."""
from fastapi import APIRouter, Depends

from .service import SearchService
from .schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(SearchService)
) -> SearchResponse:
    """Perform search based on request."""
    return await search_service.search(request) 