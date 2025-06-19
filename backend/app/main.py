"""Main application module."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import dotenv
from app.api.v1.router import router as api_v1_router
from app.db.init_db import init_app_db
from app.features.chat.router_stream import router as chat_stream_router

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_app_db()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Perplexica API",
    description="Backend API for Perplexica chat application",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1") 
app.include_router(chat_stream_router, prefix="/api") 