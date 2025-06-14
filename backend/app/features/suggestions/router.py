"""Suggestions router module."""
from fastapi import APIRouter, Depends

from .service import SuggestionsService
from .schemas import SuggestionsRequest, SuggestionsResponse

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

@router.post("", response_model=SuggestionsResponse)
async def get_suggestions(
    request: SuggestionsRequest,
    suggestions_service: SuggestionsService = Depends(SuggestionsService)
) -> SuggestionsResponse:
    """Get suggestions based on query."""
    return await suggestions_service.get_suggestions(request) 