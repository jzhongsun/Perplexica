"""Weather router module."""
from fastapi import APIRouter, Depends
from .service import WeatherService
from .schemas import WeatherRequest, WeatherResponse
from loguru import logger

router = APIRouter(prefix="/weather", tags=["weather"])

@router.post("", response_model=WeatherResponse)
async def get_weather(
    request: WeatherRequest,
    weather_service: WeatherService = Depends(WeatherService)
) -> WeatherResponse:
    """Get weather data for location."""
    logger.info(f"Weather request: {request}")
    return await weather_service.get_weather(request) 