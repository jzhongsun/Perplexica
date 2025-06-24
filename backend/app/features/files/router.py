from typing import List
from fastapi import APIRouter, Depends, File, UploadFile
from .service import FileService
from .schemas import FileUploadResponse

router = APIRouter(prefix="/uploads", tags=["files"])

@router.post("", response_model=FileUploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    file_service: FileService = Depends(FileService)
) -> FileUploadResponse:
    """Upload and process files."""
    return await file_service.process_files(
        files,
    ) 