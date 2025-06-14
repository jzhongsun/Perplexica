from typing import List
from pydantic import BaseModel, Field

class FileResponse(BaseModel):
    fileName: str = Field(..., description="Original file name")
    fileExtension: str = Field(..., description="File extension")
    fileId: str = Field(..., description="Unique file identifier")

class FileUploadResponse(BaseModel):
    files: List[FileResponse] = Field(..., description="List of processed files") 