from typing import List, Optional
from pydantic import BaseModel, Field

class EmbeddingRequest(BaseModel):
    """Single text embedding request."""
    text: str = Field(..., description="Text to generate embedding for")
    model: Optional[str] = Field("text-embedding-3-small", description="OpenAI embedding model to use")

class BatchEmbeddingRequest(BaseModel):
    """Batch text embedding request."""
    texts: List[str] = Field(..., description="List of texts to generate embeddings for")
    model: Optional[str] = Field("text-embedding-3-small", description="OpenAI embedding model to use")

class EmbeddingResponse(BaseModel):
    """Single text embedding response."""
    embedding: List[float] = Field(..., description="Text embedding vector")
    model: str = Field(..., description="Model used for embedding")
    text: str = Field(..., description="Original text")
    token_count: int = Field(..., description="Number of tokens in the text")
    extra_info: dict = Field(default_factory=dict, description="Additional metadata about the embedding")

class BatchEmbeddingResponse(BaseModel):
    """Batch text embedding response."""
    embeddings: List[List[float]] = Field(..., description="List of text embedding vectors")
    model: str = Field(..., description="Model used for embedding")
    texts: List[str] = Field(..., description="Original texts")
    token_counts: List[int] = Field(..., description="Number of tokens in each text")
    extra_info: dict = Field(default_factory=dict, description="Additional metadata about the embeddings") 