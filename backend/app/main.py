"""Main application module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import dotenv
from app.api.v1.router import router as api_v1_router

dotenv.load_dotenv()

app = FastAPI(
    title="Perplexica API",
    description="Backend API for Perplexica chat application",
    version="1.0.0"
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