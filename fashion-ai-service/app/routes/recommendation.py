import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID, uuid4
from typing import List
from datetime import datetime, timezone


from app.config import settings
from app.database.session import get_db
from app.database.models import ClothingItem, SavedOutfit, SavedOutfitItem, UserProfile, UserFeedback
from app.schemas.recommendation import (
    GenerateOutfitsRequest,
    GenerateOutfitsResponse,
    SingleOutfitResponse,
    RecommendationItemResponse,
    OutfitScoreBreakdown,
    SaveOutfitRequest,
    SavedOutfitResponse,
    GapAnalysisResponse,
    VersatilityResponse,
    UserProfileSetupRequest,
    UserProfileResponse,
    UserFeedbackRequest,
    OutfitPreviewRequest,
    PaginatedSavedOutfitResponse,
    PaginatedGapAnalysisResponse,
    PaginatedVersatilityResponse,
    PaginationMeta,
)

from app.services.outfit_preview_builder import OutfitPreviewBuilder
from app.recommendation.generators.candidate_generator import CandidateGenerator
from app.recommendation.scorers.outfit_scorer import OutfitScorer
from app.recommendation.scorers.ranker import RecommendationRanker
from app.recommendation.explainers.outfit_explainer import OutfitExplainer
from app.recommendation.evaluators.quality_evaluator import QualityEvaluator
from app.recommendation.engines.gap_analysis import GapAnalysisEngine
from app.recommendation.engines.versatility_engine import VersatilityEngine
from app.recommendation.engines.body_engine import BodyTypeEngine
from app.recommendation.engines.persona_engine import StylePersonaEngine
from app.recommendation.engines.feedback_engine import FeedbackEngine
from app.recommendation.engines.embedding_similarity_engine import EmbeddingSimilarityEngine
from app.recommendation.engines.silhouette_engine import SilhouetteEngine


logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/recommendations", tags=["Outfit Recommendations"])
explainer = OutfitExplainer()

