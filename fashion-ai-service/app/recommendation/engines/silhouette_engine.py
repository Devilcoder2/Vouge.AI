"""
Silhouette Proportions Balance Engine for Vouge.AI recommendations.
Evaluates the fit proportions and silhouette shape balance of outfits
(e.g., oversized top + slim bottoms is visually balanced; oversized top + oversized bottoms claps unless intentional).
"""
from typing import List, Dict, Any

class SilhouetteEngine:
    @classmethod
    def calculate_silhouette_balance(
        cls,
        items: List[Dict[str, Any]],
        occasion: str,
        style_persona: str
    ) -> Dict[str, Any]:
        """
        Evaluates structural proportion balance between tops and bottoms in the outfit.
        """
        if not items:
            return {"score": 1.0, "reason": "No items to evaluate silhouette balance.", "why_selected": []}

        # Pick the top and bottom items
        top_item = next((it for it in items if it.get("category", "").upper() == "TOPS"), None)
        bottom_item = next((it for it in items if it.get("category", "").upper() == "BOTTOMS"), None)

        if not top_item or not bottom_item:
            return {"score": 1.0, "reason": "Complete top/bottom combo not present; skipping silhouette analysis.", "why_selected": []}

        top_fit = top_item.get("fit", "").lower()
        bottom_fit = bottom_item.get("fit", "").lower()

        # Normalize standard fits to regular fit
        norm_top_fit = "regular" if top_fit == "standard" else top_fit
        norm_bottom_fit = "regular" if bottom_fit == "standard" else bottom_fit

        score = 1.0
        penalties = 0.0
        boosts = 0.0
        reasons = []
        why_selected = []

        style_persona_lower = style_persona.lower() if style_persona else ""

        # Proportion Rules
        # 1. Baggy-Baggy: Oversized Top + Oversized Bottom (streetwear/avant-garde exception)
        if norm_top_fit == "oversized" and norm_bottom_fit == "oversized":
            if style_persona_lower in ["streetwear", "avant_garde"]:
                boosts += 0.05
                why_selected.append("Relaxed double-baggy silhouette fits streetwear aesthetic preferences.")
            else:
                penalties += 0.20
                reasons.append("Oversized top paired with oversized bottoms can swallow your silhouette proportions; try standard or slim trousers.")

        # 2. Balanced Contrast: Oversized Top + Slim Bottom
        elif norm_top_fit == "oversized" and norm_bottom_fit == "slim":
            boosts += 0.08
            why_selected.append("Elegant contrast proportion: oversized top balanced with slim bottoms.")

        # 3. Tight-Tight: Slim Top + Slim Bottom (formal exception)
        elif norm_top_fit == "slim" and norm_bottom_fit == "slim":
            if occasion.lower() in ["office", "formal", "wedding"]:
                boosts += 0.05
            else:
                penalties += 0.15
                reasons.append("Double slim-fit silhouette can look overly severe for casual occasions.")

        # 4. Standard Classic: Regular Top + Regular Bottom
        elif norm_top_fit == "regular" and norm_bottom_fit == "regular":
            boosts += 0.05

        final_score = max(0.0, min(1.0, score + boosts - penalties))

        return {
            "score": final_score,
            "reason": "; ".join(reasons) if reasons else "Perfect silhouette proportion balance.",
            "why_selected": why_selected
        }
