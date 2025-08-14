"""Videos schemas module."""
from typing import List, Optional
from pydantic import BaseModel, Field

class VideoSearchRequest(BaseModel):
    """Video search request model."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    order: str = Field(default="relevance", description="Order of results")
    type: str = Field(default="video", description="Type of results")

class Video(BaseModel):
    """Video model."""
    id: str = Field(..., description="Video ID")
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    thumbnail_url: str = Field(..., description="Thumbnail URL")
    channel_title: str = Field(..., description="Channel title")
    published_at: str = Field(..., description="Publication date")
    view_count: Optional[int] = Field(None, description="View count")
    duration: Optional[str] = Field(None, description="Video duration")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

class VideoSearchResponse(BaseModel):
    """Video search response model."""
    videos: List[Video] = Field(..., description="List of videos")
    total_results: int = Field(..., description="Total number of results")
    next_page_token: Optional[str] = Field(None, description="Token for next page") 