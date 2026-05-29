"""
Calendar API — GET/POST/PUT/DELETE /api/calendar/entries

Coordinates planned outfits and uploads actual fit check photos.
"""
import io
import logging
import uuid
from pathlib import Path
from datetime import date as date_type, datetime, timezone
from typing import List, Optional
from PIL import Image

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_

from app.config import settings
from app.database.session import get_db
from app.auth.dependencies import get_current_active_user
from app.database.models import (
    User, ClothingItem, SavedOutfit, SavedOutfitItem,
    CalendarEntry, CalendarEntryItem, UserStyleProfile
)
from app.schemas.calendar import (
    CalendarEntryCreateRequest, CalendarEntryUpdateRequest,
    CalendarEntryResponse, CalendarGenerateSuggestionsRequest
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
router = APIRouter(prefix="/api/calendar", tags=["Digital Wardrobe Calendar"])
explainer = OutfitExplainer()


def map_calendar_entry_to_response(entry: CalendarEntry) -> CalendarEntryResponse:
    """Helper mapping database models to CalendarEntryResponse schemas."""
    # Build linked items list safely
    response_items = []
    for item in entry.items:
        gi = item.clothing_item
        if gi:
            response_items.append({
                "id": item.id,
                "clothing_item_id": item.clothing_item_id,
                "clothing_item": map_clothing_item_to_response(gi)
            })

    # SavedOutfit Mapping
    mapped_outfit = None
    if entry.outfit:
        o = entry.outfit
        mapped_outfit = {
            "id": o.id,
            "user_id": o.user_id,
            "name": o.name,
            "occasion": o.occasion,
            "season": o.season,
            "score": o.score,
            "reasoning": o.reasoning,
            "preview_url": o.preview_url,
            "created_at": o.created_at or datetime.now(timezone.utc),
            "items": [
                {
                    "id": link.clothing_item.id,
                    "category": link.clothing_item.category,
                    "subcategory": link.clothing_item.subcategory,
                    "primary_color": link.clothing_item.primary_color,
                    "primary_color_hex": link.clothing_item.primary_color_hex or "#ffffff",
                    "fit": link.clothing_item.fit,
                    "style": link.clothing_item.style,
                    "formality": link.clothing_item.formality,
                    "pattern": link.clothing_item.pattern
                }
                for link in o.items
                if link.clothing_item
            ]
        }

    return CalendarEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        date=entry.date,
        slot=entry.slot,
        outfit_id=entry.outfit_id,
        outfit=mapped_outfit,
        items=response_items,
        real_photo_path=entry.real_photo_path,
        real_photo_url=entry.real_photo_url
    )


