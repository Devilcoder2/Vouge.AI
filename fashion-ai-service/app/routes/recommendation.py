import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID, uuid4
from typing import List
from datetime import datetime, timezone

from app.database.session import get_db
from app.database.models import ClothingItem, SavedOutfit, SavedOutfitItem
from app.schemas.recommendation import (
    GenerateOutfitsRequest,
    GenerateOutfitsResponse,
    SingleOutfitResponse,
    RecommendationItemResponse,
    OutfitScoreBreakdown,
    SaveOutfitRequest,
    SavedOutfitResponse,
    GapAnalysisResponse,
    VersatilityResponse
)
from app.recommendation.generators.candidate_generator import CandidateGenerator
from app.recommendation.scorers.outfit_scorer import OutfitScorer
from app.recommendation.scorers.ranker import RecommendationRanker
from app.recommendation.explainers.outfit_explainer import OutfitExplainer
from app.recommendation.evaluators.quality_evaluator import QualityEvaluator
from app.recommendation.engines.gap_analysis import GapAnalysisEngine
from app.recommendation.engines.versatility_engine import VersatilityEngine

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
            
        # 3. Apply high-fidelity ensemble scoring
        scored_candidates = []
        for cand in candidates:
            score_res = OutfitScorer.score_outfit(
                cand["items"], payload.occasion, payload.season
            )
            scored_candidates.append({
                "items": cand["items"],
                "template_name": cand["template_name"],
                "total_score": score_res["total_score"],
                "breakdown": score_res["breakdown"],
                "reasons": score_res["reasons"]
            })
            
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
                    )
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
            reasoning=payload.reasoning
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

@router.get("/saved-outfits", response_model=List[SavedOutfitResponse], status_code=status.HTTP_200_OK)
async def get_saved_outfits(
    user_id: str = "default_user",
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all previously saved outfit combinations.
    """
    try:
        result = await db.execute(
            select(SavedOutfit)
            .where(SavedOutfit.user_id == user_id)
            .order_by(SavedOutfit.created_at.desc())
        )
        outfits = result.scalars().all()
        
        response = []
        for outfit in outfits:
            res_items = []
            for link in outfit.items:
                gi = link.clothing_item
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
                    created_at=outfit.created_at or datetime.now(timezone.utc),
                    items=res_items
                )
            )
        return response
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

@router.get("/gap-analysis", response_model=List[GapAnalysisResponse], status_code=status.HTTP_200_OK)
async def get_gap_analysis(
    db: AsyncSession = Depends(get_db)
):
    """
    Step 15 Engine: Analyzes missing essential elements in user wardrobe
    and calculates new outfit combinations they would unlock.
    """
    try:
        result = await db.execute(select(ClothingItem))
        db_items = result.scalars().all()
        return GapAnalysisEngine.analyze_gaps(db_items)
    except Exception as e:
        logger.error(f"Gap analysis route failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap analysis failed: {str(e)}"
        )

@router.get("/versatility", response_model=List[VersatilityResponse], status_code=status.HTTP_200_OK)
async def get_versatility_report(
    db: AsyncSession = Depends(get_db)
):
    """
    Step 16 Engine: Ranks all closet garments by versatility and outfit reuse counts.
    """
    try:
        result = await db.execute(select(ClothingItem))
        db_items = result.scalars().all()
        return VersatilityEngine.calculate_versatility(db_items)
    except Exception as e:
        logger.error(f"Versatility report route failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Versatility analysis failed: {str(e)}"
        )
