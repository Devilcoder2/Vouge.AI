"""
Dynamic Calendar Planner API — GET/POST/PUT/DELETE /api/planner

Enables frontend lookbook scheduling, Pillow fit snapshot uploads, and AI auto-planning.
"""
import io
import logging
import uuid
from pathlib import Path
from datetime import date as date_type, datetime, timezone, timedelta
from typing import List, Optional
from PIL import Image

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_

from app.config import settings
from app.database.session import get_db
from app.auth.dependencies import get_current_active_user
from app.database.models import (
    User, ClothingItem, SavedOutfit, SavedOutfitItem,
    CalendarEntry, CalendarEntryItem, UserStyleProfile, WearLog
)
from app.schemas.planner import (
    PlannerItemResponse, PlannerWearLogResponse, PlannerSlotResponse,
    DailyPlannerResponse, PlannerRangeResponse, PlannerScheduleRequest,
    PlannerScheduleResponse, PlannerScheduleUpdateRequest, PlannerScheduleUpdateResponse,
    PlannerAutoGenerateRequest, PlannerAutoGenerateResponse, WearLogResponse
)

# AI recommendation components for outfit generation
from app.recommendation.generators.candidate_generator import CandidateGenerator
from app.recommendation.scorers.outfit_scorer import OutfitScorer
from app.recommendation.scorers.ranker import RecommendationRanker
from app.recommendation.explainers.outfit_explainer import OutfitExplainer
from app.recommendation.engines.body_engine import BodyTypeEngine
from app.recommendation.engines.persona_engine import StylePersonaEngine
from app.recommendation.engines.feedback_engine import FeedbackEngine
from app.recommendation.engines.embedding_similarity_engine import EmbeddingSimilarityEngine
from app.recommendation.engines.silhouette_engine import SilhouetteEngine
from app.services.personalization_engine import PersonalizationEngine
from app.routes.wardrobe import map_clothing_item_to_response

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/api/planner", tags=["Dynamic Calendar Planner"])
explainer = OutfitExplainer()


def map_calendar_entry_to_planner_slot(entry: CalendarEntry, wear_log: Optional[WearLog] = None) -> PlannerSlotResponse:
    """Helper mapping CalendarEntry and WearLog SQLAlchemy models to PlannerSlotResponse schemas."""
    # 1. Fetch custom items linked to this entry
    response_items = []
    for item in entry.items:
        gi = item.clothing_item
        if gi:
            image_url = gi.processed_image_url or gi.original_image_url
            if not image_url:
                if gi.processed_image_path:
                    image_url = f"/v1/media/file/processed/{Path(gi.processed_image_path).name}"
                elif gi.original_image_path:
                    image_url = f"/v1/media/file/raw/{Path(gi.original_image_path).name}"
            
            response_items.append(
                PlannerItemResponse(
                    id=gi.id,
                    name=gi.name or f"{gi.primary_color} {gi.subcategory}".title(),
                    category=gi.category.lower(),
                    processed_image_url=image_url
                )
            )

    # 2. Fetch items from SavedOutfit if response_items is empty
    if entry.outfit and not response_items:
        for link in entry.outfit.items:
            gi = link.clothing_item
            if gi:
                image_url = gi.processed_image_url or gi.original_image_url
                if not image_url:
                    if gi.processed_image_path:
                        image_url = f"/v1/media/file/processed/{Path(gi.processed_image_path).name}"
                    elif gi.original_image_path:
                        image_url = f"/v1/media/file/raw/{Path(gi.original_image_path).name}"
                response_items.append(
                    PlannerItemResponse(
                        id=gi.id,
                        name=gi.name or f"{gi.primary_color} {gi.subcategory}".title(),
                        category=gi.category.lower(),
                        processed_image_url=image_url
                    )
                )

    # 3. Map WearLog
    mapped_wear_log = None
    wl = entry.wear_log_rel or wear_log
    if wl:
        mapped_wear_log = PlannerWearLogResponse(
            log_id=wl.id,
            image_url=wl.image_url,
            notes=wl.notes,
            logged_at=wl.created_at
        )

    return PlannerSlotResponse(
        planned_outfit_id=entry.id,
        time_slot=entry.slot,
        occasion=entry.occasion or "CASUAL",
        outfit_source=entry.outfit_source or "custom_user",
        outfit_id=entry.outfit_id,
        notes=entry.notes,
        vogue_score=entry.vogue_score or 80,
        items=response_items,
        wear_log=mapped_wear_log
    )


