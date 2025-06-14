from fastapi import APIRouter, Depends
from .service import EmbeddingService
from .schemas import (
    EmbeddingRequest,
    BatchEmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingResponse
)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

@router.post("/create", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(EmbeddingService)
) -> EmbeddingResponse:
    """Create embedding for a single text."""
    return await embedding_service.create_embedding(request)

@router.post("/batch", response_model=BatchEmbeddingResponse)
async def create_batch_embeddings(
    request: BatchEmbeddingRequest,
    embedding_service: EmbeddingService = Depends(EmbeddingService)
) -> BatchEmbeddingResponse:
    """Create embeddings for multiple texts."""
    return await embedding_service.create_batch_embeddings(request) 