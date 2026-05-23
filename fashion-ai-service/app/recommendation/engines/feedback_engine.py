"""
Feedback / Preference Learning Engine for Vouge.AI recommendations.
Dynamically adjusts outfit scores based on historical user interactions
(likes, saves, dismissals) and user profile color/style preferences.
"""
from typing import List, Dict, Any

class FeedbackEngine:
    @classmethod
    def calculate_feedback_adjustments(
        cls,
        items: List[Dict[str, Any]],
        profile: Dict[str, Any],
        feedbacks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates score multiplier boosts and penalties based on user preferences and feedback history.
        """
        score_adj = 1.0
        boosts = 0.0
        penalties = 0.0
        reasons = []
        why_selected = []

        # 1. Parse Profile Preferences
        avoided_colors = set(c.lower() for c in profile.get("avoided_colors", []))
        favorite_styles = set(s.lower() for s in profile.get("favorite_styles", []))

        # Check for avoided colors (Hard Penalty)
        for it in items:
            color = it.get("primary_color", "").lower()
            if color in avoided_colors:
                penalties += 0.40
                reasons.append(f"Contains {color}, which is on your avoided colors list.")

            style = it.get("style", "").lower()
            if style in favorite_styles:
                boosts += 0.05

        # 2. Parse Historical Feedback Actions
        # Collate IDs of liked/saved items and dismissed items
        liked_item_ids = set()
        dismissed_item_ids = set()

        for fb in feedbacks:
            fb_type = fb.get("feedback_type", "").lower()
            item_ids = fb.get("outfit_item_ids", [])
            
            if fb_type in ["like", "save"]:
                for iid in item_ids:
                    liked_item_ids.add(str(iid))
            elif fb_type == "dismiss":
                for iid in item_ids:
                    dismissed_item_ids.add(str(iid))

        # Apply interaction adjustments
        for it in items:
            it_id_str = str(it.get("id", ""))
            
            if it_id_str in liked_item_ids:
                boosts += 0.06
                why_selected.append(f"Features {it.get('subcategory', 'your garments')} which you've frequently liked.")
            
            if it_id_str in dismissed_item_ids:
                penalties += 0.15
                reasons.append(f"Features {it.get('subcategory', 'garments')} you previously dismissed.")

        # Compute combined score factor
        final_adjustment = max(0.0, min(2.0, score_adj + boosts - penalties))

        if boosts > penalties and boosts > 0.02:
            why_selected.append("Synergized with your historical favorite styles and saved looks.")

        return {
            "adjustment_factor": final_adjustment,
            "reason": "; ".join(reasons) if reasons else "Outfit aligns with your personal style preferences.",
            "why_selected": list(set(why_selected))
        }