@router.post("/generate-outfits", response_model=GenerateOutfitsResponse, status_code=status.HTTP_200_OK)
async def generate_outfits(
    payload: GenerateOutfitsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 13 Route: Generates compatible outfits, ranks and diversifies choices,
    curates stylist explanations via Gemini, and evaluates recommendation lists.
    """
    # 1. Fetch user closet items
    result = await db.execute(select(ClothingItem))
    db_items = result.scalars().all()
    
    if not db_items:
        return GenerateOutfitsResponse(outfits=[], diversity_eval={
            "diversity_index": 0.0,
            "average_score": 0.0,
            "unique_items_ratio": 0.0,
            "verdict": "Your closet is empty! Upload clothing items to generate recommendations."
        })
        
    try:
        # Fetch user profile and feedback history to personalize recommendations
        try:
            profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == payload.user_id))
            db_profile = profile_res.scalar_one_or_none()
        except Exception as profile_err:
            logger.warning(f"Unable to load UserProfile from database (using fallback): {str(profile_err)}")
            db_profile = None
        
        if db_profile:
            profile_dict = {
                "height_cm": db_profile.height_cm,
                "body_archetype": db_profile.body_archetype,
                "fit_preference": db_profile.fit_preference,
                "style_persona": db_profile.style_persona,
                "avoided_colors": db_profile.avoided_colors,
                "favorite_styles": db_profile.favorite_styles
            }
        else:
            profile_dict = {
                "height_cm": None,
                "body_archetype": "rectangle",
                "fit_preference": "standard",
                "style_persona": "minimalist",
                "avoided_colors": [],
                "favorite_styles": []
            }
            
        try:
            fb_res = await db.execute(select(UserFeedback).where(UserFeedback.user_id == payload.user_id))
            db_feedbacks = fb_res.scalars().all()
        except Exception as fb_err:
            logger.warning(f"Unable to load UserFeedback from database (using fallback): {str(fb_err)}")
            db_feedbacks = []
            
        feedback_list = [
            {"feedback_type": fb.feedback_type, "outfit_item_ids": fb.outfit_item_ids}
            for fb in db_feedbacks
            if hasattr(fb, "feedback_type")
        ]



        # 2. Generate matching template combinations with early pruning
        candidates = CandidateGenerator.generate_candidates(
            db_items, payload.occasion, payload.season
        )
        
        if not candidates:
            return GenerateOutfitsResponse(outfits=[], diversity_eval={
                "diversity_index": 0.0,
                "average_score": 0.0,
                "unique_items_ratio": 0.0,
                "verdict": "Lacks category/formality matches. Upload more diverse clothes to unlock outfits."
            })
            
        # 3. Apply high-fidelity ensemble scoring incorporating all personalization & visual engines
        scored_candidates = []
        for cand in candidates:
            score_res = OutfitScorer.score_outfit(
                cand["items"], payload.occasion, payload.season
            )
            base_score_01 = score_res["total_score"] / 100.0
            
            # A. Visual harmony similarity & pooled outfit embedding
            harmony_res = EmbeddingSimilarityEngine.calculate_visual_harmony(cand["items"])
            harmony_score = harmony_res["score"]
            outfit_embedding = harmony_res["outfit_embedding"]
            
            # B. Body archetype proportions
            body_res = BodyTypeEngine.calculate_body_compatibility(cand["items"], profile_dict)
            body_score = body_res["score"]
            
            # C. Style persona matching
            persona_res = StylePersonaEngine.calculate_persona_compatibility(cand["items"], profile_dict["style_persona"])
            persona_score = persona_res["score"]
            
            # D. User interaction feedback adjustments
            feedback_res = FeedbackEngine.calculate_feedback_adjustments(cand["items"], profile_dict, feedback_list)
            feedback_adj = feedback_res["adjustment_factor"]
            
            # E. Silhouette proportions balance
            silhouette_res = SilhouetteEngine.calculate_silhouette_balance(cand["items"], payload.occasion, profile_dict["style_persona"])
            silhouette_score = silhouette_res["score"]
            
            # F. Pool all personal styling reasons
            combined_why = []
            combined_why.extend(body_res["why_selected"])
            combined_why.extend(persona_res["why_selected"])
            combined_why.extend(feedback_res["why_selected"])
            combined_why.extend(silhouette_res["why_selected"])
            
            if not combined_why:
                combined_why.append("Balanced neutral aesthetic silhouette compatibility.")
                
            # Compile final personalized score bounded between 0 and 100
            final_score_val = round(base_score_01 * harmony_score * body_score * persona_score * feedback_adj * silhouette_score * 100)
            final_score_val = max(0, min(100, final_score_val))

            scored_candidates.append({
                "items": cand["items"],
                "template_name": cand["template_name"],
                "total_score": final_score_val,
                "breakdown": score_res["breakdown"],
                "reasons": score_res["reasons"],
                "why_selected": list(set(combined_why)),
                "outfit_embedding": outfit_embedding
            })

        # Apply Phase 3A Feature 2: Real-time personalization boosts/penalties
        try:
            user_uuid = UUID(payload.user_id)
            from app.services.personalization_engine import PersonalizationEngine
            scored_candidates = await PersonalizationEngine.apply_recommendation_boosts(
                scored_candidates, user_uuid, db
            )
        except (ValueError, TypeError):
            # Gracefully fallback for string user IDs used in Phase 2
            pass
            
        # 4. Filter and diversify (prevents visual redundancy)
        top_candidates = RecommendationRanker.diversify_and_rank(
            scored_candidates, max_outputs=10
        )
        
        # 5. Gemini visual synergy reranking and stylist explanations
        final_outfits = explainer.explain_recommendations(
            top_candidates, payload.occasion, payload.season
        )
        
        # 6. Recommendation Quality Assessment
        diversity_eval = QualityEvaluator.evaluate_recommendations_diversity(final_outfits)
        
        # Format response objects
        response_outfits = []
        for outfit in final_outfits:
            res_items = [
                RecommendationItemResponse(
                    id=it["id"],
                    category=it["category"],
                    subcategory=it.get("subcategory", ""),
                    primary_color=it["primary_color"],
                    primary_color_hex=it["primary_color_hex"],
                    fit=it["fit"],
                    style=it["style"],
                    formality=it["formality"],
                    pattern=it["pattern"]
                )
                for it in outfit["items"]
            ]
            
            # Compose outfit preview image
            preview_url: str | None = None
            try:
                preview_filename = f"{uuid.uuid4()}_preview.png"
                preview_path = settings.PREVIEWS_DIR / preview_filename
                OutfitPreviewBuilder.build_preview(
                    outfit_items=outfit["items"],
                    score=outfit["score"],
                    occasion=payload.occasion,
                    season=payload.season,
                    reasoning=outfit.get("reasoning"),
                    output_path=preview_path,
                )
                preview_url = f"/recommendations/preview-image/{preview_filename}"
            except Exception as prev_err:
                logger.warning(f"Preview generation skipped for outfit: {prev_err}")
            
            response_outfits.append(
                SingleOutfitResponse(
                    score=outfit["score"],
                    items=res_items,
                    reasoning=outfit["reasoning"],
                    template_name=outfit["template_name"],
                    breakdown=OutfitScoreBreakdown(
                        color_score=outfit["breakdown"]["color_score"],
                        style_score=outfit["breakdown"]["style_score"],
                        occasion_score=outfit["breakdown"]["occasion_score"],
                        formality_score=outfit["breakdown"]["formality_score"],
                        season_score=outfit["breakdown"]["season_score"]
                    ),
                    why_selected=outfit.get("why_selected", []),
                    preview_url=preview_url,
                )
            )

            
        return GenerateOutfitsResponse(outfits=response_outfits, diversity_eval=diversity_eval)

        
    except Exception as e:
        logger.error(f"Failed to generate outfits: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation engine failed: {str(e)}"
        )

@router.post("/save-outfit", response_model=SavedOutfitResponse, status_code=status.HTTP_201_CREATED)
async def save_outfit(
    payload: SaveOutfitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Saves a curated outfit recommendations list to the database.
    """
    try:
        # Validate that all garment IDs exist in wardrobe
        clothing_items = []
        for item_id in payload.clothing_item_ids:
            it_res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
            clothing_item = it_res.scalar_one_or_none()
            if not clothing_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Garment with ID '{item_id}' does not exist."
                )
            clothing_items.append(clothing_item)
            
        outfit_id = uuid4()
        
        # Save outfit master row
        db_outfit = SavedOutfit(
            id=outfit_id,
            user_id=payload.user_id,
            name=payload.name,
            occasion=payload.occasion,
            season=payload.season,
            score=payload.score,
            reasoning=payload.reasoning,
            preview_url=payload.preview_url
        )
        
        db.add(db_outfit)
        
        # Save outfit item link mappings
        for garment in clothing_items:
            link = SavedOutfitItem(
                id=uuid4(),
                outfit_id=outfit_id,
                clothing_item_id=garment.id
            )
            db.add(link)
            
        await db.commit()
        await db.refresh(db_outfit)
        
        response_items = [
            RecommendationItemResponse(
                id=gi.id,
                category=gi.category,
                subcategory=gi.subcategory,
                primary_color=gi.primary_color,
                primary_color_hex=gi.primary_color_hex or "#ffffff",
                fit=gi.fit,
                style=gi.style,
                formality=gi.formality,
                pattern=gi.pattern
            )
            for gi in clothing_items
        ]
        
        return SavedOutfitResponse(
            id=db_outfit.id,
            user_id=db_outfit.user_id,
            name=db_outfit.name,
            occasion=db_outfit.occasion,
            season=db_outfit.season,
            score=db_outfit.score,
            reasoning=db_outfit.reasoning,
            preview_url=db_outfit.preview_url,
            created_at=db_outfit.created_at or datetime.now(timezone.utc),
            items=response_items
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving outfit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save outfit: {str(e)}"
        )

