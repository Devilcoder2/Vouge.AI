import logging
import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID, uuid4
from typing import List
from datetime import datetime, timezone


from app.config import settings
from app.database.session import get_db
from app.database.models import ClothingItem, SavedOutfit, SavedOutfitItem, UserProfile, UserFeedback, GeneratedOutfit, GeneratedOutfitItem
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
from app.schemas.dashboard import EditorialLookResponse, RunwayTrendResponse, WeatherContext
from app.services.tryon_service import VTONService
from pydantic import BaseModel


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
    # 0. Check cache if not force regenerating
    if not payload.force_regenerate:
        try:
            result_cached = await db.execute(
                select(GeneratedOutfit)
                .where(
                    GeneratedOutfit.user_id == payload.user_id,
                    GeneratedOutfit.occasion == payload.occasion,
                    GeneratedOutfit.season == payload.season
                )
                .order_by(GeneratedOutfit.created_at.desc())
            )
            cached_outfits = result_cached.scalars().all()
            if cached_outfits:
                logger.info(f"Returning {len(cached_outfits)} cached outfit recommendations for user {payload.user_id} ({payload.occasion}, {payload.season})")
                response_outfits = []
                for outfit in cached_outfits:
                    res_items = []
                    for link in outfit.items:
                        gi = link.clothing_item
                        if gi:
                            res_items.append(
                                RecommendationItemResponse(
                                    id=gi.id,
                                    category=gi.category,
                                    subcategory=gi.subcategory or "",
                                    primary_color=gi.primary_color,
                                    primary_color_hex=gi.primary_color_hex or "#ffffff",
                                    fit=gi.fit,
                                    style=gi.style,
                                    formality=gi.formality,
                                    pattern=gi.pattern
                                )
                            )
                    
                    bk = outfit.breakdown or {}
                    response_outfits.append(
                        SingleOutfitResponse(
                            score=outfit.score,
                            items=res_items,
                            reasoning=outfit.reasoning or "A curated styling selection.",
                            template_name=outfit.template_name or "Custom Template",
                            breakdown=OutfitScoreBreakdown(
                                color_score=bk.get("color_score", 90),
                                style_score=bk.get("style_score", 90),
                                occasion_score=bk.get("occasion_score", 90),
                                formality_score=bk.get("formality_score", 90),
                                season_score=bk.get("season_score", 90)
                            ),
                            why_selected=outfit.why_selected or [],
                            preview_url=outfit.preview_url,
                        )
                    )
                
                # Evaluate diversity using list-of-dicts representation
                outfits_dict_repr = [
                    {
                        "score": o.score,
                        "items": [
                            {"id": it.id, "category": it.category}
                            for it in o.items
                        ]
                    }
                    for o in response_outfits
                ]
                diversity_eval = QualityEvaluator.evaluate_recommendations_diversity(outfits_dict_repr)
                return GenerateOutfitsResponse(outfits=response_outfits, diversity_eval=diversity_eval)
        except Exception as cache_err:
            logger.warning(f"Error querying recommendation cache: {cache_err}")

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
                    gender=db_profile.gender if (db_profile and db_profile.gender) else "male"
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

        # Cache the newly generated outfits for future calls
        try:
            # A. Delete stale cache for this user + occasion + season
            await db.execute(
                delete(GeneratedOutfit)
                .where(
                    GeneratedOutfit.user_id == payload.user_id,
                    GeneratedOutfit.occasion == payload.occasion,
                    GeneratedOutfit.season == payload.season
                )
            )
            # B. Save new outfits to cache database tables
            for outfit in response_outfits:
                db_gen_outfit = GeneratedOutfit(
                    id=uuid4(),
                    user_id=payload.user_id,
                    occasion=payload.occasion,
                    season=payload.season,
                    score=outfit.score,
                    template_name=outfit.template_name,
                    reasoning=outfit.reasoning,
                    why_selected=outfit.why_selected,
                    preview_url=outfit.preview_url,
                    breakdown={
                        "color_score": outfit.breakdown.color_score,
                        "style_score": outfit.breakdown.style_score,
                        "occasion_score": outfit.breakdown.occasion_score,
                        "formality_score": outfit.breakdown.formality_score,
                        "season_score": outfit.breakdown.season_score
                    }
                )
                db.add(db_gen_outfit)
                
                # Link garments to generated outfit items
                for it in outfit.items:
                    link = GeneratedOutfitItem(
                        id=uuid4(),
                        outfit_id=db_gen_outfit.id,
                        clothing_item_id=it.id
                    )
                    db.add(link)
            await db.commit()
            logger.info(f"Successfully cached {len(response_outfits)} generated outfit recommendations for user {payload.user_id}")
        except Exception as cache_save_err:
            logger.error(f"Failed to cache generated outfits: {cache_save_err}")

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
        user_id = "default_user"
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
            if hasattr(item, "user_id") and item.user_id:
                user_id = item.user_id

        # Query user profile to load active gender preference
        gender = "male"
        try:
            profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
            db_profile = profile_res.scalar_one_or_none()
            if db_profile and db_profile.gender:
                gender = db_profile.gender
        except Exception as e:
            logger.warning(f"Failed to query user profile in generate_outfit_preview: {e}")

        # Build the preview image bytes
        preview_bytes = OutfitPreviewBuilder.build_preview(
            outfit_items=outfit_items,
            score=payload.score,
            occasion=payload.occasion,
            season=payload.season,
            reasoning=payload.reasoning,
            gender=gender,
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


class TryOnRequest(BaseModel):
    item_id: str
    gender: str = "male"

@router.post("/tryon", status_code=status.HTTP_200_OK)
async def tryon_item(
    payload: TryOnRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers the SOTA Virtual Try-On pipeline (VTONService) for a single custom item.
    """
    try:
        # Resolve item UUID or default ID from database
        try:
            from uuid import UUID
            item_uuid = UUID(payload.item_id)
            res = await db.execute(select(ClothingItem).where(ClothingItem.id == item_uuid))
        except (ValueError, TypeError):
            res = await db.execute(select(ClothingItem).where(ClothingItem.id == payload.item_id))
            
        item = res.scalar_one_or_none()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Clothing item '{payload.item_id}' not found in active database."
            )

        # Resolve image path robustly
        path_str = item.processed_image_path or item.original_image_path
        if not path_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clothing item does not have a valid processed image path."
            )
            
        if not os.path.isabs(path_str):
            full_path = settings.BASE_DIR / path_str
            if not full_path.exists():
                full_path = settings.BASE_DIR.parent / path_str
            path_str = str(full_path)

        # Call the SOTA VTONService pipeline
        synthesized_url = await VTONService.generate_tryon(
            garment_image_path=path_str,
            category=item.category,
            gender=payload.gender,
            item_name=item.name
        )

        return {"tryon_url": synthesized_url}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Try-On pipeline execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Try-On pipeline failed: {str(e)}"
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


@router.get("/editorial-look", response_model=EditorialLookResponse, status_code=status.HTTP_200_OK)
async def get_editorial_look(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches the Daily Curated Editorial Look for the Hero spotlight panel.
    Tailored to local weather (overcast 12C London) and user style profile.
    """
    try:
        # Check if there is any cached GeneratedOutfit first!
        res_cache = await db.execute(
            select(GeneratedOutfit)
            .where(GeneratedOutfit.user_id == user_id)
            .order_by(GeneratedOutfit.created_at.desc())
        )
        cached = res_cache.scalars().all()
        if cached:
            for top_cached in cached:
                # Validate the preview image file physically exists if preview_url is provided
                if top_cached.preview_url:
                    filename = None
                    if "/preview-image/" in top_cached.preview_url:
                        filename = top_cached.preview_url.split("/preview-image/")[-1]
                    elif "/previews/" in top_cached.preview_url:
                        filename = top_cached.preview_url.split("/previews/")[-1]
                    
                    if filename:
                        file_path = settings.PREVIEWS_DIR / filename
                        if not file_path.exists():
                            logger.warning(
                                f"Stale outfit cache entry {top_cached.id} detected for user {user_id}. "
                                f"Backing file '{filename}' is missing from filesystem. Clearing stale record."
                            )
                            try:
                                if hasattr(db, "delete"):
                                    await db.delete(top_cached)
                                    await db.commit()
                            except Exception as delete_err:
                                logger.error(f"Failed to delete stale cache outfit {top_cached.id}: {delete_err}")
                            continue

                item_ids = [str(link.clothing_item_id) for link in top_cached.items if link.clothing_item_id]
                if len(item_ids) >= 2:
                    return EditorialLookResponse(
                        outfit_id=str(top_cached.id),
                        editorial_title=f"The Editorial Edit: {top_cached.template_name or 'Modern Noir'}",
                        subtitle="Architectural Minimalism",
                        description=top_cached.reasoning or "A cinematic approach to your Monday. Tailored elegantly for London weather.",
                        hero_image_url=top_cached.preview_url or "/assets/modern_noir_hero.png",
                        vogue_score=top_cached.score,
                        occasion=top_cached.occasion.upper(),
                        weather_context=WeatherContext(
                            location="London",
                            temperature_celsius=12.0,
                            condition="Overcast"
                        ),
                        clothing_item_ids=item_ids
                    )
    except Exception as cache_err:
        logger.warning(f"Error fetching cached outfit for editorial look: {cache_err}")

    # Fallback classic look matching specs exactly
    return EditorialLookResponse(
        outfit_id="modern-minimalist",
        editorial_title="The Editorial Edit: Modern Noir",
        subtitle="Architectural Minimalism",
        description="A cinematic approach to your Monday. Your charcoal wool trench meets a crisp ivory knit for an aesthetic that commands the room.",
        hero_image_url="/assets/modern_noir_hero.png",
        vogue_score=94,
        occasion="COCKTAIL PARTY",
        weather_context=WeatherContext(
            location="London",
            temperature_celsius=12.0,
            condition="Overcast"
        ),
        clothing_item_ids=["trench", "knit", "trouser", "boots"]
    )


@router.get("/trends", response_model=List[RunwayTrendResponse], status_code=status.HTTP_200_OK)
async def get_runway_trends(
    style_persona: str = "minimalist",
    limit: int = Query(3, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns runway fashion trends parsed from runway feeds matching user style persona.
    """
    all_trends = [
        RunwayTrendResponse(
            trend_id="monochromatic-discipline",
            title="The Monochromatic Discipline",
            source="Paris Fashion Week",
            category="Trending",
            image_url="/assets/monochrome_trend.png",
            description="Elevating basics through strict color discipline. A global shift towards high-contrast minimalism is emerging."
        ),
        RunwayTrendResponse(
            trend_id="quiet-luxury-layering",
            title="Quiet Luxury Cashmere Layering",
            source="Milan Fashion Week",
            category="Editorial",
            image_url="/assets/quiet_luxury_trend.png",
            description="Structured earth tones paired with unbranded knitwear layers. A strong pivot towards textured silence."
        ),
        RunwayTrendResponse(
            trend_id="heritage-outerwear",
            title="Heritage Trench Resurgence",
            source="London Fashion Week",
            category="Runway",
            image_url="/assets/heritage_trend.png",
            description="Draped oversized double-breasted silhouettes paired with high-formality chelsea boots."
        ),
        RunwayTrendResponse(
            trend_id="streetwear-utility",
            title="Tactical Techwear Utility Gorpcore",
            source="Tokyo Fashion Week",
            category="Trending",
            image_url="/assets/utility_trend.png",
            description="Multi-pocket oversized tactical cargos and reflective lightweight windproof layers."
        )
    ]
    
    # Filter based on style persona if applicable
    p_clean = style_persona.lower()
    filtered = []
    for trend in all_trends:
        desc = trend.description.lower()
        title = trend.title.lower()
        if (
            p_clean in desc or 
            p_clean in title or 
            (p_clean == "minimalist" and ("monochrome" in desc or "minimal" in desc or "minimalism" in desc or "monochromatic" in desc or "monochrome" in title)) or
            (p_clean == "streetwear" and ("streetwear" in desc or "streetwear" in title or "utility" in desc or "utility" in title or "gorpcore" in desc or "gorpcore" in title))
        ):
            filtered.append(trend)

            
    # Fallback if no matching persona filters
    if not filtered:
        filtered = all_trends
        
    return filtered[:limit]


