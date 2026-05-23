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
    primary_color: str
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
