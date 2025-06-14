"""Suggestions schemas module."""
from typing import List, Optional
from pydantic import BaseModel, Field

class Suggestion(BaseModel):
    """Suggestion model."""
    text: str = Field(..., description="Suggestion text")
    type: str = Field(..., description="Suggestion type")
    score: float = Field(..., description="Relevance score")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

class SuggestionsRequest(BaseModel):
    """Suggestions request model."""
    query: str = Field(..., description="Query to get suggestions for")
    types: Optional[List[str]] = Field(default=None, description="Types of suggestions to return")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of suggestions")

class SuggestionsResponse(BaseModel):
    """Suggestions response model."""
    suggestions: List[Suggestion] = Field(..., description="List of suggestions")
    query: str = Field(..., description="Original query") 