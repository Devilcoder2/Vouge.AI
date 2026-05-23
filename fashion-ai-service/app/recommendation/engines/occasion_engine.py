"""
Occasion Suitability Engine for Vouge.AI recommendations.
Audits outfits against the target event / environment constraints and applies penalties/bonuses.
"""
from typing import List, Dict
from app.recommendation.rules.fashion_taxonomy import OCCASION_FORMALITY_MAP, CATEGORY_MAP, STYLE_MAP

class OccasionEngine:
    @classmethod
    def calculate_occasion_score(
        cls, 
        items: List[Dict[str, any]], 
        occasion: str
    ) -> Dict[str, any]:
        """
        Calculates suitability score (0.0 to 1.0) and reasoning for a target occasion.
        Items input format: [{"category": "...", "formality": 4, "style": "...", "subcategory": "..."}]
        """
        occ = occasion.lower()
        if occ not in OCCASION_FORMALITY_MAP:
            return {"score": 0.80, "reason": f"Unknown occasion '{occasion}'; evaluated using standard casual rules."}
            
        if not items:
            return {"score": 0.0, "reason": "empty outfit cannot fit occasion"}

        penalties = 0.0
        bonuses = 0.0
        reasons = []

        # 1. Formality Boundary Audit
        min_f, max_f = OCCASION_FORMALITY_MAP[occ]
        formality_values = [it.get("formality", 3) for it in items]
        avg_formality = sum(formality_values) / len(items)
        
        if avg_formality < min_f:
            underdressed_diff = min_f - avg_formality
            penalty = min(0.40, underdressed_diff * 0.15)
            penalties += penalty
            reasons.append(f"underdressed for {occ} (formality: {avg_formality:.1f} < required: {min_f})")
        elif avg_formality > max_f:
            overdressed_diff = avg_formality - max_f
            penalty = min(0.30, overdressed_diff * 0.10)
            penalties += penalty
            reasons.append(f"slightly overdressed for {occ} (formality: {avg_formality:.1f} > required: {max_f})")
        else:
            bonuses += 0.05
            reasons.append("appropriate average formality level")

        # 2. Mandatory Clothing & Footwear Constraints
        for it in items:
            cat = CATEGORY_MAP.get(it["category"])
            style = STYLE_MAP.get(it.get("style", "").lower(), "minimal")
            subcat = it.get("subcategory", "").lower()
            
            # --- WEDDING & FORMAL EVENT AUDIT ---
            if occ in ["wedding", "formal_event"]:
                if cat == "FOOTWEAR":
                    if "sneaker" in subcat or "sandals" in subcat or "slides" in subcat:
                        penalties += 0.35
                        reasons.append("formal dress code strictly prohibits sneakers or sandals")
                    elif any(kw in subcat for kw in ["oxfords", "dress shoes", "loafers", "heels"]):
                        bonuses += 0.05
                if style == "athleisure" or style == "streetwear":
                    penalties += 0.25
                    reasons.append("activewear / streetwear elements are inappropriate for weddings")

            # --- GYM AUDIT ---
            elif occ == "gym":
                if cat == "FOOTWEAR" and "sneaker" not in subcat:
                    penalties += 0.40
                    reasons.append("athletic gym wear requires functional sneakers")
                if style != "athleisure" and cat in ["TOPS", "BOTTOMS"]:
                    penalties += 0.15
                    
            # --- OFFICE AUDIT ---
            elif occ == "office":
                if cat == "FOOTWEAR" and ("slides" in subcat or "sandals" in subcat):
                    penalties += 0.30
                    reasons.append("office dress codes strictly prohibit slides/sandals")
                if style == "streetwear" or style == "grunge":
                    penalties += 0.15
                    reasons.append("streetwear is typically too relaxed for standard office environments")

        # Calculate final consolidated score bounded between 0.0 and 1.0
        final_score = max(0.0, min(1.0, 0.80 - penalties + bonuses))
        
        # Humanize primary findings
        if final_score >= 0.85:
            reason_summary = f"Perfect style synergy for a {occ}."
        elif len(reasons) > 0:
            reason_summary = f"Occasion notes: {', '.join(reasons)}."
        else:
            reason_summary = f"Aesthetically suited for {occ}."
            
        return {
            "score": round(final_score, 2),
            "reason": reason_summary
        }