# ── GET /api/planner ──────────────────────────────────────────────────────────
@router.get("", response_model=PlannerRangeResponse, status_code=status.HTTP_200_OK)
async def list_planner_entries(
    start_date: date_type = Query(..., description="Start date YYYY-MM-DD"),
    end_date: date_type = Query(..., description="End date YYYY-MM-DD"),
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves all planned scheduled outfits and user wear logs within a given date range.
    Handles rendering the visual calendar planner grids.
    """
    # 1. Query planned entries
    query = select(CalendarEntry).where(
        and_(
            CalendarEntry.user_id == current_user.id,
            CalendarEntry.date >= start_date,
            CalendarEntry.date <= end_date
        )
    ).order_by(CalendarEntry.date.asc(), CalendarEntry.created_at.asc())
    
    result = await db.execute(query)
    entries = result.scalars().all()

    # 2. Query wear logs in range
    logs_query = select(WearLog).where(
        and_(
            WearLog.user_id == current_user.id,
            WearLog.date >= start_date,
            WearLog.date <= end_date
        )
    )
    logs_result = await db.execute(logs_query)
    wear_logs = logs_result.scalars().all()
    
    # Map logs by entry UUID and date for fast binding
    logs_by_entry = {wl.planned_outfit_id: wl for wl in wear_logs if wl.planned_outfit_id}
    logs_by_date = {wl.date: wl for wl in wear_logs if not wl.planned_outfit_id}

    # 3. Compile daily calendar grid
    date_map = {}
    current_day = start_date
    while current_day <= end_date:
        date_map[current_day] = {
            "date": current_day,
            "day_of_week": current_day.strftime("%A").upper(),
            "planned_slots": []
        }
        current_day += timedelta(days=1)

    # Distribute entries
    for entry in entries:
        wl = logs_by_entry.get(entry.id) or logs_by_date.get(entry.date)
        if entry.date in date_map:
            date_map[entry.date]["planned_slots"].append(
                map_calendar_entry_to_planner_slot(entry, wl)
            )

    calendar_list = [DailyPlannerResponse(**val) for val in date_map.values()]

    return PlannerRangeResponse(
        start_date=start_date,
        end_date=end_date,
        calendar=calendar_list
    )


# ── POST /api/planner/schedule ───────────────────────────────────────────────
@router.post("/schedule", response_model=PlannerScheduleResponse, status_code=status.HTTP_201_CREATED)
async def schedule_planner_entry(
    payload: PlannerScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Schedules an outfit (saved outfit or custom dynamic garment ids) for a date and time slot.
    Checks uniqueness constraints to avoid overlapping slot schedules.
    """
    # 1. Enforce uniqueness: user_id + date + time_slot
    existing_res = await db.execute(
        select(CalendarEntry).where(
            and_(
                CalendarEntry.user_id == current_user.id,
                CalendarEntry.date == payload.date,
                CalendarEntry.slot == payload.time_slot
            )
        )
    )
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An outfit is already planned for the '{payload.time_slot}' slot on {payload.date}."
        )

    # 2. Check if saved outfit exists
    if payload.outfit_id:
        outfit_res = await db.execute(select(SavedOutfit).where(SavedOutfit.id == payload.outfit_id))
        outfit = outfit_res.scalar_one_or_none()
        if not outfit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved outfit '{payload.outfit_id}' not found."
            )

    # 3. Create entry
    entry = CalendarEntry(
        id=uuid.uuid4(),
        user_id=current_user.id,
        date=payload.date,
        slot=payload.time_slot,
        occasion=payload.occasion.upper(),
        outfit_source=payload.outfit_source,
        outfit_id=payload.outfit_id,
        notes=payload.notes,
        vogue_score=90 if payload.outfit_id else 80
    )
    db.add(entry)
    await db.flush()

    # 4. Insert custom items if built on the go
    items_count = 0
    if payload.clothing_item_ids:
        # Check all garment IDs exist in wardrobe
        for item_id in payload.clothing_item_ids:
            item_res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
            if not item_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Garment item '{item_id}' not found in closet."
                )
            
            link = CalendarEntryItem(
                id=uuid.uuid4(),
                calendar_entry_id=entry.id,
                clothing_item_id=item_id
            )
            db.add(link)
            items_count += 1
    
    await db.commit()
    
    return PlannerScheduleResponse(
        message="Outfit scheduled successfully",
        planned_outfit_id=entry.id,
        date=entry.date,
        time_slot=entry.slot,
        items_count=items_count
    )


