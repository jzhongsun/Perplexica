from typing import List, Optional
from pydantic import BaseModel

class SearchOptions(BaseModel):
    """Search options schema."""
    categories: Optional[List[str]] = None
    engines: Optional[List[str]] = None
    language: Optional[str] = None
    pageno: Optional[int] = None

class SearchResult(BaseModel):
    """Search result schema."""
    title: str
    url: str
    img_src: Optional[str] = None
    thumbnail_src: Optional[str] = None
    thumbnail: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    iframe_src: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response schema."""
    results: List[SearchResult]
    suggestions: List[str] 