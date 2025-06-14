"""Images router module."""
from fastapi import APIRouter, Depends

from .service import ImageService
from .schemas import ImageGenerationRequest, ImageGenerationResponse

router = APIRouter(prefix="/images", tags=["images"])

@router.post("", response_model=ImageGenerationResponse)
async def generate_images(
    request: ImageGenerationRequest,
    image_service: ImageService = Depends(ImageService)
) -> ImageGenerationResponse:
    """Generate images based on prompt."""
    return await image_service.generate_images(request) 