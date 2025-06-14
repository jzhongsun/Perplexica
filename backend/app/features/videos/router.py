"""Videos router module."""
from fastapi import APIRouter, Depends

from .service import VideoService
from .schemas import VideoSearchRequest, VideoSearchResponse

router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("", response_model=VideoSearchResponse)
async def search_videos(
    request: VideoSearchRequest,
    video_service: VideoService = Depends(VideoService)
) -> VideoSearchResponse:
    """Search for videos."""
    return await video_service.search_videos(request) 