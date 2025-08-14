from typing import List, Optional
from pydantic import BaseModel, Field

class SuggestionInfo(BaseModel):
    """Suggestion information schema."""
    category: Optional[str] = Field(None, description="Suggestion category")
    relevance_score: Optional[float] = Field(None, description="Relevance score")
    source: Optional[str] = Field(None, description="Source of the suggestion")
    context: Optional[str] = Field(None, description="Additional context")

class Suggestion(BaseModel):
    """Search suggestion schema."""
    text: str = Field(..., description="Suggested search text")
    info: SuggestionInfo = Field(default_factory=SuggestionInfo, description="Suggestion information")

class SuggestionRequest(BaseModel):
    """Search suggestion request schema."""
    query: str = Field(..., description="Original search query")
    context: Optional[str] = Field(None, description="Search context")
    max_suggestions: int = Field(5, description="Maximum number of suggestions to return")
    min_relevance: Optional[float] = Field(None, description="Minimum relevance score")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")

class SuggestionResponse(BaseModel):
    """Search suggestion response schema."""
    suggestions: List[Suggestion] = Field(..., description="List of suggestions")
    original_query: str = Field(..., description="Original search query")
    total_suggestions: int = Field(..., description="Total number of suggestions") 