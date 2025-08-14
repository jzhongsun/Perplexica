from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class VideoInfo(BaseModel):
    """Video information schema."""
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    channel_name: Optional[str] = Field(None, description="Channel name")
    duration: Optional[str] = Field(None, description="Video duration")
    view_count: Optional[int] = Field(None, description="View count")
    published_at: Optional[str] = Field(None, description="Publication date")

class VideoResult(BaseModel):
    """Video search result schema."""
    video_id: str = Field(..., description="YouTube video ID")
    url: HttpUrl = Field(..., description="Video URL")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail URL")
    info: VideoInfo = Field(..., description="Video information")
    relevance_score: Optional[float] = Field(None, description="Relevance score")

class VideoSearchRequest(BaseModel):
    """Video search request schema."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, description="Maximum number of results to return")
    language: Optional[str] = Field(None, description="Preferred language")
    region_code: Optional[str] = Field(None, description="Region code (e.g., US)")
    published_after: Optional[str] = Field(None, description="Filter by publish date")
    order: Optional[str] = Field("relevance", description="Sort order (relevance, date, rating, etc.)")

class VideoSearchResponse(BaseModel):
    """Video search response schema."""
    results: List[VideoResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    next_page_token: Optional[str] = Field(None, description="Token for next page of results") 