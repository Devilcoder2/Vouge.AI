from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.schemas.wardrobe import WardrobeItemResponse

class SocialUserProfileResponse(BaseModel):
    id: UUID
    username: str
    vanity_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    verified_badge: bool
    favorite_brands: List[str] = []
    wardrobe_visibility: str
    followers_count: int
    following_count: int
    posts_count: int
    style_personas: List[str] = []

    class Config:
        from_attributes = True


class FollowActionRequest(BaseModel):
    action: str = Field(..., description="Action to perform: follow or unfollow")


class PostTaggedItemRequest(BaseModel):
    wardrobe_item_id: Optional[UUID] = None
    external_product_id: Optional[UUID] = None
    x_coord: float = Field(..., ge=0.0, le=100.0, description="X coordinate percentage from left")
    y_coord: float = Field(..., ge=0.0, le=100.0, description="Y coordinate percentage from top")


class PostTaggedItemResponse(BaseModel):
    id: UUID
    post_id: UUID
    wardrobe_item_id: Optional[UUID] = None
    external_product_id: Optional[UUID] = None
    x_coord: float
    y_coord: float
    wardrobe_item: Optional[WardrobeItemResponse] = None

    class Config:
        from_attributes = True


class PostCreateRequest(BaseModel):
    image_url: str
    caption: Optional[str] = None
    weather_context: Optional[str] = None
    occasion_tag: Optional[str] = None
    style_persona: Optional[str] = None
    tagged_items: List[PostTaggedItemRequest] = []


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    username: str
    avatar_url: Optional[str] = None
    content: str
    created_at: datetime
    parent_comment_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    parent_comment_id: Optional[UUID] = None


class PostResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    avatar_url: Optional[str] = None
    verified_badge: bool
    image_url: str
    caption: Optional[str] = None
    weather_context: Optional[str] = None
    occasion_tag: Optional[str] = None
    style_persona: Optional[str] = None
    created_at: datetime
    likes_count: int
    comments_count: int
    saves_count: int
    is_liked_by_user: bool = False
    is_saved_by_user: bool = False
    tagged_items: List[PostTaggedItemResponse] = []

    class Config:
        from_attributes = True


class RecreateSlotMatch(BaseModel):
    role: str = Field(..., description="Role slot, e.g. top, bottom, shoes")
    tagged_item_id: UUID
    tagged_item_name: str
    matched_item: Optional[WardrobeItemResponse] = None
    similarity_score: float = Field(0.0, description="Cosine similarity score, 0.0 to 1.0")
    match_status: str = Field(..., description="Perfect Match, Substitute, or Missing")
    buy_link: Optional[str] = Field(None, description="Affiliate checkout URL if missing or low similarity")


class RecreateResponse(BaseModel):
    post_id: UUID
    overall_match_percentage: float = Field(..., description="Overall compatibility index (0.0 to 100.0)")
    slots: List[RecreateSlotMatch] = []
    style_persona: Optional[str] = None
    weather_context: Optional[str] = None


class TrendingPersonaResponse(BaseModel):
    name: str
    post_count: int
    popular_image_url: Optional[str] = None


class PopularCreatorResponse(BaseModel):
    id: UUID
    username: str
    vanity_username: Optional[str] = None
    avatar_url: Optional[str] = None
    verified_badge: bool
    style_personas: List[str] = []
    followers_count: int
    is_followed_by_user: bool = False


class TrendingOccasionResponse(BaseModel):
    name: str
    post_count: int


class ExploreResponse(BaseModel):
    trending_posts: List[PostResponse]
    trending_personas: List[TrendingPersonaResponse]
    popular_creators: List[PopularCreatorResponse]
    trending_occasions: List[TrendingOccasionResponse]

