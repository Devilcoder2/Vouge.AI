"""
Personalization Router — POST /v1/recommendations/feedback
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_active_user
from app.database.models import (
    User,
    RecommendationFeedback,
    UserBehaviorEvent,
    SavedOutfit,
)
from app.database.session import get_db
from app.schemas.personalization import FeedbackRequest, FeedbackResponse
from app.services.personalization_engine import PersonalizationEngine

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/recommendations", tags=["Personalization & Feedback"])

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_recommendation_feedback(
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submits user interaction feedback (like, save, dismiss, regenerate) on recommendation outfits.
    Dynamically learns preferences and updates the persistent style profile in real-time.
    """
    action = payload.action.lower()
    if action not in ["like", "save", "dismiss", "regenerate"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action type '{action}'. Allowed: like, save, dismiss, regenerate"
        )

    try:
        # 1. Create feedback row
        feedback = RecommendationFeedback(
            user_id=current_user.id,
            outfit_id=payload.outfit_id,
            action_type=action,
        )
        db.add(feedback)

        # 2. Try to resolve outfit items to write a detailed behavior event
        items_list = []
        if payload.outfit_id:
            try:
                # Check if it corresponds to a SavedOutfit
                outfit_uuid = UUID(payload.outfit_id)
                outfit_res = await db.execute(
                    select(SavedOutfit)
                    .options(selectinload(SavedOutfit.items))
                    .where(SavedOutfit.id == outfit_uuid)
                )
                saved_outfit = outfit_res.scalar_one_or_none()
                if saved_outfit:
                    for link in saved_outfit.items:
                        gi = link.clothing_item
                        if gi:
                            items_list.append({
                                "primary_color": gi.primary_color,
                                "style": gi.style,
                                "fit": gi.fit,
                                "category": gi.category,
                                "formality": gi.formality,
                            })
            except (ValueError, TypeError):
                # outfit_id is not a valid UUID or failed to fetch
                pass

        # 3. Create behavior event row
        # Maps action -> event_type
        event_type_map = {
            "like": "outfit_liked",
            "save": "outfit_saved",
            "dismiss": "outfit_dismissed",
            "regenerate": "outfit_regenerated",
        }
        
        event = UserBehaviorEvent(
            user_id=current_user.id,
            event_type=event_type_map[action],
            event_metadata={"outfit_id": payload.outfit_id, "items": items_list},
        )
        db.add(event)

        # Commit feedback and behavior event
        await db.commit()

        # 4. Trigger profile recalculation in real-time
        await PersonalizationEngine.update_style_profile(current_user.id, db)

        return FeedbackResponse(
            success=True,
            message=f"Interaction '{action}' recorded successfully and profile updated."
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error submitting recommendation feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )
