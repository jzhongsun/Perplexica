"""Images schemas module."""
from typing import List, Optional
from pydantic import BaseModel, Field

class ImageGenerationRequest(BaseModel):
    """Image generation request model."""
    prompt: str = Field(..., description="Image generation prompt")
    n: int = Field(default=1, ge=1, le=10, description="Number of images to generate")
    size: str = Field(default="1024x1024", description="Image size")
    style: Optional[str] = Field(None, description="Image style")

class ImageResponse(BaseModel):
    """Image response model."""
    url: str = Field(..., description="Image URL")
    prompt: str = Field(..., description="Original prompt")
    created_at: str = Field(..., description="Creation timestamp")

class ImageGenerationResponse(BaseModel):
    """Image generation response model."""
    images: List[ImageResponse] = Field(..., description="Generated images") 