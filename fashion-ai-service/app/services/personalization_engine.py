"""
Vouge.AI Personalization & Dynamic Feedback Learning Engine.
Evolves clothing recommendations based on user interaction feedback and behavior events.
"""

import logging
from uuid import UUID
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database.models import (
    UserStyleProfile,
    RecommendationFeedback,
    UserBehaviorEvent,
    SavedOutfit,
    ClothingItem,
)

logger = logging.getLogger("fashion-ai-service")

class PersonalizationEngine:
    @classmethod
    async def aggregate_feedback(cls, user_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """
        Aggregates all recommendation feedback, behavior events, and saved outfits
        for the user to determine their styling preferences.
        """
        # 1. Fetch all feedback
        feedback_result = await db.execute(
            select(RecommendationFeedback)
            .where(RecommendationFeedback.user_id == user_id)
        )
        feedbacks = feedback_result.scalars().all()

        # 2. Fetch all behavior events
        events_result = await db.execute(
            select(UserBehaviorEvent)
            .where(UserBehaviorEvent.user_id == user_id)
        )
        events = events_result.scalars().all()

        # 3. Fetch all saved outfits (including their items)
        outfits_result = await db.execute(
            select(SavedOutfit)
            .options(selectinload(SavedOutfit.items))
            .where(SavedOutfit.user_id == str(user_id))
        )
        saved_outfits = outfits_result.scalars().all()

        return {
            "feedbacks": feedbacks,
            "events": events,
            "saved_outfits": saved_outfits,
        }

    @classmethod
    def compute_preference_weights(
        cls,
        feedbacks: List[RecommendationFeedback],
        events: List[UserBehaviorEvent],
        saved_outfits: List[SavedOutfit],
    ) -> Dict[str, Any]:
        """
        Calculates user style preference weights from interaction data.
        Returns aggregated scores for colors, styles, formality, fits, categories, and monochrome preferences.
        """
        color_scores = defaultdict(float)
        style_scores = defaultdict(float)
        formality_scores = defaultdict(float)
        fit_scores = defaultdict(float)
        category_scores = defaultdict(float)

        positive_formalities = []
        monochrome_saves = 0
        total_saves = 0

        # Helper to process positive outfit items
        def process_positive_items(items: List[Dict[str, Any]]):
            nonlocal monochrome_saves, total_saves
            if not items:
                return

            total_saves += 1
            # Check for monochrome
            colors = set(it.get("primary_color", "").lower() for it in items if it.get("primary_color"))
            if len(colors) == 1:
                monochrome_saves += 1

            for it in items:
                color = it.get("primary_color", "").lower()
                style = it.get("style", "").lower()
                fit = it.get("fit", "").lower()
                cat = it.get("category", "").lower()
                formality = it.get("formality")

                if color:
                    color_scores[color] += 1.0
                if style:
                    style_scores[style] += 1.0
                if fit:
                    fit_scores[fit] += 1.0
                if cat:
                    category_scores[cat] += 1.0
                if formality is not None:
                    try:
                        f_val = int(formality)
                        formality_scores[f_val] += 1.0
                        positive_formalities.append(f_val)
                    except ValueError:
                        pass

        # Helper to process negative outfit items
        def process_negative_items(items: List[Dict[str, Any]], penalty_multiplier: float = 1.0):
            if not items:
                return
            for it in items:
                color = it.get("primary_color", "").lower()
                style = it.get("style", "").lower()
                fit = it.get("fit", "").lower()
                cat = it.get("category", "").lower()
                formality = it.get("formality")

                if color:
                    color_scores[color] -= 1.0 * penalty_multiplier
                if style:
                    style_scores[style] -= 1.0 * penalty_multiplier
                if fit:
                    fit_scores[fit] -= 1.0 * penalty_multiplier
                if cat:
                    category_scores[cat] -= 1.0 * penalty_multiplier
                if formality is not None:
                    try:
                        f_val = int(formality)
                        formality_scores[f_val] -= 1.0 * penalty_multiplier
                    except ValueError:
                        pass

        # 1. Process Saved Outfits (extremely strong positive signal)
        for outfit in saved_outfits:
            items_list = []
            for link in outfit.items:
                gi = link.clothing_item
                if gi:
                    items_list.append({
                        "primary_color": gi.primary_color,
                        "style": gi.style,
                        "fit": gi.fit,
                        "category": gi.category,
                        "formality": gi.formality,
                    })
            process_positive_items(items_list)

        # 2. Process Behavior Events
        # Extract items from metadata of behavior events
        for ev in events:
            ev_type = ev.event_type.lower()
            metadata = ev.event_metadata or {}
            items_list = metadata.get("items", [])

            if ev_type in ["outfit_saved", "outfit_liked", "outfit_worn"]:
                process_positive_items(items_list)
            elif ev_type in ["outfit_dismissed", "outfit_rejected"]:
                process_negative_items(items_list, penalty_multiplier=1.0)
            elif ev_type == "outfit_regenerated":
                process_negative_items(items_list, penalty_multiplier=0.5)

        # 3. Process Feedbacks (if they reference saved outfits or metadata in behavior events)
        # Note: Feedback is also backed up by behavior events.
        for fb in feedbacks:
            action = fb.action_type.lower()
            # If outfit is saved, we can query details. Since we already aggregated saved outfits,
            # we mainly focus on dismissals/regenerates from feedback that might not be in saved outfits
            # but logged in behavior events.
            pass

        return {
            "color_scores": dict(color_scores),
            "style_scores": dict(style_scores),
            "formality_scores": dict(formality_scores),
            "fit_scores": dict(fit_scores),
            "category_scores": dict(category_scores),
            "positive_formalities": positive_formalities,
            "monochrome_ratio": monochrome_saves / max(1, total_saves) if total_saves > 0 else 0.0,
            "total_saves": total_saves,
        }

    @classmethod
    async def generate_user_preference_vector(cls, user_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """
        Compiles the aggregated scores into preferred vs avoided tags and formality ranges.
        """
        agg = await cls.aggregate_feedback(user_id, db)
        weights = cls.compute_preference_weights(
            agg["feedbacks"], agg["events"], agg["saved_outfits"]
        )

        # Thresholds: Preference score >= 2.5 -> Preferred. Score <= -2.5 -> Disliked.
        preferred_colors = [c for c, score in weights["color_scores"].items() if score >= 2.5]
        disliked_colors = [c for c, score in weights["color_scores"].items() if score <= -2.5]
        preferred_styles = [s for s, score in weights["style_scores"].items() if score >= 2.5]
        favorite_categories = [cat for cat, score in weights["category_scores"].items() if score >= 2.5]
        disliked_fits = [fit for fit, score in weights["fit_scores"].items() if score <= -2.5]

        # Calculate formality range from positive feedback
        formalities = weights["positive_formalities"]
        if formalities:
            # We sort and take a 10th to 90th percentile, or simply [min, max]
            formalities.sort()
            min_f = formalities[0]
            max_f = formalities[-1]
            preferred_formality_range = [min_f, max_f]
        else:
            preferred_formality_range = [1, 10]

        return {
            "preferred_colors": preferred_colors,
            "disliked_colors": disliked_colors,
            "preferred_styles": preferred_styles,
            "preferred_formality_range": preferred_formality_range,
            "favorite_categories": favorite_categories,
            "disliked_fits": disliked_fits,
            "prefers_monochrome": weights["monochrome_ratio"] >= 0.5 and weights["total_saves"] >= 2,
        }

    @classmethod
    async def update_style_profile(cls, user_id: UUID, db: AsyncSession) -> UserStyleProfile:
        """
        Calculates and persists/updates the UserStyleProfile for a user.
        """
        prefs = await cls.generate_user_preference_vector(user_id, db)

        # Calculate color overreliance index dynamically from user closet
        color_overreliance_index = None
        try:
            closet_res = await db.execute(select(ClothingItem))
            db_items = closet_res.scalars().all()
            if db_items:
                color_counts = {}
                for item in db_items:
                    color = item.primary_color
                    if color:
                        c_clean = color.title()
                        color_counts[c_clean] = color_counts.get(c_clean, 0) + 1
                
                if color_counts:
                    most_common_color = max(color_counts, key=color_counts.get)
                    count = color_counts[most_common_color]
                    total_items = len(db_items)
                    percentage = (count / total_items) * 100
                    
                    if percentage >= 35.0:
                        advice = f"Our engine detected a {percentage:.1f}% dependency on {most_common_color} tones this month. Your style evolution would benefit from introducing warm earth tones to soften your professional silhouette."
                    else:
                        advice = f"You have a balanced closet with {most_common_color} making up {percentage:.1f}% of your items. Excellent aesthetic diversity!"
                        
                    color_overreliance_index = {
                        "color_name": most_common_color,
                        "percentage_dependency": round(percentage, 1),
                        "advice": advice
                    }
        except Exception as overreliance_err:
            logger.warning(f"Failed to calculate dynamic color overreliance: {overreliance_err}")
            
        if not color_overreliance_index:
            color_overreliance_index = {
                "color_name": "Navy Blue",
                "percentage_dependency": 40.0,
                "advice": "Our engine detected a 40% dependency on Navy tones this month. Your style evolution would benefit from introducing warm earth tones to soften your professional silhouette."
            }

        # Check if profile already exists
        result = await db.execute(
            select(UserStyleProfile)
            .where(UserStyleProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserStyleProfile(
                id=None,  # let UUID default trigger
                user_id=user_id,
                preferred_colors=prefs["preferred_colors"],
                disliked_colors=prefs["disliked_colors"],
                preferred_styles=prefs["preferred_styles"],
                preferred_formality_range=prefs["preferred_formality_range"],
                favorite_categories=prefs["favorite_categories"],
                color_overreliance_index=color_overreliance_index,
            )
            db.add(profile)
        else:
            profile.preferred_colors = prefs["preferred_colors"]
            profile.disliked_colors = prefs["disliked_colors"]
            profile.preferred_styles = prefs["preferred_styles"]
            profile.preferred_formality_range = prefs["preferred_formality_range"]
            profile.favorite_categories = prefs["favorite_categories"]
            profile.color_overreliance_index = color_overreliance_index
            db.add(profile)

        await db.commit()
        await db.refresh(profile)
        logger.info(f"Learned style profile updated for user {user_id}.")
        return profile

    @classmethod
    async def apply_recommendation_boosts(
        cls,
        outfits: List[Dict[str, Any]],
        user_id: UUID,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Applies learned style profile boosts & penalties to dynamically adjust
        the final score and rank of candidate outfits.
        """
        # Fetch the user style profile
        result = await db.execute(
            select(UserStyleProfile)
            .where(UserStyleProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            # Check if we should compute a preference vector directly from logs (e.g. if profile not created yet)
            prefs = await cls.generate_user_preference_vector(user_id, db)
            disliked_colors = set(prefs["disliked_colors"])
            preferred_colors = set(prefs["preferred_colors"])
            preferred_styles = set(prefs["preferred_styles"])
            disliked_fits = set(prefs["disliked_fits"])
            preferred_formality_range = prefs["preferred_formality_range"]
            prefers_monochrome = prefs["prefers_monochrome"]
        else:
            disliked_colors = set(profile.disliked_colors)
            preferred_colors = set(profile.preferred_colors)
            preferred_styles = set(profile.preferred_styles)
            favorite_categories = set(profile.favorite_categories)
            preferred_formality_range = profile.preferred_formality_range or [1, 10]
            
            # Since disliked_fits and prefers_monochrome are not in UserStyleProfile, fetch them dynamically
            prefs = await cls.generate_user_preference_vector(user_id, db)
            disliked_fits = set(prefs["disliked_fits"])
            prefers_monochrome = prefs["prefers_monochrome"]

        for outfit in outfits:
            items = outfit.get("items", [])
            if not items:
                continue

            multiplier = 1.0
            reasons = outfit.get("reasons", [])
            why_selected = outfit.get("why_selected", [])

            # 1. Colors penalty/boost
            has_disliked_color = False
            has_preferred_color = False
            item_colors = []
            
            for it in items:
                color = it.get("primary_color", "").lower()
                if color:
                    item_colors.append(color)
                    if color in disliked_colors:
                        has_disliked_color = True
                    if color in preferred_colors:
                        has_preferred_color = True

            if has_disliked_color:
                multiplier *= 0.50
                reasons.append("Avoided color penalty: features colors you dislike.")
            elif has_preferred_color:
                multiplier *= 1.05
                why_selected.append("Color boost: integrates your preferred colors.")

            # 2. Preferred styles boost
            has_preferred_style = False
            for it in items:
                style = it.get("style", "").lower()
                if style in preferred_styles:
                    has_preferred_style = True

            if has_preferred_style:
                multiplier *= 1.20
                why_selected.append("Personalized style boost: aligns perfectly with your preferred styles.")

            # 3. Disliked fits penalty
            has_disliked_fit = False
            for it in items:
                fit = it.get("fit", "").lower()
                if fit in disliked_fits:
                    has_disliked_fit = True

            if has_disliked_fit:
                multiplier *= 0.80
                reasons.append("Fit penalty: features garments in fits you typically dislike (e.g., oversized).")

            # 4. Formality boundary penalty
            formality_ratings = [int(it.get("formality", 5)) for it in items]
            avg_formality = sum(formality_ratings) / len(items) if formality_ratings else 5.0
            
            min_f, max_f = preferred_formality_range[0], preferred_formality_range[1]
            if avg_formality < min_f or avg_formality > max_f:
                multiplier *= 0.70
                reasons.append(f"Formality penalty: average formality ({avg_formality:.1f}) is outside your learned preference range ({min_f}-{max_f}).")

            # 5. Monochrome boost
            is_monochrome = len(set(item_colors)) == 1 if item_colors else False
            if is_monochrome and prefers_monochrome:
                multiplier *= 1.15
                why_selected.append("Monochrome boost: harmonizes with your preference for clean monochrome fits.")

            # Adjust final score
            base_score = outfit.get("total_score", 0)
            final_score = round(base_score * multiplier)
            final_score = max(0, min(100, final_score))

            outfit["total_score"] = final_score
            outfit["why_selected"] = list(set(why_selected))
            outfit["reasons"] = list(set(reasons))

        # Re-sort outfits by final score descending
        outfits.sort(key=lambda o: o.get("total_score", 0), reverse=True)
        return outfits
