"""Discover schemas module."""
from typing import List, Optional
from pydantic import BaseModel

class BlogResult(BaseModel):
    """Blog result schema."""
    title: str
    url: str
    img_src: Optional[str] = None
    thumbnail_src: Optional[str] = None
    thumbnail: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    iframe_src: Optional[str] = None

class DiscoveryResponse(BaseModel):
    """Discovery response schema."""
    blogs: List[BlogResult] 