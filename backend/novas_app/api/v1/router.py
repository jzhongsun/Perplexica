from fastapi import APIRouter

from novas_app.features.prompts.router import router as prompts_router
from novas_app.features.agents.video.router import router as video_router
from novas_app.features.agents.image.router import router as image_router
from novas_app.features.agents.suggestion.router import router as suggestion_router
from novas_app.features.weather.router import router as weather_router
from novas_app.features.config.router import router as config_router
from novas_app.features.files.router import router as files_router
from novas_app.features.chat.router import router as chat_router
from novas_app.features.chat.router_stream import router as chat_stream_router
from novas_app.features.discover.router import router as discover_router
from novas_app.features.auth.router import router as auth_router
from novas_app.features.uploads.router import router as uploads_router

router = APIRouter()

router.include_router(prompts_router)
router.include_router(video_router)
router.include_router(image_router)
router.include_router(suggestion_router)
router.include_router(weather_router)
router.include_router(config_router)
router.include_router(files_router)
router.include_router(chat_router) 
router.include_router(chat_stream_router)
router.include_router(discover_router)
router.include_router(uploads_router)

# Add auth routes
router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)