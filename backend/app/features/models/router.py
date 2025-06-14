"""Models router module."""
from fastapi import APIRouter, Depends, Query
from loguru import logger
from .service import ModelService
from .schemas import ModelInfo, ModelsResponse

router = APIRouter(prefix="/models", tags=["models"])

@router.get("", response_model=ModelsResponse)
async def list_models(
    model_service: ModelService = Depends(ModelService)
) -> ModelsResponse:
    """List available models grouped by provider."""
    response = await model_service.list_models()
    logger.info(f"Models response: {response}")
    return response

@router.get("/{provider}/{model_id}", response_model=ModelInfo)
async def get_model(
    provider: str,
    model_id: str,
    model_type: str = Query(default="chat", description="Model type (chat or embedding)"),
    model_service: ModelService = Depends(ModelService)
) -> ModelInfo:
    """Get model by provider and ID."""
    return await model_service.get_model(provider, model_id, model_type) 