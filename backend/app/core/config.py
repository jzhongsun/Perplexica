from functools import lru_cache
from typing import Any, Dict, Optional
from loguru import logger
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Perplexica"
    
    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./perplexica.db"
    SQL_DEBUG: bool = False
    
    # SearxNG Settings
    SEARXNG_API_URL: str = "http://searxng:8080"
    
    # Weather Settings
    OPENMETEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPENMETEO_DEFAULT_UNITS: str = "metric"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Model Settings
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # Custom OpenAI Settings
    CUSTOM_OPENAI_API_URL: Optional[str] = None
    CUSTOM_OPENAI_API_KEY: Optional[str] = None
    CUSTOM_OPENAI_MODEL_NAME: Optional[str] = None
    
    # LM Studio Settings
    LM_STUDIO_API_URL: str = ""
    
    # Ollama Settings
    OLLAMA_API_URL: str = ""
    
    # YouTube Settings
    YOUTUBE_API_KEY: str = ""
    
    # Google Custom Search Settings
    GOOGLE_CUSTOM_SEARCH_API_KEY: str = ""
    GOOGLE_CUSTOM_SEARCH_ENGINE_ID: str = ""
    
    # New fields
    OLLAMA_API_ENDPOINT: Optional[str] = None
    LMSTUDIO_API_ENDPOINT: Optional[str] = None
    SEARXNG_API_ENDPOINT: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

_settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return _settings

async def update_settings(config_update: Dict[str, Any]) -> None:
    """Update settings value.
    
    Args:
        key: Setting key to update
        value: New value for the setting
        
    Raises:
        ValueError: If key is not a valid setting
    """
    for key, value in config_update.items():
        if not hasattr(_settings, key):
            logger.error(f"Invalid setting key: {key} and its value: {value}")
            continue
        logger.info(f"Updating setting: {key} to {value}")
        # Update the setting
        setattr(_settings, key, value)
    logger.info(f"Settings updated: {_settings.model_dump()}")
    
    # Clear the cache to force reload of settings
    get_settings.cache_clear() 