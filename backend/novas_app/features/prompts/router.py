from typing import List
from fastapi import APIRouter, Depends
from .service import PromptService
from .schemas import PromptTemplate, PromptRequest, PromptResponse

router = APIRouter(prefix="/prompts", tags=["prompts"])

@router.get("/templates", response_model=List[PromptTemplate])
async def list_templates(
    prompt_service: PromptService = Depends(PromptService)
) -> List[PromptTemplate]:
    """List all available prompt templates."""
    return prompt_service.list_templates()

@router.get("/templates/{template_name}", response_model=PromptTemplate)
async def get_template(
    template_name: str,
    prompt_service: PromptService = Depends(PromptService)
) -> PromptTemplate:
    """Get a specific template by name."""
    return prompt_service.get_template(template_name)

@router.post("/generate", response_model=PromptResponse)
async def generate_prompt(
    request: PromptRequest,
    prompt_service: PromptService = Depends(PromptService)
) -> PromptResponse:
    """Generate a prompt using a template and variables."""
    return prompt_service.generate_prompt(request) 