"""
User Profile API — GET /v1/users/me, PATCH /v1/users/me

Endpoints:
  GET   /v1/users/me — Return authenticated user's profile
  PATCH /v1/users/me — Partial update of user metrics and preferences
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.models import User, UserStyleProfile
from app.database.session import get_db
from app.schemas.auth import UpdateProfileRequest, UserResponse
from app.schemas.personalization import StyleProfileResponse
from app.services.personalization_engine import PersonalizationEngine
from sqlalchemy.future import select

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/users", tags=["User Profile"])


# ── GET /v1/users/me ──────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the full profile of the currently authenticated user.

    Requires a valid Bearer JWT in the Authorization header.
    """
    return UserResponse.model_validate(current_user)


# ── PATCH /v1/users/me ────────────────────────────────────────────────────────

@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_my_profile(
    payload: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Partially updates the authenticated user's profile.

    All fields are optional — only supplied fields are updated.
    Updatable fields include:
      - Personal details (first_name, last_name, gender, date_of_birth)
      - Body metrics (height_cm, weight_kg, body_type, preferred_fit)
      - Style intelligence (style_personas, avoided_colors, climate_region)

    Automatically marks onboarding_completed=True once height_cm and body_type are both set.
    """
    update_fields = payload.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        setattr(current_user, field, value)

    # Auto-complete onboarding when key profile fields are filled
    if current_user.height_cm and current_user.body_type:
        current_user.onboarding_completed = True

    current_user.updated_at = datetime.now(timezone.utc)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    logger.info(f"Profile updated for user: {current_user.email} (ID: {current_user.id})")
    return UserResponse.model_validate(current_user)


# ── GET /v1/users/style-profile ───────────────────────────────────────────────

@router.get("/style-profile", response_model=StyleProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_style_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves the authenticated user's calculated style profile.
    If no style profile has been generated yet, it compiles and returns an initial one.
    """
    result = await db.execute(
        select(UserStyleProfile)
        .where(UserStyleProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = await PersonalizationEngine.update_style_profile(current_user.id, db)

    return StyleProfileResponse.model_validate(profile)
