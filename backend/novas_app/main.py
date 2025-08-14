"""Main application module."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import dotenv
from novas_app.api.v1.router import router as api_v1_router
from novas_app.db.init_db import init_app_db
from novas_app.db.database import close_db_connections
from novas_app.features.chat.router_stream import router as chat_stream_router
from novas_app.features.chat.admin_router import router as chat_admin_router
from novas_app.core.background_tasks import start_background_tasks

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_app_db()
    await start_background_tasks()
    yield
    logger.info("Shutting down...")
    await close_db_connections()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Perplexica API",
        description="AI-powered search and chat API",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(chat_stream_router, prefix="/api/v1")
    app.include_router(chat_admin_router, prefix="/api/v1")
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 