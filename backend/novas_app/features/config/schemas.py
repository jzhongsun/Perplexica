from typing import Optional, TypedDict
from pydantic import BaseModel, Field

class ModelInfo(BaseModel):
    name: str = Field(..., description="Model name")
    displayName: str = Field(..., description="Display name for the model")

class ConfigResponse(BaseModel):
    automaticImageSearch: Optional[bool] = Field(default=True, description="Whether to automatically search for images")
    automaticVideoSearch: Optional[bool] = Field(default=False, description="Whether to automatically search for videos")
    systemInstructions: Optional[str] = Field(default="", description="System instructions for the chatbot")

class ConfigUpdate(TypedDict):
    pass
