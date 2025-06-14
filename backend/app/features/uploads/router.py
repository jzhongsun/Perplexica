"""Uploads router module."""
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile

from .service import UploadService
from .schemas import UploadResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    upload_service: UploadService = Depends(UploadService)
) -> UploadResponse:
    """Upload files."""
    return await upload_service.upload_files(files) 