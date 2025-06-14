"""Models service module."""
from typing import Dict
from fastapi import HTTPException

from .schemas import ModelInfo, ModelsResponse

_chat_models = {
    "openai": {
        "gpt-4": ModelInfo(
            name="GPT-4",
            description="Advanced language model with strong reasoning capabilities",
            type="chat",
            capabilities=["chat", "completion", "reasoning"],
            parameters={
                "temperature": 0.7,
                "max_tokens": 4096
            }
        ),
        "gpt-3.5-turbo": ModelInfo(
            name="GPT-3.5 Turbo",
            description="Fast and efficient language model",
            type="chat",
            capabilities=["chat", "completion"],
            parameters={
                "temperature": 0.7,
                "max_tokens": 4096
            }
        )
    },
    "anthropic": {
        "claude-2": ModelInfo(
            name="Claude 2",
            description="Advanced language model with strong reasoning and analysis capabilities",
            type="chat",
            capabilities=["chat", "completion", "reasoning", "analysis"],
            parameters={
                "temperature": 0.7,
                "max_tokens": 8192
            }
        )
    }
}

_embedding_models = {
    "openai": {
        "text-embedding-ada-002": ModelInfo(
            name="Text Embedding Ada 002",
            description="Efficient text embedding model",
            type="embedding",
            capabilities=["embedding"],
            parameters={
                "dimensions": 1536
            }
        )
    }
}

class ModelService:
    """Model service class."""
    
    def __init__(self):
        """Initialize model service."""
        # Hardcoded providers and models for now, replace with database/config in production

    
    async def list_models(self) -> ModelsResponse:
        """List all available models grouped by provider."""
        return ModelsResponse(
            chat_model_providers=_chat_models,
            embedding_model_providers=_embedding_models
        )
    
    async def get_model(self, provider: str, model_id: str, model_type: str = "chat") -> ModelInfo:
        """Get model by provider and ID."""
        models = _chat_models if model_type == "chat" else _embedding_models
        
        if provider not in models:
            raise HTTPException(status_code=404, detail="Provider not found")
            
        provider_models = models[provider]
        if model_id not in provider_models:
            raise HTTPException(status_code=404, detail="Model not found")
            
        return provider_models[model_id] 