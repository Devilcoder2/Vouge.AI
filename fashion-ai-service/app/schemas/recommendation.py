from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class GenerateOutfitsRequest(BaseModel):
    user_id: Optional[str] = Field("default_user", description="Identifier of the user closet owner")
    occasion: str = Field(..., description="Target occasion for styling, e.g. casual, office, date, gym, wedding")
    season: str = Field(..., description="Target weather season: spring, summer, autumn, winter")

class RecommendationItemResponse(BaseModel):
    id: UUID
    category: str
    subcategory: str
    primary_color: str
    primary_color_hex: str
    fit: str
    style: str
    formality: int
    pattern: str

class OutfitScoreBreakdown(BaseModel):
    color_score: int
    style_score: int
    occasion_score: int
    formality_score: int
    season_score: int

class SingleOutfitResponse(BaseModel):
    score: int
    items: List[RecommendationItemResponse]
    reasoning: str
    template_name: str
    breakdown: OutfitScoreBreakdown
    why_selected: List[str] = Field(default_factory=list)
    outfit_embedding: Optional[List[float]] = None

class GenerateOutfitsResponse(BaseModel):
    outfits: List[SingleOutfitResponse]
    diversity_eval: Dict[str, Any]

class SaveOutfitRequest(BaseModel):
    user_id: str = Field("default_user", description="User ID")
    name: str = Field(..., description="Descriptive name of the outfit")
    occasion: str = Field(..., description="Occasion")
    season: str = Field(..., description="Season")
    score: int = Field(..., description="Compatibility score")
    reasoning: str = Field(..., description="Stylist reasoning")
    clothing_item_ids: List[UUID] = Field(..., description="List of garment IDs included in the outfit")

class SavedOutfitResponse(BaseModel):
    id: UUID
    user_id: str
    name: str
    occasion: str
    season: str
    score: int
    reasoning: Optional[str] = None
    created_at: datetime
    items: List[RecommendationItemResponse]

class GapAnalysisResponse(BaseModel):
    item_name: str
    category: str
    subcategory: str
    style: str
    fit: str
    formality: int
    primary_color: str
    primary_color_hex: str
    pattern: str
    unlocked_outfits_count: int
    reasoning: str

class VersatilityResponse(BaseModel):
    item_id: UUID
    category: str
    subcategory: str
    primary_color: str
    versatility_score: int
    usage_count: int
    reasoning: str

class UserProfileSetupRequest(BaseModel):
    user_id: str
    height_cm: Optional[int] = None
    body_archetype: Optional[str] = None  # pear_shape, rectangle, athletic, stocky, lean_tall
    fit_preference: Optional[str] = None  # slim, standard, oversized
    style_persona: Optional[str] = None   # minimalist, old_money, streetwear, quiet_luxury, etc.
    avoided_colors: List[str] = Field(default_factory=list)
    favorite_styles: List[str] = Field(default_factory=list)

class UserProfileResponse(BaseModel):
    user_id: str
    height_cm: Optional[int] = None
    body_archetype: Optional[str] = None
    fit_preference: Optional[str] = None
    style_persona: Optional[str] = None
    avoided_colors: List[str] = Field(default_factory=list)
    favorite_styles: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

class UserFeedbackRequest(BaseModel):
    user_id: str
    outfit_item_ids: List[UUID]
    feedback_type: str  # like, save, dismiss

