from typing import List, Optional
from openai import AsyncOpenAI
import tiktoken

from app.core.config import get_settings
from app.core.cache import get_redis
from .schemas import (
    EmbeddingRequest,
    BatchEmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingResponse
)

class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.redis = get_redis()
        self.default_model = "text-embedding-3-small"

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{model}:{text_hash}"

    def _count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text using tiktoken."""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except KeyError:
            # Fallback to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))

    async def _get_cached_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Get embedding from cache if available."""
        cache_key = self._get_cache_key(text, model)
        cached = await self.redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)
        return None

    async def _cache_embedding(self, text: str, model: str, embedding: List[float]) -> None:
        """Cache embedding for future use."""
        cache_key = self._get_cache_key(text, model)
        import json
        await self.redis.set(
            cache_key,
            json.dumps(embedding),
            ex=86400  # Cache for 24 hours
        )

    async def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embedding for a single text."""
        model = request.model or self.default_model
        
        # Check cache first
        cached_embedding = await self._get_cached_embedding(request.text, model)
        if cached_embedding:
            return EmbeddingResponse(
                embedding=cached_embedding,
                model=model,
                text=request.text,
                token_count=self._count_tokens(request.text, model)
            )
        
        # Generate new embedding
        response = await self.client.embeddings.create(
            model=model,
            input=request.text
        )
        
        embedding = response.data[0].embedding
        
        # Cache the result
        await self._cache_embedding(request.text, model, embedding)
        
        return EmbeddingResponse(
            embedding=embedding,
            model=model,
            text=request.text,
            token_count=self._count_tokens(request.text, model)
        )

    async def create_batch_embeddings(self, request: BatchEmbeddingRequest) -> BatchEmbeddingResponse:
        """Create embeddings for multiple texts."""
        model = request.model or self.default_model
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(request.texts):
            cached_embedding = await self._get_cached_embedding(text, model)
            if cached_embedding:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate new embeddings for uncached texts
        if uncached_texts:
            response = await self.client.embeddings.create(
                model=model,
                input=uncached_texts
            )
            
            # Update embeddings and cache
            for i, embedding_data in zip(uncached_indices, response.data):
                embeddings[i] = embedding_data.embedding
                await self._cache_embedding(request.texts[i], model, embedding_data.embedding)
        
        return BatchEmbeddingResponse(
            embeddings=embeddings,
            model=model,
            texts=request.texts,
            token_counts=[self._count_tokens(text, model) for text in request.texts]
        ) 