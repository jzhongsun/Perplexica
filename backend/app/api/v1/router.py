from fastapi import APIRouter

from app.features.prompts.router import router as prompts_router
from app.features.agents.video.router import router as video_router
from app.features.agents.image.router import router as image_router
from app.features.agents.suggestion.router import router as suggestion_router
from app.features.embedding.router import router as embedding_router
from app.features.weather.router import router as weather_router
from app.features.config.router import router as config_router
from app.features.files.router import router as files_router
from app.features.chat.router import router as chat_router
from app.features.chat.router_stream import router as chat_stream_router
from app.features.discover.router import router as discover_router
from app.features.auth.router import router as auth_router

router = APIRouter()

router.include_router(prompts_router)
router.include_router(video_router)
router.include_router(image_router)
router.include_router(suggestion_router)
router.include_router(embedding_router)
router.include_router(weather_router)
router.include_router(config_router)
router.include_router(files_router)
router.include_router(chat_router) 
router.include_router(chat_stream_router)
router.include_router(discover_router)

# Add auth routes
router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)