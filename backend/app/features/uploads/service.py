"""Uploads service module."""
import os
import uuid
from typing import List
from datetime import datetime
from fastapi import UploadFile

from .schemas import UploadResponse, UploadedFile

class UploadService:
    """Upload service class."""
    
    def __init__(self):
        """Initialize upload service."""
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def upload_files(self, files: List[UploadFile]) -> UploadResponse:
        """Upload files and return their information."""
        uploaded_files = []
        
        for file in files:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Get file extension
            _, ext = os.path.splitext(file.filename)
            
            # Create unique filename
            unique_filename = f"{file_id}{ext}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Create file record
            uploaded_file = UploadedFile(
                id=file_id,
                filename=file.filename,
                content_type=file.content_type,
                size=os.path.getsize(file_path),
                url=f"/uploads/{unique_filename}",
                uploaded_at=datetime.now()
            )
            uploaded_files.append(uploaded_file)
        
        return UploadResponse(files=uploaded_files) 