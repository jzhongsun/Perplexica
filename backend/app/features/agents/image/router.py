from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from .service import ImageSearchService
from .schemas import ImageSearchRequest, ImageSearchResponse, ImageResult

router = APIRouter(prefix="/image", tags=["image"])

@router.post("/search", response_model=ImageSearchResponse)
async def search_images(
    request: ImageSearchRequest,
    image_service: ImageSearchService = Depends(ImageSearchService)
) -> ImageSearchResponse:
    """Search for images with enhanced query processing."""
    return await image_service.search_images(request)

@router.get("/details", response_model=ImageResult)
async def get_image_details(
    image_url: str,
    image_service: ImageSearchService = Depends(ImageSearchService)
) -> ImageResult:
    """Get detailed information about a specific image."""
    result = await image_service.get_image_details(image_url)
    if not result:
        raise HTTPException(status_code=404, detail="Image not found")
    return result 