@router.get("/saved-outfits", response_model=PaginatedSavedOutfitResponse, status_code=status.HTTP_200_OK)
async def get_saved_outfits(
    user_id: str = "default_user",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all previously saved outfit combinations. Supports pagination.
    """
    try:
        # Calculate total matching count
        total_count = await db.scalar(
            select(func.count())
            .select_from(SavedOutfit)
            .where(SavedOutfit.user_id == user_id)
        ) or 0

        offset = (page - 1) * limit
        result = await db.execute(
            select(SavedOutfit)
            .where(SavedOutfit.user_id == user_id)
            .order_by(SavedOutfit.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        outfits = result.scalars().all()
        
        response = []
        for outfit in outfits:
            res_items = []
            for link in outfit.items:
                gi = link.clothing_item
                if gi:
                    res_items.append(
                        RecommendationItemResponse(
                            id=gi.id,
                            category=gi.category,
                            subcategory=gi.subcategory,
                            primary_color=gi.primary_color,
                            primary_color_hex=gi.primary_color_hex or "#ffffff",
                            fit=gi.fit,
                            style=gi.style,
                            formality=gi.formality,
                            pattern=gi.pattern
                        )
                    )
            response.append(
                SavedOutfitResponse(
                    id=outfit.id,
                    user_id=outfit.user_id,
                    name=outfit.name,
                    occasion=outfit.occasion,
                    season=outfit.season,
                    score=outfit.score,
                    reasoning=outfit.reasoning,
                    preview_url=outfit.preview_url,
                    created_at=outfit.created_at or datetime.now(timezone.utc),
                    items=res_items
                )
            )
            
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        meta = PaginationMeta(
            currentPage=page,
            pageSize=limit,
            totalPages=total_pages,
            totalCount=total_count,
            hasNextPage=page < total_pages,
            hasPrevPage=page > 1
        )
        
        return PaginatedSavedOutfitResponse(data=response, meta=meta)
    except Exception as e:
        logger.error(f"Error retrieving outfits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query saved outfits: {str(e)}"
        )

@router.delete("/saved-outfits/{outfit_id}", status_code=status.HTTP_200_OK)
async def delete_saved_outfit(
    outfit_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a specific saved outfit recommendation from the database.
    """
    try:
        result = await db.execute(select(SavedOutfit).where(SavedOutfit.id == outfit_id))
        outfit = result.scalar_one_or_none()
        if not outfit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved outfit with ID '{outfit_id}' not found."
            )
            
        await db.delete(outfit)
        await db.commit()
        return {"message": f"Successfully deleted saved outfit ID: {outfit_id}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting outfit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete saved outfit: {str(e)}"
        )

