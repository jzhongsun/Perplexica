from typing import Dict, List
from fastapi import HTTPException

from app.core.config import get_settings, update_settings
from app.features.providers import (
    get_available_chat_model_providers,
    get_available_embedding_model_providers
)
from .schemas import ConfigResponse, ConfigUpdate, ModelInfo

class ConfigService:
    """Service for managing application configuration."""

    async def get_config(self) -> ConfigResponse:
        """Get current configuration."""
        settings = get_settings()
        
        chat_providers = await get_available_chat_model_providers()
        embedding_providers = await get_available_embedding_model_providers()

        # Convert providers to response format
        chat_model_providers: Dict[str, List[ModelInfo]] = {}
        embedding_model_providers: Dict[str, List[ModelInfo]] = {}

        for provider, models in chat_providers.items():
            chat_model_providers[provider] = [
                ModelInfo(
                    name=model_name,
                    displayName=model_info.get("displayName", model_name)
                )
                for model_name, model_info in models.items()
            ]

        for provider, models in embedding_providers.items():
            embedding_model_providers[provider] = [
                ModelInfo(
                    name=model_name,
                    displayName=model_info.get("displayName", model_name)
                )
                for model_name, model_info in models.items()
            ]

        return ConfigResponse(
            chatModelProviders=chat_model_providers,
            embeddingModelProviders=embedding_model_providers,
            openaiApiKey=settings.OPENAI_API_KEY,
            ollamaApiUrl=settings.OLLAMA_API_ENDPOINT,
            lmStudioApiUrl=settings.LMSTUDIO_API_ENDPOINT,
            anthropicApiKey=settings.ANTHROPIC_API_KEY,
            groqApiKey=settings.GROQ_API_KEY,
            geminiApiKey=settings.GEMINI_API_KEY,
            deepseekApiKey=settings.DEEPSEEK_API_KEY,
            customOpenaiApiUrl=settings.CUSTOM_OPENAI_API_URL,
            customOpenaiApiKey=settings.CUSTOM_OPENAI_API_KEY,
            customOpenaiModelName=settings.CUSTOM_OPENAI_MODEL_NAME
        )

    async def update_config(self, config_update: ConfigUpdate) -> None:
        """Update configuration value."""
        try:
            await update_settings(config_update)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            ) 