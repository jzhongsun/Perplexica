from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class ImageInfo(BaseModel):
    """Image information schema."""
    title: Optional[str] = Field(None, description="Image title")
    description: Optional[str] = Field(None, description="Image description")
    source: Optional[str] = Field(None, description="Image source")
    author: Optional[str] = Field(None, description="Image author/creator")
    license: Optional[str] = Field(None, description="Image license")
    dimensions: Optional[str] = Field(None, description="Image dimensions")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="File type/format")

class ImageResult(BaseModel):
    """Image search result schema."""
    url: HttpUrl = Field(..., description="Image URL")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail URL")
    page_url: Optional[HttpUrl] = Field(None, description="Source page URL")
    info: ImageInfo = Field(..., description="Image information")
    relevance_score: Optional[float] = Field(None, description="Relevance score")

class ImageSearchRequest(BaseModel):
    """Image search request schema."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, description="Maximum number of results to return")
    safe_search: bool = Field(True, description="Enable safe search")
    image_type: Optional[str] = Field(None, description="Type of image (photo, illustration, etc.)")
    color_type: Optional[str] = Field(None, description="Color type (color, gray, etc.)")
    size: Optional[str] = Field(None, description="Image size (small, medium, large, etc.)")
    license_type: Optional[str] = Field(None, description="License type (creative commons, etc.)")

class ImageSearchResponse(BaseModel):
    """Image search response schema."""
    results: List[ImageResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    next_page_token: Optional[str] = Field(None, description="Token for next page of results") 