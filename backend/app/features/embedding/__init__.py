"""
Embedding feature module using Hugging Face transformers
"""

from .router import router
from .service import EmbeddingService
from .schemas import EmbeddingRequest, EmbeddingResponse, BatchEmbeddingRequest

__all__ = [
    "router",
    "EmbeddingService",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "BatchEmbeddingRequest"
] 