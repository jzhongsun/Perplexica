"""Search schemas module."""
from typing import List, Optional
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    """Search result model."""
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="Result snippet/description")
    source: str = Field(..., description="Result source")
    score: float = Field(..., description="Relevance score")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    mode: str = Field(default="web", description="Search mode (web, academic, news, etc.)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[dict] = Field(default=None, description="Search filters")

class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
    mode: str = Field(..., description="Search mode used") 