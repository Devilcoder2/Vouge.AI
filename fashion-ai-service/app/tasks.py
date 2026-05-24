"""
Asynchronous Background Tasks for Vouge.AI.
Runs AI pipelines, recommendation scoring, and analytics inside Celery workers using asyncio wrappers.
"""
import logging
import asyncio
from uuid import UUID
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

from app.celery_app import celery_app
from app.config import settings
from app.database.session import AsyncSessionLocal
from app.database.models import (
    BackgroundJob,
    ClothingItem,
    User,
    SavedOutfit,
    UserProfile,
    UserFeedback,
)
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Import AI Pipeline components
from app.utils.file_handler import FileHandler
from app.ai.background_removal import BackgroundRemover
from app.ai.preprocessing import ImagePreprocessor
from app.ai.classifier import FashionClassifier
from app.ai.color_extractor import ColorExtractor
from app.ai.embedding_service import FashionEmbeddingService
from app.services.duplicate_detector import DuplicateDetector

# Import Recommendation components
from app.recommendation.generators.candidate_generator import CandidateGenerator
from app.recommendation.scorers.outfit_scorer import OutfitScorer
from app.recommendation.scorers.ranker import RecommendationRanker
from app.recommendation.explainers.outfit_explainer import OutfitExplainer
from app.recommendation.evaluators.quality_evaluator import QualityEvaluator
from app.recommendation.engines.body_engine import BodyTypeEngine
from app.recommendation.engines.persona_engine import StylePersonaEngine
from app.recommendation.engines.feedback_engine import FeedbackEngine
from app.recommendation.engines.embedding_similarity_engine import EmbeddingSimilarityEngine
from app.recommendation.engines.silhouette_engine import SilhouetteEngine
from app.recommendation.engines.gap_analysis import GapAnalysisEngine
from app.services.personalization_engine import PersonalizationEngine
from app.services.outfit_preview_builder import OutfitPreviewBuilder

logger = logging.getLogger("fashion-ai-service")


# ── Event Loop Broker ─────────────────────────────────────────────────────────

