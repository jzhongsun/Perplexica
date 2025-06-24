from typing import Dict, List
from fastapi import HTTPException

from app.core.config import get_settings, update_settings
from .schemas import ConfigResponse, ConfigUpdate, ModelInfo

class ConfigService:
    """Service for managing application configuration."""

    async def get_config(self) -> ConfigResponse:
        """Get current configuration."""
        settings = get_settings()
        
        # Convert providers to response format
        return ConfigResponse(
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