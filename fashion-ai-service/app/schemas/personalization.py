from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class FeedbackRequest(BaseModel):
    """
    Pydantic schema representing the user interaction feedback request.
    """
    outfit_id: Optional[str] = None
    action: str  # like, save, dismiss, regenerate

class FeedbackResponse(BaseModel):
    """
    Pydantic schema representing feedback submission success status.
    """
    success: bool
    message: str

class StyleProfileResponse(BaseModel):
    """
    Pydantic schema representing the user's persistently learned style profile preferences.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    preferred_colors: List[str]
    disliked_colors: List[str]
    preferred_styles: List[str]
    preferred_formality_range: List[int]
    favorite_categories: List[str]
    updated_at: datetime
