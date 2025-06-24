import os
import uuid
from typing import List
from fastapi import HTTPException, UploadFile
from app.core.config import get_settings
from .schemas import FileUploadResponse, FileResponse

class FileService:
    """Service for handling file uploads and processing."""

    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = os.path.join(os.getcwd(), "uploads")

        # Ensure upload directory exists
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def process_files(
        self,
        files: List[UploadFile],
    ) -> FileUploadResponse:
        """
        Process uploaded files.
        
        Args:
            files: List of uploaded files
            
        Returns:
            FileUploadResponse containing processed file information
            
        Raises:
            HTTPException: If file processing fails
        """
        processed_files = []

        for file in files:
            file_extension = file.filename.split(".")[-1].lower()
            
            if file_extension not in ["pdf", "docx", "txt"]:
                raise HTTPException(
                    status_code=400,
                    detail="File type not supported"
                )

            # Generate unique file ID and save file
            file_id = str(uuid.uuid4())
            file_path = os.path.join(
                self.upload_dir,
                f"{file_id}.{file_extension}"
            )
            
            try:
                # Save uploaded file
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                processed_files.append(
                    FileResponse(
                        fileName=file.filename,
                        fileExtension=file_extension,
                        fileId=file_id
                    )
                )

            except Exception as e:
                # Clean up files in case of error
                for path in [file_path]:
                    if os.path.exists(path):
                        os.remove(path)
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing file: {str(e)}"
                )

        return FileUploadResponse(files=processed_files) 