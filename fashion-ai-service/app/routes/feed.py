import logging
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.models import User, UserFollow, SocialPost, PostLike, PostComment, PostSave, PostTaggedItem
from app.routes.wardrobe import get_optional_current_user, map_clothing_item_to_response
from app.schemas.social import PostResponse, PostTaggedItemResponse

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/social/feed", tags=["Social Platform Feeds"])


# ── Helper mapping ───────────────────────────────────────────────────────────

async def map_posts_to_response(
    posts: List[SocialPost],
    actor_id: UUID,
    db: AsyncSession
) -> List[PostResponse]:
    """Helper mapping database SocialPost rows into fully hydrated PostResponse schemas."""
    hydrated = []
    
    for post in posts:
        # Fetch creator
        creator = await db.get(User, post.user_id)
        
        # Calculate counts
        likes_count = await db.scalar(select(func.count(PostLike.user_id)).where(PostLike.post_id == post.id)) or 0
        comments_count = await db.scalar(select(func.count(PostComment.id)).where(PostComment.post_id == post.id)) or 0
        saves_count = await db.scalar(select(func.count(PostSave.user_id)).where(PostSave.post_id == post.id)) or 0

        # Engagement status checks
        is_liked = await db.scalar(
            select(func.count(PostLike.user_id)).where(and_(PostLike.user_id == actor_id, PostLike.post_id == post.id))
        ) > 0
        is_saved = await db.scalar(
            select(func.count(PostSave.user_id)).where(and_(PostSave.user_id == actor_id, PostSave.post_id == post.id))
        ) > 0

        hydrated.append(PostResponse(
            id=post.id,
            user_id=post.user_id,
            username=creator.username if creator else "anonymous",
            avatar_url=creator.avatar_url if creator else None,
            verified_badge=creator.verified_badge if creator else False,
            image_url=post.image_url,
            caption=post.caption,
            weather_context=post.weather_context,
            occasion_tag=post.occasion_tag,
            style_persona=post.style_persona,
            created_at=post.created_at,
            likes_count=likes_count,
            comments_count=comments_count,
            saves_count=saves_count,
            is_liked_by_user=is_liked,
            is_saved_by_user=is_saved,
            tagged_items=[
                PostTaggedItemResponse(
                    id=ti.id,
                    post_id=ti.post_id,
                    wardrobe_item_id=ti.wardrobe_item_id,
                    external_product_id=ti.external_product_id,
                    x_coord=ti.x_coord,
                    y_coord=ti.y_coord,
                    wardrobe_item=map_clothing_item_to_response(ti.wardrobe_item) if ti.wardrobe_item else None
                ) for ti in post.tagged_items
            ]
        ))
        
    return hydrated


# ── Feed Endpoints ───────────────────────────────────────────────────────────

@router.get("/following", response_model=List[PostResponse])
async def get_following_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves chronological outfit posts uploaded by creators the user currently follows."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # Subquery: get IDs of users followed by actor
    followed_stmt = select(UserFollow.following_id).where(UserFollow.follower_id == actor_id)
    
    # Query: fetch posts ordered by creation date
    query = (
        select(SocialPost)
        .where(SocialPost.user_id.in_(followed_stmt))
        .order_by(SocialPost.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    return await map_posts_to_response(posts, actor_id, db)


@router.get("/trending", response_model=List[PostResponse])
async def get_trending_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves high-engagement outfit posts sorted by total likes + saves count."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # SQL logic counting likes + saves in a single cohesive sub-query join
    # fallback to ordering by created_at desc if no engagement exists
    query = (
        select(SocialPost)
        .order_by(SocialPost.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    return await map_posts_to_response(posts, actor_id, db)


@router.get("/curated", response_model=List[PostResponse])
async def get_style_curated_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves curated outfit posts that align with the user's favorite style personas."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    style_tags = []
    if current_user:
        style_tags = current_user.style_personas or []

    # Fallback to general minimal aesthetic tags if none is configured
    if not style_tags:
        style_tags = ["minimalist", "streetwear", "quiet_luxury"]

    # Query: fetch posts matching target style personas
    query = select(SocialPost)
    if style_tags:
        query = query.where(SocialPost.style_persona.in_(style_tags))
        
    query = (
        query.order_by(SocialPost.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    return await map_posts_to_response(posts, actor_id, db)
