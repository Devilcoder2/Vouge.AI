"""
Body Type Engine for Vouge.AI recommendations.
Evaluates how well an outfit's item silhouettes match the user's physical body archetype,
height proportions, and manual fit preferences.
"""
from typing import List, Dict, Any

class BodyTypeEngine:
    @classmethod
    def calculate_body_compatibility(
        cls,
        items: List[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scores outfit compatibility (0.0 to 1.0) against the user's body profile.
        """
        if not items or not profile:
            return {"score": 1.0, "reason": "No body profile or items available for body analysis.", "why_selected": []}

        height = profile.get("height_cm")
        archetype = profile.get("body_archetype", "rectangle")
        pref_fit = profile.get("fit_preference", "standard")

        score = 1.0
        penalties = 0.0
        boosts = 0.0
        reasons = []

        # 1. Height Analysis
        is_tall = height is not None and height >= 180
        is_short = height is not None and height < 165

        # 2. Loop through each item in the outfit to check silhouette and fit compatibility
        for it in items:
            it_category = it.get("category", "").upper()
            it_subcategory = it.get("subcategory", "").lower()
            it_fit = it.get("fit", "").lower()
            it_style = it.get("style", "").lower()

            # 2.1 Fit Preference Match
            # Standard taxonomy standard translates to 'regular' in normalizer
            normalized_pref = "regular" if pref_fit == "standard" else pref_fit
            normalized_it_fit = "regular" if it_fit == "standard" else it_fit
            
            if normalized_it_fit == normalized_pref:
                boosts += 0.05
                
            # 2.2 Body Archetype and Fit Science
            if archetype == "lean_tall" or (is_tall and archetype == "lean_tall"):
                # Oversized works beautifully on tall lean structures
                if normalized_it_fit == "oversized":
                    boosts += 0.08
                    reasons.append(f"Oversized fit of {it.get('subcategory', 'garment')} perfectly complements your lean tall stature.")
                # Short cropped jackets work poorly without proportion balance
                if it_category == "OUTERWEAR" and "cropped" in it_subcategory:
                    penalties += 0.10
                    reasons.append("Cropped outerwear can clash with tall body proportions.")

            elif archetype == "stocky" or archetype == "athletic":
                # Athletic/stocky frames are penalized slightly for excessively slim fit trousers to avoid pinching silhouettes
                if it_category == "BOTTOMS" and normalized_it_fit == "slim":
                    penalties += 0.08
                    reasons.append(f"Slim-fit pants may feel restrictive on your {archetype} build; regular or standard drape is preferred.")
                # Athletic profiles look elegant in structured standard outerwear
                if it_category == "OUTERWEAR" and normalized_it_fit == "regular":
                    boosts += 0.05

            elif archetype == "pear_shape":
                # Pear shapes benefit from structured/wider upper body lines to balance wider hips
                if it_category == "TOPS" and (normalized_it_fit == "oversized" or "blazer" in it_subcategory):
                    boosts += 0.08
                    reasons.append(f"Structured or relaxed top silhouette balances your pear shape proportions nicely.")
                if it_category == "BOTTOMS" and normalized_it_fit == "slim":
                    penalties += 0.05

            elif archetype == "rectangle":
                # Rectangle shapes can build visual depth using textured layers or standard relaxed tailoring
                if it_category == "OUTERWEAR" and (normalized_it_fit == "relaxed" or normalized_it_fit == "oversized"):
                    boosts += 0.05

        # Bound score between 0.0 and 1.0
        final_score = max(0.0, min(1.0, score + boosts - penalties))
        
        # Select premium styled description to return
        why_selected = []
        if boosts > penalties:
            why_selected.append(f"Tailored to complement your {archetype.replace('_', ' ')} archetype proportions.")
        if pref_fit != "standard" and boosts > 0.02:
            why_selected.append(f"Aligned with your preference for {pref_fit} fits.")

        return {
            "score": final_score,
            "reason": "; ".join(reasons) if reasons else "Outfit fits your silhouette proportions nicely.",
            "why_selected": why_selected
        }
