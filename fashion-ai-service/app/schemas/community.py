from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.schemas.social import PostResponse

class CommunityCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Community name")
    description: Optional[str] = Field(None, description="Detailed aesthetic theme")
    cover_image_url: Optional[str] = Field(None, description="Header banner image URL")
    rules: Optional[str] = Field(None, description="Community posting guidelines")


class CommunityMemberResponse(BaseModel):
    user_id: UUID
    username: str
    avatar_url: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class CommunityResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    rules: Optional[str] = None
    creator_id: UUID
    members_count: int
    posts_count: int
    is_joined: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
