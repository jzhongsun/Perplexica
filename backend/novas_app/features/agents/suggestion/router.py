from fastapi import APIRouter, Depends
from .service import SuggestionService
from .schemas import SuggestionRequest, SuggestionResponse

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

@router.post("", response_model=SuggestionResponse)
async def generate_suggestions(
    request: SuggestionRequest,
    suggestion_service: SuggestionService = Depends(SuggestionService)
) -> SuggestionResponse:
    """Generate search suggestions based on query and context."""
    return await suggestion_service.generate_suggestions(request) 