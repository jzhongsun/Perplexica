"""Uploads schemas module."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class UploadedFile(BaseModel):
    """Uploaded file model."""
    id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size: int = Field(..., description="File size in bytes")
    url: str = Field(..., description="File URL")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

class UploadResponse(BaseModel):
    """Upload response model."""
    files: List[UploadedFile] = Field(..., description="List of uploaded files") 