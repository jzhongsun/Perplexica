from typing import Dict
import httpx
from fastapi import HTTPException
import random
from datetime import datetime
from loguru import logger
from app.core.config import get_settings
from .schemas import (
    WeatherRequest,
    WeatherResponse,
    WeatherData,
    WeatherCondition,
    Temperature
)

class WeatherService:
    """Service for fetching and processing weather data."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OPENMETEO_API_URL
        self.default_units = self.settings.OPENMETEO_DEFAULT_UNITS
        self.weather_codes: Dict[int, Dict[str, str]] = {
            0: {"condition": "Clear", "icon": "clear"},
            1: {"condition": "Mainly Clear", "icon": "cloudy-1"},
            2: {"condition": "Partly Cloudy", "icon": "cloudy-1"},
            3: {"condition": "Cloudy", "icon": "cloudy-1"},
            45: {"condition": "Fog", "icon": "fog"},
            48: {"condition": "Fog", "icon": "fog"},
            51: {"condition": "Light Drizzle", "icon": "rainy-1"},
            53: {"condition": "Moderate Drizzle", "icon": "rainy-1"},
            55: {"condition": "Dense Drizzle", "icon": "rainy-1"},
            56: {"condition": "Light Freezing Drizzle", "icon": "frost"},
            57: {"condition": "Dense Freezing Drizzle", "icon": "frost"},
            61: {"condition": "Slight Rain", "icon": "rainy-2"},
            63: {"condition": "Moderate Rain", "icon": "rainy-2"},
            65: {"condition": "Heavy Rain", "icon": "rainy-2"},
            66: {"condition": "Light Freezing Rain", "icon": "rain-and-sleet-mix"},
            67: {"condition": "Heavy Freezing Rain", "icon": "rain-and-sleet-mix"},
            71: {"condition": "Slight Snow Fall", "icon": "snowy-2"},
            73: {"condition": "Moderate Snow Fall", "icon": "snowy-2"},
            75: {"condition": "Heavy Snow Fall", "icon": "snowy-2"},
            77: {"condition": "Snow", "icon": "snowy-1"},
            80: {"condition": "Slight Rain Showers", "icon": "rainy-3"},
            81: {"condition": "Moderate Rain Showers", "icon": "rainy-3"},
            82: {"condition": "Heavy Rain Showers", "icon": "rainy-3"},
            85: {"condition": "Slight Snow Showers", "icon": "snowy-3"},
            86: {"condition": "Heavy Snow Showers", "icon": "snowy-3"},
            95: {"condition": "Thunderstorm", "icon": "scattered-thunderstorms"},
            96: {"condition": "Thunderstorm with Slight Hail", "icon": "severe-thunderstorm"},
            99: {"condition": "Thunderstorm with Heavy Hail", "icon": "severe-thunderstorm"}
        }

    async def get_weather(self, request: WeatherRequest) -> WeatherResponse:
        """
        Get weather information for a specific location.
        
        Args:
            request: WeatherRequest containing latitude and longitude
            
        Returns:
            WeatherResponse with weather data
            
        Raises:
            HTTPException: If the weather API request fails
        """
        try:
            # Use default units if not specified
            units = request.units or self.default_units
            
            # Fetch weather data from Open-Meteo API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "latitude": request.lat,
                        "longitude": request.lng,
                        "current": "weather_code,temperature_2m,is_day,relative_humidity_2m,wind_speed_10m",
                        "timezone": "auto"
                    }
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to fetch weather data from external API"
                    )
                
                data = response.json()
                
                if "error" in data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Weather API error: {data['reason']}"
                    )
                
                current = data["current"]
                weather_code = current["weather_code"]
                is_day = current["is_day"] == 1
                
                # Get weather condition and icon
                weather_info = self.weather_codes.get(weather_code, {
                    "condition": "Unknown",
                    "icon": "clear"
                })
                
                # Append day/night suffix to icon
                icon = f"{weather_info['icon']}-{is_day and 'day' or 'night'}"
                
                temperature = current["temperature_2m"]
                if units == "imperial":
                    # Convert to Fahrenheit
                    temperature = temperature * 9/5 + 32
                
                return WeatherResponse(
                    temperature=temperature,
                    condition=weather_info["condition"],
                    location=f"{request.lat:.2f}, {request.lng:.2f}",  # Using coordinates as location
                    humidity=current["relative_humidity_2m"],
                    windSpeed=current["wind_speed_10m"],
                    icon=icon
                )

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch weather data: {str(e)}"
            ) 