from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile
from .service import FileService
from .schemas import FileUploadResponse

router = APIRouter(prefix="/uploads", tags=["files"])

@router.post("", response_model=FileUploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    embedding_model: str = Form(...),
    embedding_model_provider: str = Form(...),
    file_service: FileService = Depends(FileService)
) -> FileUploadResponse:
    """Upload and process files."""
    return await file_service.process_files(
        files,
        embedding_model,
        embedding_model_provider
    ) 