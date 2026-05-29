"""
Pydantic Schemas for VOGUE.AI Digital Wardrobe Calendar System.
"""
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date as date_type
from typing import List, Optional

from app.schemas.wardrobe import WardrobeItemResponse
from app.schemas.recommendation import SavedOutfitResponse


class CalendarEntryItemResponse(BaseModel):
    """Junction response representing clothing items associated with a calendar entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clothing_item_id: UUID
    clothing_item: WardrobeItemResponse


class CalendarEntryResponse(BaseModel):
    """Response representing a fully scheduled outfit calendar entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    date: date_type
    slot: str
    outfit_id: Optional[UUID] = None
    outfit: Optional[SavedOutfitResponse] = None
    items: List[CalendarEntryItemResponse] = []
    real_photo_path: Optional[str] = None
    real_photo_url: Optional[str] = None


class CalendarEntryCreateRequest(BaseModel):
    """Request payload to create a new calendar entry (linking saved outfits or custom clothes on the go)."""
    date: date_type = Field(..., description="Target calendar date YYYY-MM-DD")
    slot: str = Field(..., description="Occasion slot name (e.g., office, gym, dinner, casual)")
    outfit_id: Optional[UUID] = Field(None, description="ID of pre-existing saved outfit to plan")
    clothing_item_ids: Optional[List[UUID]] = Field(None, description="Array of garment IDs to build custom outfit on the go")


class CalendarEntryUpdateRequest(BaseModel):
    """Request payload to update an existing calendar entry."""
    slot: Optional[str] = Field(None, description="Updated occasion slot name")
    outfit_id: Optional[UUID] = Field(None, description="Updated saved outfit ID")
    clothing_item_ids: Optional[List[UUID]] = Field(None, description="Updated array of custom garment IDs")
    real_photo_url: Optional[str] = Field(None, description="Updated real photo cdn url path")
    real_photo_path: Optional[str] = Field(None, description="Updated real photo physical file path")


class CalendarGenerateSuggestionsRequest(BaseModel):
    """Request payload to ask the AI engine to curate and plan an outfit for a calendar slot."""
    date: date_type = Field(..., description="Target date for AI suggestions YYYY-MM-DD")
    slot: str = Field(..., description="Target slot name (e.g., office, gym, casual, dinner)")
