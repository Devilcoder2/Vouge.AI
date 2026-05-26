import logging
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.models import (
    User, UserFollow, SocialPost, PostTaggedItem, PostLike, PostComment, PostSave, ClothingItem, ExternalProduct, RecreatedFit
)
from app.routes.wardrobe import get_optional_current_user, map_clothing_item_to_response
from app.schemas.social import (
    SocialUserProfileResponse, FollowActionRequest, PostCreateRequest, PostResponse,
    CommentCreateRequest, CommentResponse, RecreateResponse, RecreateSlotMatch, PostTaggedItemResponse,
    ExploreResponse, TrendingPersonaResponse, PopularCreatorResponse, TrendingOccasionResponse
)
from app.services.recreation import OutfitRecreationService

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/social", tags=["Social Platform"])


# ── Profiles & Identity ──────────────────────────────────────────────────────

@router.get("/profile/{username}", response_model=SocialUserProfileResponse)
async def get_social_profile(username: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a user's digital fashion identity and style preferences by username."""
    # Find user
    result = await db.execute(select(User).where(User.username.ilike(username)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile '{username}' not found."
        )

    # Calculate counts
    followers_count = await db.scalar(
        select(func.count(UserFollow.follower_id)).where(UserFollow.following_id == user.id)
    ) or 0
    following_count = await db.scalar(
        select(func.count(UserFollow.following_id)).where(UserFollow.follower_id == user.id)
    ) or 0
    posts_count = await db.scalar(
        select(func.count(SocialPost.id)).where(SocialPost.user_id == user.id)
    ) or 0

    return SocialUserProfileResponse(
        id=user.id,
        username=user.username,
        vanity_username=user.vanity_username or user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio or "Monochrome lover | Casual wear edits",
        avatar_url=user.avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={user.username}",
        verified_badge=user.verified_badge or False,
        favorite_brands=user.favorite_brands or ["COS", "Zara", "Uniqlo"],
        wardrobe_visibility=user.wardrobe_visibility or "public",
        followers_count=followers_count,
        following_count=following_count,
        posts_count=posts_count,
        style_personas=user.style_personas or ["minimalist", "streetwear"]
    )


# ── Follow Graph System ─────────────────────────────────────────────────────

@router.post("/follow/{user_id}", status_code=status.HTTP_200_OK)
async def toggle_follow_user(
    user_id: UUID,
    payload: FollowActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Allows following or unfollowing another creator on the platform."""
    # Active user fallback for testing
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")
    
    if actor_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself."
        )

    # Check target exists
    target_exists = await db.scalar(select(func.count(User.id)).where(User.id == user_id))
    if not target_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target user ID '{user_id}' not found."
        )

    # Check existing follow relation
    stmt = select(UserFollow).where(
        and_(UserFollow.follower_id == actor_id, UserFollow.following_id == user_id)
    )
    result = await db.execute(stmt)
    existing_follow = result.scalar_one_or_none()

    if payload.action.lower() == "follow":
        if existing_follow:
            return {"message": "You are already following this user."}
        
        new_follow = UserFollow(follower_id=actor_id, following_id=user_id)
        db.add(new_follow)
        await db.commit()
        return {"message": "Successfully followed user."}

    elif payload.action.lower() == "unfollow":
        if not existing_follow:
            return {"message": "You are not following this user."}
        
        await db.delete(existing_follow)
        await db.commit()
        return {"message": "Successfully unfollowed user."}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid follow action. Allowed: follow, unfollow"
        )


# ── Outfit Posting Router ──────────────────────────────────────────────────

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_outfit_post(
    payload: PostCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Creates a new structured outfit social post with coordinate-mapped garment tags."""
    # Active user fallback for testing
    actor = current_user
    if not actor:
        # Fetch or create a default user for testing if none is logged in
        res = await db.execute(select(User).limit(1))
        actor = res.scalar_one_or_none()
        if not actor:
            actor = User(
                id=UUID("00000000-0000-0000-0000-000000000001"),
                email="test_social_creator@vouge.ai",
                username="social_curator",
                hashed_password="mock",
                vanity_username="Aesthetic_Curator",
                bio="Minimalist monochrome editor | NYC",
                verified_badge=True
            )
            db.add(actor)
            await db.commit()
            await db.refresh(actor)

    post_id = uuid4()

    # Dynamic CLIP image embedding generation
    from PIL import Image
    import os
    from app.config import settings
    from app.ai.embedding_service import FashionEmbeddingService

    local_path = None
    if "uploads/" in payload.image_url:
        filename = payload.image_url.split("uploads/")[-1]
        local_path = settings.UPLOAD_DIR / filename
    elif "processed/" in payload.image_url:
        filename = payload.image_url.split("processed/")[-1]
        local_path = settings.PROCESSED_DIR / filename
    else:
        local_path = settings.UPLOAD_DIR / os.path.basename(payload.image_url)

    embedding_path = None
    if local_path and local_path.exists():
        try:
            img = Image.open(local_path).convert("RGB")
            emb_service = FashionEmbeddingService()
            vector = emb_service.generate_image_embedding(img)
            saved_path = FashionEmbeddingService.save_embedding_to_disk(vector, f"post_{post_id}")
            embedding_path = str(saved_path)
        except Exception as e:
            logger.error(f"Failed to generate CLIP image embedding for post {post_id}: {e}")

    new_post = SocialPost(
        id=post_id,
        user_id=actor.id,
        image_url=payload.image_url,
        caption=payload.caption,
        weather_context=payload.weather_context,
        occasion_tag=payload.occasion_tag,
        style_persona=payload.style_persona,
        community_id=payload.community_id,
        embedding_path=embedding_path,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_post)

    # Insert tagged clothing coordinates
    for item in payload.tagged_items:
        tagged = PostTaggedItem(
            id=uuid4(),
            post_id=post_id,
            wardrobe_item_id=item.wardrobe_item_id,
            external_product_id=item.external_product_id,
            x_coord=item.x_coord,
            y_coord=item.y_coord
        )
        db.add(tagged)

    await db.commit()
    
    # Reload post with selectin relationships
    stmt = select(SocialPost).where(SocialPost.id == post_id)
    reloaded = (await db.execute(stmt)).scalar_one()

    return PostResponse(
        id=reloaded.id,
        user_id=actor.id,
        username=actor.username,
        avatar_url=actor.avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={actor.username}",
        verified_badge=actor.verified_badge,
        image_url=reloaded.image_url,
        caption=reloaded.caption,
        weather_context=reloaded.weather_context,
        occasion_tag=reloaded.occasion_tag,
        style_persona=reloaded.style_persona,
        community_id=reloaded.community_id,
        created_at=reloaded.created_at,
        likes_count=0,
        comments_count=0,
        saves_count=0,
        tagged_items=[
            PostTaggedItemResponse(
                id=ti.id,
                post_id=ti.post_id,
                wardrobe_item_id=ti.wardrobe_item_id,
                external_product_id=ti.external_product_id,
                x_coord=ti.x_coord,
                y_coord=ti.y_coord,
                wardrobe_item=map_clothing_item_to_response(ti.wardrobe_item) if ti.wardrobe_item else None
            ) for ti in reloaded.tagged_items
        ]
    )


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_outfit_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves detailed information of an outfit post, including coordinate tags."""
    result = await db.execute(
        select(SocialPost).where(SocialPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outfit post with ID '{post_id}' not found."
        )

    # Fetch creator profile
    creator = await db.get(User, post.user_id)
    
    # Calculate counts
    likes_count = await db.scalar(select(func.count(PostLike.user_id)).where(PostLike.post_id == post_id)) or 0
    comments_count = await db.scalar(select(func.count(PostComment.id)).where(PostComment.post_id == post_id)) or 0
    saves_count = await db.scalar(select(func.count(PostSave.user_id)).where(PostSave.post_id == post_id)) or 0

    # Engagement status
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")
    is_liked = await db.scalar(
        select(func.count(PostLike.user_id)).where(and_(PostLike.user_id == actor_id, PostLike.post_id == post_id))
    ) > 0
    is_saved = await db.scalar(
        select(func.count(PostSave.user_id)).where(and_(PostSave.user_id == actor_id, PostSave.post_id == post_id))
    ) > 0

    return PostResponse(
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
        community_id=post.community_id,
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
    )


# ── Social Engagement Actions ────────────────────────────────────────────────

@router.post("/posts/{post_id}/like", status_code=status.HTTP_200_OK)
async def toggle_like_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Liking or unliking an outfit social post."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")
    
    # Check post exists
    post_exists = await db.scalar(select(func.count(SocialPost.id)).where(SocialPost.id == post_id))
    if not post_exists:
        raise HTTPException(status_code=404, detail="Post not found.")

    stmt = select(PostLike).where(and_(PostLike.user_id == actor_id, PostLike.post_id == post_id))
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return {"liked": False, "message": "Post unliked successfully."}
    else:
        new_like = PostLike(user_id=actor_id, post_id=post_id)
        db.add(new_like)
        await db.commit()
        return {"liked": True, "message": "Post liked successfully."}


@router.post("/posts/{post_id}/save", status_code=status.HTTP_200_OK)
async def toggle_save_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Saving or unsaving an outfit post to digital collections."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")
    
    # Check post exists
    post_exists = await db.scalar(select(func.count(SocialPost.id)).where(SocialPost.id == post_id))
    if not post_exists:
        raise HTTPException(status_code=404, detail="Post not found.")

    stmt = select(PostSave).where(and_(PostSave.user_id == actor_id, PostSave.post_id == post_id))
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return {"saved": False, "message": "Post removed from saves successfully."}
    else:
        new_save = PostSave(user_id=actor_id, post_id=post_id)
        db.add(new_save)
        await db.commit()
        return {"saved": True, "message": "Post saved successfully."}


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_post_comment(
    post_id: UUID,
    payload: CommentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Adds a new comment or nested threaded comment to an outfit post."""
    actor = current_user
    if not actor:
        # Fallback query
        res = await db.execute(select(User).limit(1))
        actor = res.scalar_one()

    # Check post exists
    post_exists = await db.scalar(select(func.count(SocialPost.id)).where(SocialPost.id == post_id))
    if not post_exists:
        raise HTTPException(status_code=404, detail="Post not found.")

    new_comment = PostComment(
        id=uuid4(),
        user_id=actor.id,
        post_id=post_id,
        content=payload.content,
        parent_comment_id=payload.parent_comment_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return CommentResponse(
        id=new_comment.id,
        post_id=new_comment.post_id,
        user_id=actor.id,
        username=actor.username,
        avatar_url=actor.avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={actor.username}",
        content=new_comment.content,
        created_at=new_comment.created_at,
        parent_comment_id=new_comment.parent_comment_id
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def list_post_comments(post_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves all comments and replies organized chronologically for an outfit post."""
    stmt = (
        select(PostComment)
        .where(PostComment.post_id == post_id)
        .order_by(PostComment.created_at.asc())
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()

    return [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            user_id=c.user_id,
            username=c.user.username if c.user else "anonymous",
            avatar_url=c.user.avatar_url if c.user else None,
            content=c.content,
            created_at=c.created_at,
            parent_comment_id=c.parent_comment_id
        ) for c in comments
    ]


# ── AI Wardrobe-Integrated Curation ──────────────────────────────────────────

@router.get("/posts/{post_id}/recreate", response_model=RecreateResponse)
async def recreate_creator_outfit(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Step 11 Integration Moat: Calculates real-time vector matches between 
    a post's tagged coordinate items and the active user's local digital wardrobe.
    """
    result = await db.execute(select(SocialPost).where(SocialPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outfit post with ID '{post_id}' not found."
        )

    actor_id = str(current_user.id) if current_user else "default_user"

    slots = []
    total_slots = 0
    total_similarity = 0.0

    # Iterate coordinate tags
    for ti in post.tagged_items:
        # We only run matching if the tag represents an actual creator wardrobe item
        if not ti.wardrobe_item_id:
            continue

        total_slots += 1
        
        # Calculate optimal candidate matching in user's digital wardrobe
        matched_item, similarity, status_tag = await OutfitRecreationService.match_tagged_item_to_wardrobe(
            tagged_item=ti,
            user_id=actor_id,
            db=db
        )

        total_similarity += similarity

        # Standard checkout link mapping fallback if missing
        buy_link = None
        if status_tag == "Missing":
            # Select first external commerce product brand matching category
            commerce_result = await db.execute(
                select(ExternalProduct).where(ExternalProduct.title.ilike(f"%{ti.wardrobe_item.subcategory}%")).limit(1)
            )
            scraped = commerce_result.scalar_one_or_none()
            if scraped:
                buy_link = scraped.url
            else:
                buy_link = f"https://www.cos.com/en_usd/search.html?q={ti.wardrobe_item.subcategory.replace(' ', '+')}"

        slots.append(RecreateSlotMatch(
            role=ti.wardrobe_item.category.lower(),
            tagged_item_id=ti.wardrobe_item_id,
            tagged_item_name=ti.wardrobe_item.name or f"{ti.wardrobe_item.primary_color} {ti.wardrobe_item.subcategory}".title(),
            matched_item=map_clothing_item_to_response(matched_item) if matched_item else None,
            similarity_score=similarity,
            match_status=status_tag,
            buy_link=buy_link
        ))

    # Calculate overall outfit compatibility index
    overall_match = 0.0
    if total_slots > 0:
        overall_match = round((total_similarity / total_slots) * 100.0, 1)

    # Database Logging of Recreation Event
    try:
        user_uuid = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")
        details_dict = [
            {
                "role": s.role,
                "tagged_item_id": str(s.tagged_item_id) if s.tagged_item_id else None,
                "tagged_item_name": s.tagged_item_name,
                "matched_item": {
                    "id": str(s.matched_item.id) if s.matched_item.id else None,
                    "name": s.matched_item.name,
                    "textile": s.matched_item.textile,
                    "primary_color": s.matched_item.primary_color
                } if s.matched_item else None,
                "similarity_score": float(s.similarity_score),
                "match_status": s.match_status,
                "buy_link": s.buy_link
            }
            for s in slots
        ]
        history_entry = RecreatedFit(
            id=uuid4(),
            user_id=user_uuid,
            post_id=post_id,
            overall_match_percentage=overall_match,
            details=details_dict,
            created_at=datetime.now(timezone.utc)
        )
        db.add(history_entry)
        await db.commit()
    except Exception as ex:
        logger.error(f"Error logging recreated fit: {str(ex)}")
        await db.rollback()

    return RecreateResponse(
        post_id=post_id,
        overall_match_percentage=overall_match,
        slots=slots,
        style_persona=post.style_persona,
        weather_context=post.weather_context
    )


@router.get("/recreate/history")
async def get_recreation_history(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Retrieves the active user's chronological outfit recreation log history.
    """
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")
    stmt = select(RecreatedFit).where(RecreatedFit.user_id == actor_id).order_by(desc(RecreatedFit.created_at))
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    serialized = []
    for h in history:
        # Fetch the original post details
        post = h.post
        creator = None
        if post:
            creator = await db.get(User, post.user_id)
            
        serialized.append({
            "id": str(h.id),
            "post_id": str(h.post_id),
            "overall_match_percentage": float(h.overall_match_percentage),
            "details": h.details,
            "created_at": h.created_at.isoformat(),
            "post_username": creator.username if creator else "anonymous",
            "post_image_url": post.image_url if post else "",
            "post_caption": post.caption if post else ""
        })
    return serialized


@router.get("/explore", response_model=ExploreResponse)
async def explore_style_showroom(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Retrieves discovery page aggregations including trending posts, 
    highly active style personas, popular creators, and top occasions.
    """
    # Active user fallback for testing
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # 1. Trending Posts (sorted by created_at desc)
    posts_stmt = select(SocialPost).order_by(SocialPost.created_at.desc()).limit(5)
    posts_res = await db.execute(posts_stmt)
    posts = posts_res.scalars().all()

    # Hydrate posts
    from app.routes.feed import map_posts_to_response
    trending_posts = await map_posts_to_response(posts, actor_id, db)

    # 2. Trending Personas (aggregate from SocialPost table)
    persona_stmt = (
        select(
            SocialPost.style_persona,
            func.count(SocialPost.id).label("post_count"),
            func.max(SocialPost.image_url).label("popular_image_url")
        )
        .where(SocialPost.style_persona.isnot(None))
        .group_by(SocialPost.style_persona)
        .order_by(desc("post_count"))
        .limit(6)
    )
    persona_res = await db.execute(persona_stmt)
    trending_personas = [
        TrendingPersonaResponse(
            name=row[0],
            post_count=row[1],
            popular_image_url=row[2]
        ) for row in persona_res.all()
    ]

    # 3. Trending Occasions (aggregate from SocialPost table)
    occasion_stmt = (
        select(
            SocialPost.occasion_tag,
            func.count(SocialPost.id).label("post_count")
        )
        .where(SocialPost.occasion_tag.isnot(None))
        .group_by(SocialPost.occasion_tag)
        .order_by(desc("post_count"))
        .limit(6)
    )
    occasion_res = await db.execute(occasion_stmt)
    trending_occasions = [
        TrendingOccasionResponse(
            name=row[0],
            post_count=row[1]
        ) for row in occasion_res.all()
    ]

    # 4. Popular Creators (Users with high follower count)
    creators_stmt = select(User).where(User.id != actor_id).limit(5)
    creators_res = await db.execute(creators_stmt)
    creators = creators_res.scalars().all()

    popular_creators = []
    for creator in creators:
        followers_count = await db.scalar(
            select(func.count(UserFollow.follower_id)).where(UserFollow.following_id == creator.id)
        ) or 0
        
        is_followed = await db.scalar(
            select(func.count(UserFollow.follower_id)).where(
                and_(UserFollow.follower_id == actor_id, UserFollow.following_id == creator.id)
            )
        ) > 0

        popular_creators.append(PopularCreatorResponse(
            id=creator.id,
            username=creator.username,
            vanity_username=creator.vanity_username or creator.username,
            avatar_url=creator.avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={creator.username}",
            verified_badge=creator.verified_badge or False,
            style_personas=creator.style_personas or ["minimalist"],
            followers_count=followers_count,
            is_followed_by_user=is_followed
        ))

    popular_creators.sort(key=lambda x: x.followers_count, reverse=True)

    return ExploreResponse(
        trending_posts=trending_posts,
        trending_personas=trending_personas,
        popular_creators=popular_creators,
        trending_occasions=trending_occasions
    )


@router.get("/search", response_model=List[PostResponse])
async def social_semantic_search(
    q: str = Query(..., min_length=1, description="Natural language search query"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Step 7 Integration Moat: Performs CLIP-backed semantic natural language 
    text-to-image search across the styling showroom posts collection.
    """
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # 1. Encode text query via CLIPModel
    import numpy as np
    from pathlib import Path
    from app.ai.embedding_service import FashionEmbeddingService

    try:
        emb_service = FashionEmbeddingService()
        query_vector = emb_service.generate_text_embedding(q)
    except Exception as e:
        logger.error(f"Semantic search text encoding failed: {e}")
        query_vector = None

    top_posts = []

    if query_vector is not None:
        # Fetch posts with embeddings
        stmt = select(SocialPost).where(SocialPost.embedding_path.isnot(None))
        result = await db.execute(stmt)
        posts = result.scalars().all()

        scored_posts = []
        for post in posts:
            try:
                post_vector = FashionEmbeddingService.load_embedding_from_disk(Path(post.embedding_path))
                similarity = float(np.dot(query_vector, post_vector))
                scored_posts.append((post, similarity))
            except Exception as e:
                logger.warning(f"Failed to load embedding for post {post.id}: {e}")

        scored_posts.sort(key=lambda x: x[1], reverse=True)
        top_posts = [item[0] for item in scored_posts[:10]]

    # 2. Unified Fallback: Keyword search if no vector matches or CLIP was unavailable
    if not top_posts:
        keyword_stmt = (
            select(SocialPost)
            .where(
                (SocialPost.caption.ilike(f"%{q}%")) |
                (SocialPost.style_persona.ilike(f"%{q}%")) |
                (SocialPost.occasion_tag.ilike(f"%{q}%"))
            )
            .order_by(SocialPost.created_at.desc())
            .limit(10)
        )
        res = await db.execute(keyword_stmt)
        top_posts = res.scalars().all()

    # Hydrate and map to response schemas
    from app.routes.feed import map_posts_to_response
    return await map_posts_to_response(top_posts, actor_id, db)


