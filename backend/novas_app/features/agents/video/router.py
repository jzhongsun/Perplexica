from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from .service import VideoSearchService
from .schemas import VideoSearchRequest, VideoSearchResponse, VideoResult

router = APIRouter(prefix="/video", tags=["video"])

@router.post("/search", response_model=VideoSearchResponse)
async def search_videos(
    request: VideoSearchRequest,
    video_service: VideoSearchService = Depends(VideoSearchService)
) -> VideoSearchResponse:
    """Search for videos with enhanced query processing."""
    return await video_service.search_videos(request)

@router.get("/videos/{video_id}", response_model=VideoResult)
async def get_video_details(
    video_id: str,
    video_service: VideoSearchService = Depends(VideoSearchService)
) -> VideoResult:
    """Get detailed information about a specific video."""
    result = await video_service.get_video_details(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    return result 