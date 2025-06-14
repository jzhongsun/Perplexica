"""Model providers factory functions."""
from typing import Dict, Optional, TypedDict, Any
import httpx

from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from app.core.config import get_settings

# Provider metadata
PROVIDER_METADATA = {
    "openai": {
        "key": "openai",
        "displayName": "OpenAI"
    },
    "ollama": {
        "key": "ollama",
        "displayName": "Ollama"
    },
    "groq": {
        "key": "groq",
        "displayName": "Groq"
    },
    "anthropic": {
        "key": "anthropic",
        "displayName": "Anthropic"
    },
    "gemini": {
        "key": "gemini",
        "displayName": "Google Gemini"
    },
    "deepseek": {
        "key": "deepseek",
        "displayName": "Deepseek AI"
    },
    "lmstudio": {
        "key": "lmstudio",
        "displayName": "LM Studio"
    },
    "custom_openai": {
        "key": "custom_openai",
        "displayName": "Custom OpenAI"
    }
}

class ChatModel(TypedDict):
    """Chat model type."""
    displayName: str
    model: Optional[BaseChatModel]

class EmbeddingModel(TypedDict):
    """Embedding model type."""
    displayName: str
    model: Optional[Embeddings]

async def load_openai_chat_models() -> Dict[str, ChatModel]:
    """Load OpenAI chat models."""
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return {}
    
    try:
        return {
            "gpt-3.5-turbo": {
                "displayName": "GPT-3.5 Turbo",
                "model": ChatOpenAI(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model_name="gpt-3.5-turbo"
                )
            },
            "gpt-4": {
                "displayName": "GPT-4",
                "model": ChatOpenAI(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model_name="gpt-4"
                )
            }
        }
    except Exception as e:
        print(f"Error loading OpenAI models: {e}")
        return {}

async def load_anthropic_chat_models() -> Dict[str, ChatModel]:
    """Load Anthropic chat models."""
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        return {}
    
    try:
        return {
            "claude-3-sonnet": {
                "displayName": "Claude 3 Sonnet",
                "model": ChatAnthropic(
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    model_name="claude-3-sonnet-20240229"
                )
            }
        }
    except Exception as e:
        print(f"Error loading Anthropic models: {e}")
        return {}

async def load_groq_chat_models() -> Dict[str, ChatModel]:
    """Load Groq chat models."""
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        return {}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            models = response.json()["data"]
            
            return {
                model["id"]: {
                    "displayName": model["id"],
                    "model": ChatOpenAI(
                        api_key=settings.GROQ_API_KEY,
                        model_name=model["id"],
                        temperature=0.7,
                        base_url="https://api.groq.com/openai/v1"
                    )
                }
                for model in models
            }
    except Exception as e:
        print(f"Error loading Groq models: {e}")
        return {}

async def load_ollama_chat_models() -> Dict[str, ChatModel]:
    """Load Ollama chat models."""
    settings = get_settings()
    if not settings.OLLAMA_API_ENDPOINT:
        return {}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_API_ENDPOINT}/api/tags")
            models = response.json()
            
            return {
                model["name"]: {
                    "displayName": model.get("title", model["name"]),
                    "model": ChatOpenAI(
                        base_url=f"{settings.OLLAMA_API_ENDPOINT}/v1",
                        model_name=model["name"]
                    )
                }
                for model in models
            }
    except Exception as e:
        print(f"Error loading Ollama models: {e}")
        return {}

async def load_lmstudio_chat_models() -> Dict[str, ChatModel]:
    """Load LM Studio chat models."""
    settings = get_settings()
    if not settings.LMSTUDIO_API_ENDPOINT:
        return {}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.LMSTUDIO_API_ENDPOINT}/v1/models")
            models = response.json()
            
            return {
                model["id"]: {
                    "displayName": model.get("name", model["id"]),
                    "model": ChatOpenAI(
                        base_url=settings.LMSTUDIO_API_ENDPOINT,
                        model_name=model["id"]
                    )
                }
                for model in models
            }
    except Exception as e:
        print(f"Error loading LM Studio models: {e}")
        return {}

async def load_openai_embedding_models() -> Dict[str, EmbeddingModel]:
    """Load OpenAI embedding models."""
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return {}
    
    try:
        return {
            "text-embedding-3-small": {
                "displayName": "text-embedding-3-small",
                "model": OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
            }
        }
    except Exception as e:
        print(f"Error loading OpenAI embedding models: {e}")
        return {}

# Chat model providers mapping
CHAT_MODEL_PROVIDERS = {
    "openai": load_openai_chat_models,
    "anthropic": load_anthropic_chat_models,
    "groq": load_groq_chat_models,
    "ollama": load_ollama_chat_models,
    "lmstudio": load_lmstudio_chat_models
}

# Embedding model providers mapping
EMBEDDING_MODEL_PROVIDERS = {
    "openai": load_openai_embedding_models
}

async def get_available_chat_model_providers() -> Dict[str, Dict[str, ChatModel]]:
    """Get all available chat model providers and their models."""
    models: Dict[str, Dict[str, ChatModel]] = {}
    
    # Load models from each provider
    for provider, loader in CHAT_MODEL_PROVIDERS.items():
        provider_models = await loader()
        if provider_models:
            models[provider] = provider_models
    
    # Add custom OpenAI provider if configured
    settings = get_settings()
    if (settings.CUSTOM_OPENAI_API_KEY and 
        settings.CUSTOM_OPENAI_API_URL and 
        settings.CUSTOM_OPENAI_MODEL_NAME):
        models["custom_openai"] = {
            settings.CUSTOM_OPENAI_MODEL_NAME: {
                "displayName": settings.CUSTOM_OPENAI_MODEL_NAME,
                "model": ChatOpenAI(
                    api_key=settings.CUSTOM_OPENAI_API_KEY,
                    base_url=settings.CUSTOM_OPENAI_API_URL,
                    model_name=settings.CUSTOM_OPENAI_MODEL_NAME,
                    temperature=0.7
                )
            }
        }
    
    return models

async def get_available_embedding_model_providers() -> Dict[str, Dict[str, EmbeddingModel]]:
    """Get all available embedding model providers and their models."""
    models: Dict[str, Dict[str, EmbeddingModel]] = {}
    
    # Load models from each provider
    for provider, loader in EMBEDDING_MODEL_PROVIDERS.items():
        provider_models = await loader()
        if provider_models:
            models[provider] = provider_models
    
    return models

def get_chat_model(provider: str = "openai") -> BaseChatModel:
    """Get chat model instance based on provider.
    
    Args:
        provider: Model provider name
        
    Returns:
        Chat model instance
    """
    settings = get_settings()
    
    if provider == "openai":
        return ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo"
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            model_name="claude-3-sonnet-20240229"
        )
    elif provider == "custom":
        return ChatOpenAI(
            api_key=settings.CUSTOM_OPENAI_API_KEY,
            base_url=settings.CUSTOM_OPENAI_API_URL,
            model_name=settings.CUSTOM_OPENAI_MODEL_NAME
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def get_embedding_model(provider: str = "openai") -> Embeddings:
    """Get embedding model instance based on provider.
    
    Args:
        provider: Model provider name
        
    Returns:
        Embedding model instance
    """
    settings = get_settings()
    
    if provider == "openai":
        return OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")

def get_search_handler(provider: str = "searxng") -> Optional[str]:
    """Get search handler based on provider.
    
    Args:
        provider: Search provider name
        
    Returns:
        Search handler endpoint if available
    """
    settings = get_settings()
    
    if provider == "searxng":
        return settings.SEARXNG_API_ENDPOINT
    else:
        return None 