# ── DELETE /api/planner/schedule/{planned_outfit_id} ──────────────────────────
@router.delete("/schedule/{planned_outfit_id}", status_code=status.HTTP_200_OK)
async def unschedule_planner_entry(
    planned_outfit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancels and removes a scheduled planned outfit block."""
    result = await db.execute(
        select(CalendarEntry)
        .where(and_(CalendarEntry.id == planned_outfit_id, CalendarEntry.user_id == current_user.id))
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned scheduled outfit block not found."
        )

    # Optional: Delete associated local photo if it exists
    if entry.real_photo_path:
        try:
            p = Path(entry.real_photo_path)
            if p.exists() and p.is_file():
                p.unlink()
                logger.info(f"Deleted local fit photo file: {entry.real_photo_path}")
        except Exception as file_err:
            logger.warning(f"Failed to delete photo file: {file_err}")

    await db.delete(entry)
    await db.commit()

    return {
        "message": "Planned outfit successfully unscheduled.",
        "planned_outfit_id": planned_outfit_id
    }


# ── PUT /api/planner/schedule/{planned_outfit_id} ─────────────────────────────
@router.put("/schedule/{planned_outfit_id}", response_model=PlannerScheduleUpdateResponse, status_code=status.HTTP_200_OK)
async def update_planner_entry(
    planned_outfit_id: uuid.UUID,
    payload: PlannerScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reschedules or updates an existing planned scheduled outfit.
    Allows changing slot date, slot name, custom clothing items, and remarks.
    """
    result = await db.execute(
        select(CalendarEntry)
        .where(and_(CalendarEntry.id == planned_outfit_id, CalendarEntry.user_id == current_user.id))
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned scheduled outfit block not found."
        )

    updated_fields = []

    # 1. Date or Slot uniqueness conflict check
    new_date = payload.date if payload.date is not None else entry.date
    new_slot = payload.time_slot if payload.time_slot is not None else entry.slot
    
    if payload.date is not None or payload.time_slot is not None:
        conflict_res = await db.execute(
            select(CalendarEntry).where(
                and_(
                    CalendarEntry.user_id == current_user.id,
                    CalendarEntry.date == new_date,
                    CalendarEntry.slot == new_slot,
                    CalendarEntry.id != planned_outfit_id
                )
            )
        )
        if conflict_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An outfit is already planned for the '{new_slot}' slot on {new_date}."
            )
        
        if payload.date is not None:
            entry.date = payload.date
            updated_fields.append("date")
        if payload.time_slot is not None:
            entry.slot = payload.time_slot
            updated_fields.append("time_slot")

    if payload.notes is not None:
        entry.notes = payload.notes
        updated_fields.append("notes")

    # 2. Update custom items links
    if payload.clothing_item_ids is not None:
        # Delete old items
        await db.execute(delete(CalendarEntryItem).where(CalendarEntryItem.calendar_entry_id == planned_outfit_id))
        
        # Link new ones
        for item_id in payload.clothing_item_ids:
            item_res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
            if not item_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Garment item '{item_id}' not found in closet."
                )
            
            link = CalendarEntryItem(
                id=uuid.uuid4(),
                calendar_entry_id=planned_outfit_id,
                clothing_item_id=item_id
            )
            db.add(link)
        
        updated_fields.append("clothing_item_ids")

    await db.commit()
    
    return PlannerScheduleUpdateResponse(
        message="Planned outfit schedule updated successfully.",
        planned_outfit_id=planned_outfit_id,
        updated_fields=updated_fields
    )