@router.get("/gap-analysis", response_model=PaginatedGapAnalysisResponse, status_code=status.HTTP_200_OK)
async def get_gap_analysis(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 15 Engine: Analyzes missing essential elements in user wardrobe
    and calculates new outfit combinations they would unlock. Supports pagination.
    """
    try:
        result = await db.execute(select(ClothingItem))
        db_items = result.scalars().all()
        gaps = GapAnalysisEngine.analyze_gaps(db_items)
        
        total_count = len(gaps)
        offset = (page - 1) * limit
        paginated_gaps = gaps[offset : offset + limit]
        
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        meta = PaginationMeta(
            currentPage=page,
            pageSize=limit,
            totalPages=total_pages,
            totalCount=total_count,
            hasNextPage=page < total_pages,
            hasPrevPage=page > 1
        )
        
        return PaginatedGapAnalysisResponse(data=paginated_gaps, meta=meta)
    except Exception as e:
        logger.error(f"Gap analysis route failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap analysis failed: {str(e)}"
        )

@router.get("/versatility", response_model=PaginatedVersatilityResponse, status_code=status.HTTP_200_OK)
async def get_versatility_report(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 16 Engine: Ranks all closet garments by versatility and outfit reuse counts. Supports pagination.
    """
    try:
        result = await db.execute(select(ClothingItem))
        db_items = result.scalars().all()
        versatility = VersatilityEngine.calculate_versatility(db_items)
        
        total_count = len(versatility)
        offset = (page - 1) * limit
        paginated_versatility = versatility[offset : offset + limit]
        
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        meta = PaginationMeta(
            currentPage=page,
            pageSize=limit,
            totalPages=total_pages,
            totalCount=total_count,
            hasNextPage=page < total_pages,
            hasPrevPage=page > 1
        )
        
        return PaginatedVersatilityResponse(data=paginated_versatility, meta=meta)
    except Exception as e:
        logger.error(f"Versatility report route failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Versatility analysis failed: {str(e)}"
        )

@router.post("/profile", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def setup_or_update_profile(
    payload: UserProfileSetupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sets up or updates the user's body type and styling persona profile.
    """
    try:
        # Check if profile already exists
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == payload.user_id))
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(
                id=uuid4(),
                user_id=payload.user_id,
                height_cm=payload.height_cm,
                body_archetype=payload.body_archetype,
                fit_preference=payload.fit_preference,
                style_persona=payload.style_persona,
                avoided_colors=payload.avoided_colors,
                favorite_styles=payload.favorite_styles
            )
            db.add(profile)
        else:
            if payload.height_cm is not None:
                profile.height_cm = payload.height_cm
            if payload.body_archetype is not None:
                profile.body_archetype = payload.body_archetype
            if payload.fit_preference is not None:
                profile.fit_preference = payload.fit_preference
            if payload.style_persona is not None:
                profile.style_persona = payload.style_persona
            if payload.avoided_colors is not None:
                profile.avoided_colors = payload.avoided_colors
            if payload.favorite_styles is not None:
                profile.favorite_styles = payload.favorite_styles
                
        await db.commit()
        await db.refresh(profile)
        return profile
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup user profile: {str(e)}"
        )

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_user_feedback(
    payload: UserFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Logs user feedback interaction (likes, saves, dismissals) for recommendations learning.
    """
    try:
        feedback = UserFeedback(
            id=uuid4(),
            user_id=payload.user_id,
            outfit_item_ids=[str(iid) for iid in payload.outfit_item_ids],
            feedback_type=payload.feedback_type
        )
        db.add(feedback)
        await db.commit()
        return {"message": "Feedback submitted successfully."}
    except Exception as e:
        logger.error(f"Error logging feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log feedback: {str(e)}"
        )


@router.post("/outfit-preview", status_code=status.HTTP_200_OK)
async def generate_outfit_preview(
    payload: OutfitPreviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Composes a vertically stacked outfit preview PNG image from a list of
    clothing item IDs. Returns the raw image as a PNG response.
    """
    try:
        # Fetch all requested garments from DB
        outfit_items = []
        for item_id in payload.clothing_item_ids:
            res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
            item = res.scalar_one_or_none()
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Clothing item '{item_id}' not found in wardrobe."
                )
            outfit_items.append({
                "id": item.id,
                "category": item.category,
                "processed_image_path": item.processed_image_path,
            })

        # Build the preview image bytes
        preview_bytes = OutfitPreviewBuilder.build_preview(
            outfit_items=outfit_items,
            score=payload.score,
            occasion=payload.occasion,
            season=payload.season,
            reasoning=payload.reasoning,
        )

        return Response(
            content=preview_bytes,
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=outfit_preview.png"}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Outfit preview generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )


@router.get("/preview-image/{filename}", status_code=status.HTTP_200_OK)
async def serve_preview_image(filename: str):
    """
    Serves a previously generated outfit preview PNG image by filename.
    Used by the frontend to load preview_url returned by /generate-outfits.
    """
    file_path = settings.PREVIEWS_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preview image '{filename}' not found."
        )
    return FileResponse(str(file_path), media_type="image/png")
