"""
Weather feature module for fetching and processing weather data
"""

from .router import router
from .service import WeatherService
from .schemas import WeatherRequest, WeatherResponse

__all__ = [
    "router",
    "WeatherService",
    "WeatherRequest",
    "WeatherResponse"
] 