# ── POST /api/planner/auto-generate ──────────────────────────────────────────
@router.post("/auto-generate", response_model=PlannerAutoGenerateResponse, status_code=status.HTTP_200_OK)
async def auto_generate_planner_suggestions(
    payload: PlannerAutoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    AI Auto-Planner. Automatically curates and schedules weather-appropriate outfits
    across multiple days and slots dynamically based on the user's styling profile.
    """
    logger.info(f"AI Auto-Planner triggered user={current_user.id}, days={payload.days_count}")

    # 1. Retrieve user closet items
    item_res = await db.execute(select(ClothingItem))
    db_items = item_res.scalars().all()
    if not db_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your digital closet is empty! Please upload garments first to enable AI planning."
        )

    # 2. Fetch User Styling Profile
    profile_res = await db.execute(select(UserStyleProfile).where(UserStyleProfile.user_id == current_user.id))
    profile = profile_res.scalar_one_or_none()
    
    profile_dict = {
        "height_cm": current_user.height_cm or 180,
        "body_archetype": current_user.body_type or "rectangle",
        "fit_preference": "standard",
        "style_persona": "minimalist",
        "avoided_colors": [],
        "favorite_styles": []
    }
    if profile:
        profile_dict["style_persona"] = profile.preferred_styles[0] if profile.preferred_styles else "minimalist"
        profile_dict["avoided_colors"] = profile.disliked_colors

    auto_scheduled_count = 0
    planned_days = []

    # 3. Loop over daily agendas and generate slots
    for agenda in payload.agendas:
        # Season detection
        month = agenda.date.month
        if month in {12, 1, 2}:
            season = "winter"
        elif month in {3, 4, 5}:
            season = "spring"
        elif month in {6, 7, 8}:
            season = "summer"
        else:
            season = "autumn"

        planned_days.append(agenda.date)

        for slot in agenda.slots:
            slot_clean = slot.time_slot.lower()
            occasion = slot.occasion.lower()

            # Enforce deletion to plan fresh AI looks if slot exists
            existing_res = await db.execute(
                select(CalendarEntry).where(
                    and_(
                        CalendarEntry.user_id == current_user.id,
                        CalendarEntry.date == agenda.date,
                        CalendarEntry.slot == slot.time_slot
                    )
                )
            )
            existing = existing_res.scalar_one_or_none()
            if existing:
                await db.delete(existing)
                await db.flush()

            # Generate candidate template outfits
            candidates = CandidateGenerator.generate_candidates(db_items, occasion, season)
            if not candidates:
                logger.warning(f"Lacks compatible items for occasion '{occasion}' on {agenda.date}. Skipping slot.")
                continue

            # Score candidates
            scored_candidates = []
            for cand in candidates:
                score_res = OutfitScorer.score_outfit(cand["items"], occasion, season)
                base_score_01 = score_res["total_score"] / 100.0
                
                harmony_res = EmbeddingSimilarityEngine.calculate_visual_harmony(cand["items"])
                harmony_score = harmony_res["score"]
                
                body_res = BodyTypeEngine.calculate_body_compatibility(cand["items"], profile_dict)
                body_score = body_res["score"]
                
                persona_res = StylePersonaEngine.calculate_persona_compatibility(cand["items"], profile_dict["style_persona"])
                persona_score = persona_res["score"]
                
                silhouette_res = SilhouetteEngine.calculate_silhouette_balance(cand["items"], occasion, profile_dict["style_persona"])
                silhouette_score = silhouette_res["score"]
                
                combined_why = []
                combined_why.extend(body_res["why_selected"])
                combined_why.extend(persona_res["why_selected"])
                combined_why.extend(silhouette_res["why_selected"])
                
                final_score_val = round(base_score_01 * harmony_score * body_score * persona_score * silhouette_score * 100)
                final_score_val = max(0, min(100, final_score_val))

                scored_candidates.append({
                    "items": cand["items"],
                    "template_name": cand["template_name"],
                    "total_score": final_score_val,
                    "breakdown": score_res["breakdown"],
                    "reasons": score_res["reasons"],
                    "why_selected": list(set(combined_why)),
                    "outfit_embedding": harmony_res["outfit_embedding"]
                })

            # Apply boosts
            scored_candidates = await PersonalizationEngine.apply_recommendation_boosts(
                scored_candidates, current_user.id, db
            )

            # Rank and pick the top one
            top_candidates = RecommendationRanker.diversify_and_rank(scored_candidates, max_outputs=1)
            if not top_candidates:
                continue

            top_recommendation = explainer.explain_recommendations(top_candidates, occasion, season)[0]

            # Save as SavedOutfit
            ai_saved_outfit = SavedOutfit(
                id=uuid.uuid4(),
                user_id=str(current_user.id),
                name=f"AI Planned: {slot.time_slot}",
                occasion=occasion,
                season=season,
                score=top_recommendation["score"],
                reasoning=top_recommendation["reasoning"],
                preview_url="/assets/previews/ai_planner.png"
            )
            db.add(ai_saved_outfit)
            await db.flush()

            # Link items
            for it in top_recommendation["items"]:
                link = SavedOutfitItem(
                    id=uuid.uuid4(),
                    outfit_id=ai_saved_outfit.id,
                    clothing_item_id=it["id"]
                )
                db.add(link)

            # Save to Calendar planned entry
            entry = CalendarEntry(
                id=uuid.uuid4(),
                user_id=current_user.id,
                date=agenda.date,
                slot=slot.time_slot,
                occasion=occasion.upper(),
                outfit_source="saved_outfit",
                outfit_id=ai_saved_outfit.id,
                notes=top_recommendation["reasoning"],
                vogue_score=top_recommendation["score"]
            )
            db.add(entry)
            auto_scheduled_count += 1

    await db.commit()

    return PlannerAutoGenerateResponse(
        message="AI Calendar Auto-Planning successfully completed.",
        auto_scheduled_count=auto_scheduled_count,
        planned_days=planned_days
    )


# ── POST /api/planner/log-photo ──────────────────────────────────────────────
@router.post("/log-photo", response_model=WearLogResponse, status_code=status.HTTP_201_CREATED)
async def log_planner_photo(
    date: date_type = Form(..., description="Date YYYY-MM-DD when the outfit was worn"),
    planned_outfit_id: Optional[uuid.UUID] = Form(None, description="Optional link to a scheduled calendar entry ID"),
    notes: Optional[str] = Form(None, description="Remarks about the look or fit check reactions"),
    user_id: Optional[str] = Form(None, description="Optional user ID"),
    file: UploadFile = File(..., description="Fit check photo snap (MIME type JPG/PNG/WebP, max 10MB)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Logs a real-life snapshot of the user wearing their scheduled outfit.
    Allows Pillow optimization, cap aspect ratio locking, and S3 fallback.
    """
    # 1. Validate MIME type
    mime = file.content_type.lower()
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPEG, PNG, WebP."
        )

    # 2. Check content size limits
    contents = await file.read()
    if len(contents) > settings.MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum content length limit."
        )

    try:
        # Validate integrity via Pillow
        img = Image.open(io.BytesIO(contents))
        img.verify()
        
        # Re-open image for scaling & compression
        img = Image.open(io.BytesIO(contents))
        
        # Mobile aspect resizing: preserve aspect lock, cap width at 750px
        MAX_WIDTH = 750
        w, h = img.size
        if w > MAX_WIDTH:
            ratio = MAX_WIDTH / w
            new_size = (MAX_WIDTH, int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        ext = "png" if "png" in mime else "webp" if "webp" in mime else "jpg"
        unique_name = f"log_{uuid.uuid4()}.{ext}"
        
        # Save S3 vs Local Fallback
        if settings.USE_S3:
            buffer = io.BytesIO()
            fmt = "PNG" if ext == "png" else "WEBP" if ext == "webp" else "JPEG"
            img.save(buffer, format=fmt, optimize=True, quality=80)
            buffer.seek(0)
            
            # connectivity check
            from app.services.storage_service import storage_service
            storage_service.generate_presigned_upload_url(
                folder="calendar", filename=unique_name, content_type=mime
            )
            
            region = settings.AWS_S3_REGION_NAME
            if settings.AWS_S3_ENDPOINT_URL:
                download_url = f"{settings.AWS_S3_ENDPOINT_URL.rstrip('/')}/{settings.AWS_S3_BUCKET_NAME}/calendar/{unique_name}"
            else:
                download_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{region}.amazonaws.com/calendar/{unique_name}"
                
            image_path = f"calendar/{unique_name}"
            image_url = download_url
            
        else:
            local_dir = settings.UPLOAD_DIR / "calendar"
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / unique_name
            
            fmt = "PNG" if ext == "png" else "WEBP" if ext == "webp" else "JPEG"
            img.save(local_path, format=fmt, optimize=True, quality=80)
            
            image_path = str(local_path)
            image_url = f"/v1/media/file/calendar/{unique_name}"

        # Create WearLog
        log_entry = WearLog(
            id=uuid.uuid4(),
            user_id=current_user.id,
            date=date,
            image_path=image_path,
            image_url=image_url,
            notes=notes,
            planned_outfit_id=planned_outfit_id
        )
        db.add(log_entry)
        
        # Also sync directly to CalendarEntry if linked
        if planned_outfit_id:
            cal_res = await db.execute(select(CalendarEntry).where(CalendarEntry.id == planned_outfit_id))
            cal = cal_res.scalar_one_or_none()
            if cal:
                cal.real_photo_path = image_path
                cal.real_photo_url = image_url

        await db.commit()
        
        return WearLogResponse(
            message="Outfit wear snapshot logged successfully",
            log_id=log_entry.id,
            date=log_entry.date,
            image_url=log_entry.image_url,
            notes=log_entry.notes,
            planned_outfit_id=log_entry.planned_outfit_id
        )

    except Exception as e:
        logger.error(f"Failed to log fit check wear snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log wear snap: {str(e)}"
        )


# ── DELETE /api/planner/log-photo/{log_id} ────────────────────────────────────
@router.delete("/log-photo/{log_id}", status_code=status.HTTP_200_OK)
async def delete_wear_log_snap(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deletes a previously uploaded wear snapshot log and cleans up local storage."""
    result = await db.execute(
        select(WearLog)
        .where(and_(WearLog.id == log_id, WearLog.user_id == current_user.id))
    )
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wear log snapshot not found."
        )

    # Delete local physical file
    try:
        p = Path(log_entry.image_path)
        if p.exists() and p.is_file():
            p.unlink()
            logger.info(f"Deleted local wear log photo file: {log_entry.image_path}")
    except Exception as file_err:
        logger.warning(f"Failed to delete wear log file: {file_err}")

    # Remove links from CalendarEntry if linked
    if log_entry.planned_outfit_id:
        cal_res = await db.execute(select(CalendarEntry).where(CalendarEntry.id == log_entry.planned_outfit_id))
        cal = cal_res.scalar_one_or_none()
        if cal:
            cal.real_photo_path = None
            cal.real_photo_url = None

    await db.delete(log_entry)
    await db.commit()

    return {
        "message": "Logged wear snapshot deleted successfully.",
        "log_id": log_id
    }