# ── GET /api/calendar/entries ────────────────────────────────────────────────
@router.get("/entries", response_model=List[CalendarEntryResponse], status_code=status.HTTP_200_OK)
async def list_calendar_entries(
    start_date: Optional[date_type] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[date_type] = Query(None, description="End date YYYY-MM-DD"),
    date: Optional[date_type] = Query(None, description="Specific date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lists calendar entries for the active authenticated user.
    Allows range queries (start_date/end_date) or specific date lookup.
    """
    query = select(CalendarEntry).where(CalendarEntry.user_id == current_user.id)

    if date:
        query = query.where(CalendarEntry.date == date)
    elif start_date and end_date:
        query = query.where(and_(CalendarEntry.date >= start_date, CalendarEntry.date <= end_date))

    query = query.order_by(CalendarEntry.date.asc(), CalendarEntry.created_at.asc())
    
    result = await db.execute(query)
    entries = result.scalars().all()

    return [map_calendar_entry_to_response(e) for e in entries]


# ── GET /api/calendar/entries/{entryId} ─────────────────────────────────────
@router.get("/entries/{entryId}", response_model=CalendarEntryResponse, status_code=status.HTTP_200_OK)
async def get_calendar_entry(
    entryId: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieves detailed properties of a single scheduled calendar entry."""
    result = await db.execute(
        select(CalendarEntry)
        .where(and_(CalendarEntry.id == entryId, CalendarEntry.user_id == current_user.id))
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar entry '{entryId}' not found."
        )

    return map_calendar_entry_to_response(entry)


# ── POST /api/calendar/entries ───────────────────────────────────────────────
@router.post("/entries", response_model=CalendarEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_entry(
    payload: CalendarEntryCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Creates a new outfit calendar event entry on a target date and slot.
    Allows planning a pre-saved outfit ID or custom items directly on the go.
    """
    logger.info(f"Creating calendar entry user={current_user.id}, date={payload.date}, slot={payload.slot}")

    # Check unique constraint on user_id + date + slot
    existing_res = await db.execute(
        select(CalendarEntry)
        .where(
            and_(
                CalendarEntry.user_id == current_user.id,
                CalendarEntry.date == payload.date,
                CalendarEntry.slot == payload.slot
            )
        )
    )
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An outfit is already scheduled for slot '{payload.slot}' on date {payload.date}."
        )

    # Validate outfit ID if provided
    if payload.outfit_id:
        outfit_res = await db.execute(select(SavedOutfit).where(SavedOutfit.id == payload.outfit_id))
        if not outfit_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved outfit '{payload.outfit_id}' not found."
            )

    # Verify custom clothing items if provided on-the-go
    clothing_items = []
    if payload.clothing_item_ids:
        for item_id in payload.clothing_item_ids:
            item_res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
            ci = item_res.scalar_one_or_none()
            if not ci:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Clothing item '{item_id}' not found."
                )
            clothing_items.append(ci)

    # Insert CalendarEntry row
    entry = CalendarEntry(
        id=None,
        user_id=current_user.id,
        date=payload.date,
        slot=payload.slot,
        outfit_id=payload.outfit_id
    )
    db.add(entry)
    await db.flush()  # populate entry.id

    # Insert CalendarEntryItem junction rows if custom items provided
    if clothing_items:
        for ci in clothing_items:
            junction = CalendarEntryItem(
                id=None,
                calendar_entry_id=entry.id,
                clothing_item_id=ci.id
            )
            db.add(junction)

    await db.commit()
    
    # Reload fully mapped relationships
    reload_res = await db.execute(select(CalendarEntry).where(CalendarEntry.id == entry.id))
    entry = reload_res.scalar_one()

    return map_calendar_entry_to_response(entry)


# ── PUT /api/calendar/entries/{entryId} ──────────────────────────────────────
@router.put("/entries/{entryId}", response_model=CalendarEntryResponse, status_code=status.HTTP_200_OK)
async def update_calendar_entry(
    entryId: uuid.UUID,
    payload: CalendarEntryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Updates occasion slots, outfit IDs, or custom garments array on a planned calendar entry."""
    result = await db.execute(
        select(CalendarEntry)
        .where(and_(CalendarEntry.id == entryId, CalendarEntry.user_id == current_user.id))
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar entry '{entryId}' not found."
        )

    # Update slot if provided
    if payload.slot is not None:
        # Check unique constraint if slot/date change overlaps
        dup_res = await db.execute(
            select(CalendarEntry)
            .where(
                and_(
                    CalendarEntry.user_id == current_user.id,
                    CalendarEntry.date == entry.date,
                    CalendarEntry.slot == payload.slot,
                    CalendarEntry.id != entry.id
                )
            )
        )
        if dup_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An outfit is already scheduled for slot '{payload.slot}' on date {entry.date}."
            )
        entry.slot = payload.slot

    # Update outfit link if provided
    if payload.outfit_id is not None:
        outfit_res = await db.execute(select(SavedOutfit).where(SavedOutfit.id == payload.outfit_id))
        if not outfit_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved outfit '{payload.outfit_id}' not found."
            )
        entry.outfit_id = payload.outfit_id

    # Update photo details if provided
    if payload.real_photo_url is not None:
        entry.real_photo_url = payload.real_photo_url
    if payload.real_photo_path is not None:
        entry.real_photo_path = payload.real_photo_path

    # Update custom items list if provided
    if payload.clothing_item_ids is not None:
        # Cascade-delete current linked entry items first
        await db.execute(delete(CalendarEntryItem).where(CalendarEntryItem.calendar_entry_id == entry.id))
        
        # Link new garments
        for item_id in payload.clothing_item_ids:
            item_res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
            ci = item_res.scalar_one_or_none()
            if not ci:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Clothing item '{item_id}' not found."
                )
            junction = CalendarEntryItem(
                id=None,
                calendar_entry_id=entry.id,
                clothing_item_id=ci.id
            )
            db.add(junction)

    await db.commit()
    
    # Reload fully mapped relationships
    reload_res = await db.execute(select(CalendarEntry).where(CalendarEntry.id == entry.id))
    entry = reload_res.scalar_one()

    return map_calendar_entry_to_response(entry)


# ── DELETE /api/calendar/entries/{entryId} ───────────────────────────────────
@router.delete("/entries/{entryId}", status_code=status.HTTP_200_OK)
async def delete_calendar_entry(
    entryId: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deletes calendar planned entries (Linked SavedOutfits remain completely unaffected)."""
    result = await db.execute(
        select(CalendarEntry)
        .where(and_(CalendarEntry.id == entryId, CalendarEntry.user_id == current_user.id))
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar entry '{entryId}' not found."
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

    return {"success": True, "message": "Calendar planned entry deleted successfully."}


# ── POST /api/calendar/entries/{entryId}/photo ──────────────────────────────
@router.post("/entries/{entryId}/photo", response_model=CalendarEntryResponse, status_code=status.HTTP_200_OK)
async def upload_calendar_photo(
    entryId: uuid.UUID,
    file: UploadFile = File(..., description="Actual fit check image file (MIME type JPG/PNG/WebP, max 10MB)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Uploads a real fit check photo for a planned entry.
    Optimizes and scales image aspect ratios (mobile standards) securely via Pillow before saving.
    """
    result = await db.execute(
        select(CalendarEntry)
        .where(and_(CalendarEntry.id == entryId, CalendarEntry.user_id == current_user.id))
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar entry '{entryId}' not found."
        )

    # Validate MIME type
    mime = file.content_type.lower()
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPEG, PNG, WebP."
        )

    # Read binary bytes
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
        
        # Mobile-optimizing scaling: preserve aspect ratio, cap max width at 750px
        MAX_WIDTH = 750
        w, h = img.size
        if w > MAX_WIDTH:
            ratio = MAX_WIDTH / w
            new_size = (MAX_WIDTH, int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        # Compile unique filename safely
        ext = "png" if "png" in mime else "webp" if "webp" in mime else "jpg"
        unique_name = f"{uuid.uuid4()}.{ext}"
        
        # Local fallback vs S3 Cloud Storage
        if settings.USE_S3:
            # Output optimized bytes
            buffer = io.BytesIO()
            fmt = "PNG" if ext == "png" else "WEBP" if ext == "webp" else "JPEG"
            img.save(buffer, format=fmt, optimize=True, quality=80)
            buffer.seek(0)
            
            # S3 client upload via storage_service
            from app.services.storage_service import storage_service
            storage_service.generate_presigned_upload_url(
                folder="calendar", filename=unique_name, content_type=mime
            ) # test connectivity/permissions
            
            # Since S3 is mock or live, save URL cleanly
            region = settings.AWS_S3_REGION_NAME
            if settings.AWS_S3_ENDPOINT_URL:
                download_url = f"{settings.AWS_S3_ENDPOINT_URL.rstrip('/')}/{settings.AWS_S3_BUCKET_NAME}/calendar/{unique_name}"
            else:
                download_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{region}.amazonaws.com/calendar/{unique_name}"
            
            entry.real_photo_path = f"calendar/{unique_name}"
            entry.real_photo_url = download_url
            
        else:
            # Save under local settings directory
            local_dir = settings.UPLOAD_DIR / "calendar"
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / unique_name
            
            fmt = "PNG" if ext == "png" else "WEBP" if ext == "webp" else "JPEG"
            img.save(local_path, format=fmt, optimize=True, quality=80)
            
            entry.real_photo_path = str(local_path)
            entry.real_photo_url = f"/v1/media/file/calendar/{unique_name}"
            
        await db.commit()
        await db.refresh(entry)
        
        logger.info(f"Calendar fit photo uploaded successfully for entry '{entryId}' by user {current_user.id}")
        return map_calendar_entry_to_response(entry)

    except Exception as img_err:
        logger.error(f"Failed to process and upload calendar entry fit photo: {img_err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile photo: {str(img_err)}"
        )


# ── POST /api/calendar/generate-suggestions ───────────────────────────────
@router.post("/generate-suggestions", response_model=CalendarEntryResponse, status_code=status.HTTP_201_CREATED)
async def generate_calendar_ai_suggestion(
    payload: CalendarGenerateSuggestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    AI Outfit Planner. Generates high-fidelity compatible outfit recommendations
    tailored to weather, body archetype, preferred styles, and feedback.
    Saves the top recommendation and plans it directly inside the target date calendar slot.
    """
    logger.info(f"AI Calendar Planner triggered user={current_user.id}, date={payload.date}, slot={payload.slot}")

    # Check unique constraint on user_id + date + slot
    existing_res = await db.execute(
        select(CalendarEntry)
        .where(
            and_(
                CalendarEntry.user_id == current_user.id,
                CalendarEntry.date == payload.date,
                CalendarEntry.slot == payload.slot
            )
        )
    )
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An outfit is already scheduled for slot '{payload.slot}' on date {payload.date}."
        )

    # 1. Map slot name to occasion
    slot_clean = payload.slot.lower()
    if "gym" in slot_clean or "workout" in slot_clean or "exercise" in slot_clean:
        occasion = "gym"
    elif "office" in slot_clean or "work" in slot_clean or "meeting" in slot_clean:
        occasion = "work"
    elif "evening" in slot_clean or "date" in slot_clean or "party" in slot_clean:
        occasion = "evening"
    else:
        occasion = "casual"

    # 2. Map date month to season
    month = payload.date.month
    if month in {12, 1, 2}:
        season = "winter"
    elif month in {3, 4, 5}:
        season = "spring"
    elif month in {6, 7, 8}:
        season = "summer"
    else:
        season = "autumn"

    # 3. Query all user closet items
    item_res = await db.execute(select(ClothingItem))
    db_items = item_res.scalars().all()
    if not db_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your digital closet is empty! Please upload garments first to enable AI planning."
        )

    # 4. Fetch User Styling Profiles and interactions
    profile_res = await db.execute(select(UserStyleProfile).where(UserStyleProfile.user_id == current_user.id))
    profile = profile_res.scalar_one_or_none()
    
    # Compile preference dict
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

    # 5. Generate template candidate combinations
    candidates = CandidateGenerator.generate_candidates(db_items, occasion, season)
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lacks compatible items in digital wardrobe to plan an outfit for occasion '{occasion}' ({season})."
        )

    # 6. Score candidate combinations using ensemble engines
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
        
        feedback_adj = 1.0  # mock feedback adjustments
        
        silhouette_res = SilhouetteEngine.calculate_silhouette_balance(cand["items"], occasion, profile_dict["style_persona"])
        silhouette_score = silhouette_res["score"]
        
        combined_why = []
        combined_why.extend(body_res["why_selected"])
        combined_why.extend(persona_res["why_selected"])
        combined_why.extend(silhouette_res["why_selected"])
        
        final_score_val = round(base_score_01 * harmony_score * body_score * persona_score * feedback_adj * silhouette_score * 100)
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

    # Apply real-time personalization boosts
    scored_candidates = await PersonalizationEngine.apply_recommendation_boosts(
        scored_candidates, current_user.id, db
    )

    # Rank and select best scored outfit
    top_candidates = RecommendationRanker.diversify_and_rank(scored_candidates, max_outputs=1)
    if not top_candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI failed to generate compatible outfit scores."
        )

    # Stylist explanation rerank fallback
    final_outfits = explainer.explain_recommendations(top_candidates, occasion, season)
    top_recommendation = final_outfits[0]

    # Save curated AI recommendation persistently as a SavedOutfit
    ai_saved_outfit = SavedOutfit(
        id=None,
        user_id=str(current_user.id),
        name=f"AI Planned: {payload.slot.title()}",
        occasion=occasion,
        season=season,
        score=top_recommendation["score"],
        reasoning=top_recommendation["reasoning"],
        preview_url="/assets/previews/ai_planner.png"
    )
    db.add(ai_saved_outfit)
    await db.flush()

    # Link outfit items
    for it in top_recommendation["items"]:
        link = SavedOutfitItem(
            id=None,
            outfit_id=ai_saved_outfit.id,
            clothing_item_id=it["id"]
        )
        db.add(link)

    # Save to Calendar planned entry
    entry = CalendarEntry(
        id=None,
        user_id=current_user.id,
        date=payload.date,
        slot=payload.slot,
        outfit_id=ai_saved_outfit.id
    )
    db.add(entry)
    await db.commit()

    # Reload relationships for the completed planned entry response
    reload_res = await db.execute(select(CalendarEntry).where(CalendarEntry.id == entry.id))
    entry = reload_res.scalar_one()

    return map_calendar_entry_to_response(entry)
