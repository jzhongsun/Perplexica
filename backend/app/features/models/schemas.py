"""Models schemas module."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ModelInfo(BaseModel):
    """Model information."""
    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    type: str = Field(..., description="Model type (e.g., chat, embedding)")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    parameters: Optional[dict] = Field(default=None, description="Model parameters")

class ModelsResponse(BaseModel):
    """Response model for models endpoint."""
    chat_model_providers: Dict[str, Dict[str, ModelInfo]] = Field(
        default_factory=dict,
        description="Available chat model providers and their models"
    )
    embedding_model_providers: Dict[str, Dict[str, ModelInfo]] = Field(
        default_factory=dict,
        description="Available embedding model providers and their models"
    ) 