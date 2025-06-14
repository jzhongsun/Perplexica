"""Weather schemas module."""
from typing import List, Optional
from pydantic import BaseModel, Field

class WeatherCondition(BaseModel):
    """Weather condition model."""
    main: str = Field(..., description="Main weather condition")
    description: str = Field(..., description="Detailed weather description")
    icon: str = Field(..., description="Weather icon code")

class Temperature(BaseModel):
    """Temperature model."""
    current: float = Field(..., description="Current temperature")
    feels_like: float = Field(..., description="Feels like temperature")
    min: float = Field(..., description="Minimum temperature")
    max: float = Field(..., description="Maximum temperature")

class WeatherData(BaseModel):
    """Weather data model."""
    location: str = Field(..., description="Location name")
    conditions: List[WeatherCondition] = Field(..., description="Weather conditions")
    temperature: Temperature = Field(..., description="Temperature information")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed")
    clouds: int = Field(..., description="Cloud coverage percentage")
    timestamp: str = Field(..., description="Weather data timestamp")

class WeatherRequest(BaseModel):
    """Weather request model."""
    lat: float = Field(..., description="Latitude of the location")
    lng: float = Field(..., description="Longitude of the location")
    units: str = Field(default="metric", description="Temperature units (metric/imperial)")

class WeatherResponse(BaseModel):
    """Weather response model matching frontend interface."""
    temperature: float = Field(..., description="Current temperature")
    condition: str = Field(..., description="Weather condition description")
    location: str = Field(..., description="Location name")
    humidity: int = Field(..., description="Humidity percentage")
    windSpeed: float = Field(..., description="Wind speed in km/h")
    icon: str = Field(..., description="Weather icon identifier") 