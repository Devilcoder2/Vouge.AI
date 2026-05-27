"""
Dashboard API — GET /api/dashboard/weather

Provides weather context metrics mapped to client geolocations.
"""
import logging
import math
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.dashboard import DashboardWeatherResponse

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Weather"])

# Major fashion capitals geolocation dictionary
CAPITALS = {
    "London": {"lat": 51.5074, "lon": -0.1278, "temp": 12.0, "cond": "Overcast", "hum": 82, "wind": 14.0, "icon": "weather-cloudy"},
    "Paris": {"lat": 48.8566, "lon": 2.3522, "temp": 15.0, "cond": "Sunny", "hum": 60, "wind": 10.0, "icon": "weather-sunny"},
    "Milan": {"lat": 45.4642, "lon": 9.1900, "temp": 18.0, "cond": "Clear", "hum": 55, "wind": 8.0, "icon": "weather-sunny"},
    "New York": {"lat": 40.7128, "lon": -74.0060, "temp": 21.0, "cond": "Partly Cloudy", "hum": 65, "wind": 12.0, "icon": "weather-partly-cloudy"},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "temp": 20.0, "cond": "Rainy", "hum": 90, "wind": 18.0, "icon": "weather-rainy"}
}

def get_nearest_capital(lat: float, lon: float) -> str:
    """Finds the nearest fashion capital using Euclidean distance."""
    min_dist = float("inf")
    nearest_city = "London"
    
    for city, coords in CAPITALS.items():
        dist = math.sqrt((lat - coords["lat"])**2 + (lon - coords["lon"])**2)
        if dist < min_dist:
            min_dist = dist
            nearest_city = city
            
    return nearest_city

@router.get("/weather", response_model=DashboardWeatherResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_weather(
    user_id: str = "default_user",
    latitude: Optional[float] = Query(None, description="Client latitude decimal"),
    longitude: Optional[float] = Query(None, description="Client longitude decimal"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the user's local climate data and returns structural metrics.
    If coordinates are provided, it dynamically resolves the nearest fashion capital.
    Otherwise, defaults to the London overcast standard.
    """
    logger.info(f"Fetching weather for user={user_id}, lat={latitude}, lon={longitude}")
    
    if latitude is not None and longitude is not None:
        nearest_city = get_nearest_capital(latitude, longitude)
        weather_data = CAPITALS[nearest_city]
        logger.info(f"Resolved location to nearest fashion capital: {nearest_city}")
        
        return DashboardWeatherResponse(
            location=nearest_city,
            temperature_celsius=weather_data["temp"],
            condition=weather_data["cond"],
            humidity_percent=weather_data["hum"],
            wind_kph=weather_data["wind"],
            icon=weather_data["icon"]
        )
        
    # Default fallback to London specs
    default_weather = CAPITALS["London"]
    return DashboardWeatherResponse(
        location="London",
        temperature_celsius=default_weather["temp"],
        condition=default_weather["cond"],
        humidity_percent=default_weather["hum"],
        wind_kph=default_weather["wind"],
        icon=default_weather["icon"]
    )
