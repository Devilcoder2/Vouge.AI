import logging
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.models import (
    User, FashionCommunity, CommunityMember, SocialPost
)
from app.routes.wardrobe import get_optional_current_user
from app.schemas.community import (
    CommunityCreateRequest, CommunityResponse, CommunityMemberResponse
)
from app.schemas.social import PostResponse

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/social/communities", tags=["Fashion Communities"])


def generate_slug(name: str) -> str:
    """Generates a clean URL slug from a name."""
    clean = "".join(c for c in name.lower() if c.isalnum() or c.isspace())
    return "-".join(clean.split())


@router.post("", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED)
async def create_community(
    payload: CommunityCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Creates a new fashion community and assigns creator as admin."""
    actor = current_user
    if not actor:
        # Fallback query for testing
        res = await db.execute(select(User).limit(1))
        actor = res.scalar_one()

    slug = generate_slug(payload.name)

    # Check unique constraints
    existing_stmt = select(FashionCommunity).where(
        (FashionCommunity.name.ilike(payload.name)) | (FashionCommunity.slug == slug)
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fashion community with name or slug matching '{payload.name}' already exists."
        )

    community_id = uuid4()
    new_community = FashionCommunity(
        id=community_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        cover_image_url=payload.cover_image_url or "https://api.dicebear.com/7.x/identicon/svg?seed=" + slug,
        rules=payload.rules,
        creator_id=actor.id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_community)

    # Automatically add creator as admin member
    creator_membership = CommunityMember(
        community_id=community_id,
        user_id=actor.id,
        role="admin",
        joined_at=datetime.now(timezone.utc)
    )
    db.add(creator_membership)

    await db.commit()
    await db.refresh(new_community)

    return CommunityResponse(
        id=new_community.id,
        name=new_community.name,
        slug=new_community.slug,
        description=new_community.description,
        cover_image_url=new_community.cover_image_url,
        rules=new_community.rules,
        creator_id=new_community.creator_id,
        members_count=1,
        posts_count=0,
        is_joined=True,
        created_at=new_community.created_at
    )


@router.get("", response_model=List[CommunityResponse])
async def list_communities(
    q: Optional[str] = Query(None, description="Search communities by name or description"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Lists all fashion communities with optional query filtering."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    stmt = select(FashionCommunity)
    if q:
        stmt = stmt.where(
            (FashionCommunity.name.ilike(f"%{q}%")) | 
            (FashionCommunity.description.ilike(f"%{q}%"))
        )

    stmt = stmt.order_by(FashionCommunity.name.asc())
    result = await db.execute(stmt)
    communities = result.scalars().all()

    hydrated = []
    for c in communities:
        members_count = await db.scalar(
            select(func.count(CommunityMember.user_id)).where(CommunityMember.community_id == c.id)
        ) or 0
        posts_count = await db.scalar(
            select(func.count(SocialPost.id)).where(SocialPost.community_id == c.id)
        ) or 0
        is_joined = await db.scalar(
            select(func.count(CommunityMember.user_id)).where(
                and_(CommunityMember.community_id == c.id, CommunityMember.user_id == actor_id)
            )
        ) > 0

        hydrated.append(CommunityResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            cover_image_url=c.cover_image_url,
            rules=c.rules,
            creator_id=c.creator_id,
            members_count=members_count,
            posts_count=posts_count,
            is_joined=is_joined,
            created_at=c.created_at
        ))

    return hydrated


@router.get("/my", response_model=List[CommunityResponse])
async def get_my_communities(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves all fashion communities the active user has joined."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    stmt = (
        select(FashionCommunity)
        .join(CommunityMember, CommunityMember.community_id == FashionCommunity.id)
        .where(CommunityMember.user_id == actor_id)
        .order_by(FashionCommunity.name.asc())
    )
    result = await db.execute(stmt)
    communities = result.scalars().all()

    hydrated = []
    for c in communities:
        members_count = await db.scalar(
            select(func.count(CommunityMember.user_id)).where(CommunityMember.community_id == c.id)
        ) or 0
        posts_count = await db.scalar(
            select(func.count(SocialPost.id)).where(SocialPost.community_id == c.id)
        ) or 0

        hydrated.append(CommunityResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            cover_image_url=c.cover_image_url,
            rules=c.rules,
            creator_id=c.creator_id,
            members_count=members_count,
            posts_count=posts_count,
            is_joined=True,
            created_at=c.created_at
        ))

    return hydrated


@router.get("/{community_slug}", response_model=CommunityResponse)
async def get_community_details(
    community_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves detailed community info by URL handle slug."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    stmt = select(FashionCommunity).where(FashionCommunity.slug == community_slug)
    community = (await db.execute(stmt)).scalar_one_or_none()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community with slug '{community_slug}' not found."
        )

    members_count = await db.scalar(
        select(func.count(CommunityMember.user_id)).where(CommunityMember.community_id == community.id)
    ) or 0
    posts_count = await db.scalar(
        select(func.count(SocialPost.id)).where(SocialPost.community_id == community.id)
    ) or 0
    is_joined = await db.scalar(
        select(func.count(CommunityMember.user_id)).where(
            and_(CommunityMember.community_id == community.id, CommunityMember.user_id == actor_id)
        )
    ) > 0

    return CommunityResponse(
        id=community.id,
        name=community.name,
        slug=community.slug,
        description=community.description,
        cover_image_url=community.cover_image_url,
        rules=community.rules,
        creator_id=community.creator_id,
        members_count=members_count,
        posts_count=posts_count,
        is_joined=is_joined,
        created_at=community.created_at
    )


@router.post("/{community_id}/join", status_code=status.HTTP_200_OK)
async def join_community(
    community_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Registers the user as a community member."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # Check community exists
    exists = await db.scalar(select(func.count(FashionCommunity.id)).where(FashionCommunity.id == community_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Community not found.")

    # Check already member
    member_stmt = select(CommunityMember).where(
        and_(CommunityMember.community_id == community_id, CommunityMember.user_id == actor_id)
    )
    existing = (await db.execute(member_stmt)).scalar_one_or_none()
    if existing:
        return {"message": "You are already a member of this community."}

    new_member = CommunityMember(
        community_id=community_id,
        user_id=actor_id,
        role="member",
        joined_at=datetime.now(timezone.utc)
    )
    db.add(new_member)
    await db.commit()

    return {"message": "Successfully joined community."}


@router.post("/{community_id}/leave", status_code=status.HTTP_200_OK)
async def leave_community(
    community_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Removes user membership from community."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # Check community exists
    exists = await db.scalar(select(func.count(FashionCommunity.id)).where(FashionCommunity.id == community_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Community not found.")

    member_stmt = select(CommunityMember).where(
        and_(CommunityMember.community_id == community_id, CommunityMember.user_id == actor_id)
    )
    membership = (await db.execute(member_stmt)).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=400, detail="You are not a member of this community.")

    if membership.role == "admin":
        raise HTTPException(
            status_code=400, 
            detail="As an admin/creator, you cannot leave the community. Pass administrative role to another member first."
        )

    await db.delete(membership)
    await db.commit()

    return {"message": "Successfully left community."}


@router.get("/{community_id}/posts", response_model=List[PostResponse])
async def list_community_posts(
    community_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Lists chronological outfit posts uploaded to a specific community."""
    actor_id = current_user.id if current_user else UUID("00000000-0000-0000-0000-000000000001")

    # Check community exists
    exists = await db.scalar(select(func.count(FashionCommunity.id)).where(FashionCommunity.id == community_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Community not found.")

    query = (
        select(SocialPost)
        .where(SocialPost.community_id == community_id)
        .order_by(SocialPost.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    from app.routes.feed import map_posts_to_response
    return await map_posts_to_response(posts, actor_id, db)


@router.get("/{community_id}/members", response_model=List[CommunityMemberResponse])
async def list_community_members(
    community_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all members of a specific community organized by joining date."""
    # Check community exists
    exists = await db.scalar(select(func.count(FashionCommunity.id)).where(FashionCommunity.id == community_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Community not found.")

    stmt = (
        select(CommunityMember)
        .where(CommunityMember.community_id == community_id)
        .order_by(CommunityMember.joined_at.asc())
    )
    result = await db.execute(stmt)
    members = result.scalars().all()

    response_data = []
    for m in members:
        # Load user
        user = m.user
        response_data.append(CommunityMemberResponse(
            user_id=m.user_id,
            username=user.username if user else "anonymous",
            avatar_url=user.avatar_url if user else None,
            role=m.role,
            joined_at=m.joined_at
        ))

    return response_data