def run_async_task(coro):
    """
    Helper to run an async coroutine safely.
    If an event loop is already running in this thread (or globally), submits
    the coroutine to run on the active loop, blocking the calling thread until done.
    Otherwise, starts a completely fresh event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Submit task to main running loop and await output synchronously in threadpool thread
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        # Standard Celery worker thread has no loop, safe to create a new one
        return asyncio.run(coro)


# ── Helper Telemetry Operations ───────────────────────────────────────────────

async def is_job_cancelled(db: AsyncSessionLocal, job_uuid: UUID) -> bool:
    """Checks if the user has cancelled this background job."""
    result = await db.execute(select(BackgroundJob).where(BackgroundJob.id == job_uuid))
    job = result.scalar_one_or_none()
    return job is not None and job.status == "cancelled"

async def update_job_status(
    db: AsyncSessionLocal,
    job_uuid: UUID,
    status: str = None,
    progress: int = None,
    error_message: str = None,
    result_reference: Any = None,
):
    """Updates progress, status, and result reference inside PostgreSQL background_jobs table."""
    result = await db.execute(select(BackgroundJob).where(BackgroundJob.id == job_uuid))
    job = result.scalar_one_or_none()
    if job:
        if status:
            job.status = status
        if progress is not None:
            job.progress = progress
        if error_message is not None:
            job.error_message = error_message
        if result_reference is not None:
            job.result_reference = result_reference
        if status in ["completed", "failed", "cancelled"]:
            job.completed_at = datetime.now(timezone.utc)
        db.add(job)
        await db.commit()


# ── Task 1: Clothing Processing Job ──────────────────────────────────────────

async def run_async_clothing_processing(job_uuid: UUID, raw_image_path: str, user_id: UUID):
    async with AsyncSessionLocal() as db:
        raw_filepath = Path(raw_image_path)
        processed_filepath = None
        embedding_filepath = None

        try:
            # 1. Start Job
            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, status="processing", progress=10)
            logger.info(f"[Job {job_uuid}] Running background removal...")

            # 2. Background Removal
            with open(raw_filepath, "rb") as f:
                raw_bytes = f.read()
            transparent_img = BackgroundRemover.remove_background(raw_bytes)

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=30)
            logger.info(f"[Job {job_uuid}] Preprocessing image...")

            # 3. Image Preprocessing
            processed_img = ImagePreprocessor.preprocess_image(transparent_img, target_size=512)
            processed_filename = f"{raw_filepath.stem}_processed.png"
            processed_filepath = settings.PROCESSED_DIR / processed_filename
            processed_img.save(processed_filepath, format="PNG")

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=50)
            logger.info(f"[Job {job_uuid}] Running Gemini classifier...")

            # 4. Gemini Classification
            classifier = FashionClassifier()
            extracted_metadata = classifier.classify_garment(processed_img, filename_hint=raw_filepath.name)

            if extracted_metadata.detected_items_count > 1:
                raise ValueError(f"Detected {extracted_metadata.detected_items_count} clothing items. Please upload one item only.")

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=70)
            logger.info(f"[Job {job_uuid}] Extracting colors & generating embeddings...")

            # 5. Color Extraction
            primary_color, secondary_colors, primary_hex, secondary_hexes = ColorExtractor.extract_colors(processed_img)

            # 6. Embedding Generation
            embedding_service = FashionEmbeddingService()
            embedding = embedding_service.generate_image_embedding(processed_img)
            embedding_filepath = FashionEmbeddingService.save_embedding_to_disk(embedding, raw_filepath.stem)

            # 7. Duplicate Check
            perceptual_hash = DuplicateDetector.calculate_dhash(processed_img)
            result = await db.execute(select(ClothingItem))
            existing_items = result.scalars().all()
            is_duplicate, duplicate_of_id = DuplicateDetector.check_duplicates(
                processed_img,
                embedding,
                existing_items
            )

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=90)
            logger.info(f"[Job {job_uuid}] Persisting clothing item to database...")

            # 8. Save Item
            db_item = ClothingItem(
                original_image_path=str(raw_filepath),
                processed_image_path=str(processed_filepath),
                category=extracted_metadata.category.value,
                confidence_category=extracted_metadata.category.confidence,
                subcategory=extracted_metadata.subcategory.value,
                confidence_subcategory=extracted_metadata.subcategory.confidence,
                primary_color=extracted_metadata.primary_color,
                primary_color_hex=primary_hex,
                secondary_colors=extracted_metadata.secondary_colors,
                secondary_colors_hex=secondary_hexes,
                fit=extracted_metadata.fit.value,
                confidence_fit=extracted_metadata.fit.confidence,
                style=extracted_metadata.style.value,
                confidence_style=extracted_metadata.style.confidence,
                formality=extracted_metadata.formality,
                seasons=extracted_metadata.seasons,
                pattern=extracted_metadata.pattern.value,
                confidence_pattern=extracted_metadata.pattern.confidence,
                prompt_version=classifier.PROMPT_VERSION,
                detected_items_count=extracted_metadata.detected_items_count,
                is_duplicate=is_duplicate,
                duplicate_of_id=duplicate_of_id,
                perceptual_hash=perceptual_hash,
                embedding_path=str(embedding_filepath)
            )
            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)

            # 9. Finalize Job
            logger.info(f"[Job {job_uuid}] Job successfully completed.")
            await update_job_status(
                db,
                job_uuid,
                status="completed",
                progress=100,
                result_reference={"item_id": str(db_item.id), "category": db_item.category}
            )

        except Exception as err:
            logger.error(f"[Job {job_uuid}] Processing failed: {str(err)}", exc_info=True)
            # Cleanup intermediate writes
            if raw_filepath:
                FileHandler.delete_file(raw_filepath)
            if processed_filepath:
                FileHandler.delete_file(processed_filepath)
            if embedding_filepath:
                FileHandler.delete_file(embedding_filepath)

            await update_job_status(db, job_uuid, status="failed", progress=100, error_message=str(err))
            raise err

@celery_app.task(bind=True, max_retries=3)
def clothing_processing_job(self, job_id: str, raw_image_path: str, user_id: str):
    """Celery task running async clothing processing pipeline."""
    try:
        run_async_task(run_async_clothing_processing(UUID(job_id), raw_image_path, UUID(user_id)))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ── Task 2: Outfit Generation Job ────────────────────────────────────────────

async def run_async_outfit_generation(job_uuid: UUID, user_id: UUID, occasion: str, season: str):
    async with AsyncSessionLocal() as db:
        try:
            # 1. Start Job
            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, status="processing", progress=10)
            logger.info(f"[Job {job_uuid}] Fetching user wardrobe items...")

            # 2. Fetch closet items
            result = await db.execute(select(ClothingItem))
            db_items = result.scalars().all()
            
            if not db_items:
                await update_job_status(
                    db,
                    job_uuid,
                    status="completed",
                    progress=100,
                    result_reference={"outfits": [], "verdict": "Closet empty"}
                )
                return

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=30)
            logger.info(f"[Job {job_uuid}] Generating matches & scoring candidates...")

            # 3. Generate matches & base scoring
            candidates = CandidateGenerator.generate_candidates(db_items, occasion, season)
            if not candidates:
                await update_job_status(
                    db,
                    job_uuid,
                    status="completed",
                    progress=100,
                    result_reference={"outfits": [], "verdict": "No compatible candidates"}
                )
                return

            # Retrieve user profile & feedback lists
            try:
                profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == str(user_id)))
                db_profile = profile_res.scalar_one_or_none()
            except Exception:
                db_profile = None

            profile_dict = {
                "height_cm": db_profile.height_cm if db_profile else None,
                "body_archetype": db_profile.body_archetype if db_profile else "rectangle",
                "fit_preference": db_profile.fit_preference if db_profile else "standard",
                "style_persona": db_profile.style_persona if db_profile else "minimalist",
                "avoided_colors": db_profile.avoided_colors if db_profile else [],
                "favorite_styles": db_profile.favorite_styles if db_profile else []
            }

            try:
                fb_res = await db.execute(select(UserFeedback).where(UserFeedback.user_id == str(user_id)))
                db_feedbacks = fb_res.scalars().all()
            except Exception:
                db_feedbacks = []
                
            feedback_list = [
                {"feedback_type": fb.feedback_type, "outfit_item_ids": fb.outfit_item_ids}
                for fb in db_feedbacks if hasattr(fb, "feedback_type")
            ]

            scored_candidates = []
            for cand in candidates:
                score_res = OutfitScorer.score_outfit(cand["items"], occasion, season)
                base_score_01 = score_res["total_score"] / 100.0

                harmony_res = EmbeddingSimilarityEngine.calculate_visual_harmony(cand["items"])
                harmony_score = harmony_res["score"]
                outfit_embedding = harmony_res["outfit_embedding"]

                body_res = BodyTypeEngine.calculate_body_compatibility(cand["items"], profile_dict)
                body_score = body_res["score"]

                persona_res = StylePersonaEngine.calculate_persona_compatibility(cand["items"], profile_dict["style_persona"])
                persona_score = persona_res["score"]

                feedback_res = FeedbackEngine.calculate_feedback_adjustments(cand["items"], profile_dict, feedback_list)
                feedback_adj = feedback_res["adjustment_factor"]

                silhouette_res = SilhouetteEngine.calculate_silhouette_balance(cand["items"], occasion, profile_dict["style_persona"])
                silhouette_score = silhouette_res["score"]

                combined_why = []
                combined_why.extend(body_res["why_selected"])
                combined_why.extend(persona_res["why_selected"])
                combined_why.extend(feedback_res["why_selected"])
                combined_why.extend(silhouette_res["why_selected"])

                if not combined_why:
                    combined_why.append("Balanced neutral aesthetic silhouette compatibility.")

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

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=60)
            logger.info(f"[Job {job_uuid}] Running personalization boosts & rankings...")

            # 4. Apply real-time personalization boosts/penalties
            scored_candidates = await PersonalizationEngine.apply_recommendation_boosts(
                scored_candidates, user_id, db
            )

            # 5. Diversify and rank
            top_candidates = RecommendationRanker.diversify_and_rank(scored_candidates, max_outputs=10)

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=80)
            logger.info(f"[Job {job_uuid}] Curating stylist explanations via Gemini...")

            # 6. Gemini explanations
            explainer = OutfitExplainer()
            final_outfits = explainer.explain_recommendations(top_candidates, occasion, season)

            # Quality Assessment
            diversity_eval = QualityEvaluator.evaluate_recommendations_diversity(final_outfits)

            # Format Response outfits
            response_outfits = []
            for outfit in final_outfits:
                res_items = [{
                    "id": str(it["id"]),
                    "category": it["category"],
                    "subcategory": it.get("subcategory", ""),
                    "primary_color": it["primary_color"],
                    "primary_color_hex": it["primary_color_hex"],
                    "fit": it["fit"],
                    "style": it["style"],
                    "formality": it["formality"],
                    "pattern": it["pattern"]
                } for it in outfit["items"]]

                # Previews (skip actual write to folder for generated outfits, or build preview bytes and skip)
                response_outfits.append({
                    "score": outfit["score"],
                    "items": res_items,
                    "reasoning": outfit["reasoning"],
                    "template_name": outfit["template_name"],
                    "why_selected": outfit.get("why_selected", []),
                    "breakdown": {
                        "color_score": outfit["breakdown"]["color_score"],
                        "style_score": outfit["breakdown"]["style_score"],
                        "occasion_score": outfit["breakdown"]["occasion_score"],
                        "formality_score": outfit["breakdown"]["formality_score"],
                        "season_score": outfit["breakdown"]["season_score"]
                    }
                })

            # 7. Finalize Job
            logger.info(f"[Job {job_uuid}] Job successfully completed.")
            await update_job_status(
                db,
                job_uuid,
                status="completed",
                progress=100,
                result_reference={
                    "outfits": response_outfits,
                    "diversity_eval": {
                        "diversity_index": diversity_eval.get("diversity_index", 0.0),
                        "average_score": diversity_eval.get("average_score", 0.0),
                        "unique_items_ratio": diversity_eval.get("unique_items_ratio", 0.0),
                        "verdict": diversity_eval.get("verdict", "")
                    }
                }
            )

        except Exception as err:
            logger.error(f"[Job {job_uuid}] Outfit generation failed: {str(err)}", exc_info=True)
            await update_job_status(db, job_uuid, status="failed", progress=100, error_message=str(err))
            raise err

@celery_app.task(bind=True, max_retries=3)
def outfit_generation_job(self, job_id: str, user_id: str, occasion: str, season: str):
    """Celery task running async outfit generation and ranking."""
    try:
        run_async_task(run_async_outfit_generation(UUID(job_id), UUID(user_id), occasion, season))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ── Task 3: Gap Analysis Job ─────────────────────────────────────────────────

async def run_async_gap_analysis(job_uuid: UUID, user_id: UUID):
    async with AsyncSessionLocal() as db:
        try:
            # 1. Start Job
            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, status="processing", progress=20)
            logger.info(f"[Job {job_uuid}] Loading closet items...")

            # 2. Fetch clothes
            result = await db.execute(select(ClothingItem))
            db_items = result.scalars().all()

            if await is_job_cancelled(db, job_uuid):
                await update_job_status(db, job_uuid, status="cancelled")
                return

            await update_job_status(db, job_uuid, progress=60)
            logger.info(f"[Job {job_uuid}] Running Gap analysis calculations...")

            # 3. Run Gap analysis
            gaps = GapAnalysisEngine.analyze_gaps(db_items)

            # Format Response
            response_gaps = []
            for g in gaps:
                unlocked_items = [{
                    "occasion": ui.get("occasion", ""),
                    "season": ui.get("season", ""),
                    "avg_score": ui.get("avg_score", 0),
                    "reasoning": ui.get("reasoning", "")
                } for ui in g.get("unlocked_outfits_sample", [])]

                response_gaps.append({
                    "missing_item": {
                        "category": g["missing_item"]["category"],
                        "subcategory": g["missing_item"].get("subcategory", ""),
                        "primary_color": g["missing_item"]["primary_color"],
                        "style": g["missing_item"]["style"],
                        "formality": g["missing_item"]["formality"]
                    },
                    "outfits_unlocked_count": g["outfits_unlocked_count"],
                    "unlocked_outfits_sample": unlocked_items
                })

            # 4. Finalize Job
            logger.info(f"[Job {job_uuid}] Job successfully completed.")
            await update_job_status(
                db,
                job_uuid,
                status="completed",
                progress=100,
                result_reference={"gaps": response_gaps}
            )

        except Exception as err:
            logger.error(f"[Job {job_uuid}] Gap analysis failed: {str(err)}", exc_info=True)
            await update_job_status(db, job_uuid, status="failed", progress=100, error_message=str(err))
            raise err

@celery_app.task(bind=True, max_retries=3)
def gap_analysis_job(self, job_id: str, user_id: str):
    """Celery task running async wardrobe gap analysis."""
    try:
        run_async_task(run_async_gap_analysis(UUID(job_id), UUID(user_id)))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ── Task 4: Dead Job Recovery (Reaper) ────────────────────────────────────────

async def run_async_dead_job_recovery():
    """Finds stuck queued/processing jobs older than 1 hour and marks them failed."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(hours=1)

        result = await db.execute(
            select(BackgroundJob)
            .where(BackgroundJob.status.in_(["queued", "processing"]))
            .where(BackgroundJob.created_at <= threshold)
        )
        stuck_jobs = result.scalars().all()

        if stuck_jobs:
            logger.warning(f"Reaper: Recovering {len(stuck_jobs)} dead background jobs.")
            for job in stuck_jobs:
                job.status = "failed"
                job.completed_at = now
                job.error_message = "Job timed out or worker process terminated unexpectedly."
                db.add(job)
            await db.commit()

@celery_app.task
def dead_job_recovery_job():
    """Celery task periodically reclaiming hung background jobs."""
    run_async_task(run_async_dead_job_recovery())
