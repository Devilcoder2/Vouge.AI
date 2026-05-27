from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class WeatherContext(BaseModel):
    """Represents local weather context associated with curation look."""
    location: str = Field(..., description="Local weather city name")
    temperature_celsius: float = Field(..., description="Local Celsius temperature")
    condition: str = Field(..., description="Local overcast/sunny weather condition text")

class EditorialLookResponse(BaseModel):
    """Payload representing Today's Curated Look for the Hero spotlight panel."""
    outfit_id: str = Field(..., description="Identifier of the cached/generated daily look")
    editorial_title: str = Field(..., description="High-fashion curations editorial title")
    subtitle: str = Field(..., description="Styling sub-theme subtitle")
    description: str = Field(..., description="Stylist-written paragraph matching local weather")
    hero_image_url: str = Field(..., description="High-res cover collage image path")
    vogue_score: int = Field(..., description="Calculated style score out of 100")
    occasion: str = Field(..., description="Curation target occasion")
    weather_context: WeatherContext = Field(..., description="Weather context")
    clothing_item_ids: List[str] = Field(..., description="Array of garment IDs in look")

class DashboardWeatherResponse(BaseModel):
    """Geolocation weather response representing current weather banner metrics."""
    location: str = Field(..., description="Calculated user city locality")
    temperature_celsius: float = Field(..., description="Local Celsius temperature")
    condition: str = Field(..., description="Weather condition description")
    humidity_percent: int = Field(..., description="Humidity percentage counter")
    wind_kph: float = Field(..., description="Wind speed counter in kilometers per hour")
    icon: str = Field(..., description="MaterialDesign or FontAwesome weather icon slug")

class RunwayTrendResponse(BaseModel):
    """ runway trends mapped to the styling subculture persona."""
    trend_id: str = Field(..., description="Trend identifier key")
    title: str = Field(..., description="Trend title")
    source: str = Field(..., description="Runway source city (e.g. Paris Fashion Week)")
    category: str = Field(..., description="Category label")
    image_url: str = Field(..., description="Trend cover aesthetic image path")
    description: str = Field(..., description="Runway trend details description")

class ChatMessage(BaseModel):
    """Representing conversational stylist chat messages history logs."""
    role: str = Field(..., description="Role key: user or assistant")
    content: str = Field(..., description="Message text content")

class ChatMessageRequest(BaseModel):
    """Interactive personal chat query payload."""
    user_id: str = Field("default_user", description="Active user closet owner ID")
    message: str = Field(..., description="Current chat query statement")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="History log messages")

class ChatMessageResponse(BaseModel):
    """Conversational stylist Gemini response envelope."""
    reply: str = Field(..., description="AI generated personal stylist reply text")
    timestamp: datetime = Field(..., description="Response generation timestamp")
    suggested_outfit_id: Optional[str] = Field(None, description="Suggested cached GeneratedOutfit ID if matched")
