"""
Seasonal Suitability & Layering Engine for Vouge.AI recommendations.
Assesses if an outfit matches seasonal weather and rewards smart outerwear layering.
"""
from typing import List, Dict
from app.recommendation.rules.fashion_taxonomy import CATEGORY_MAP

class SeasonEngine:
    @staticmethod
    def calculate_season_score(
        items: List[Dict[str, any]], 
        target_season: str
    ) -> Dict[str, any]:
        """
        Assesses an outfit's seasonal suitability.
        Each item is expected to be: {"category": "...", "seasons": ["spring", ...]}
        target_season: "spring", "summer", "autumn", "winter"
        """
        target_season = target_season.lower()
        if not items:
            return {"score": 1.0, "reason": "empty wardrobe (default season)"}
            
        penalties = 0.0
        has_outerwear = any(CATEGORY_MAP.get(it["category"]) == "OUTERWEAR" for it in items)
        
        # Track items that are not season-appropriate
        out_of_season_count = 0
        reasons = []
        
        for it in items:
            item_seasons = [s.lower() for s in it.get("seasons", [])]
            category = CATEGORY_MAP.get(it["category"])
            
            # If the item is natively suitable for the target season, perfect
            if target_season in item_seasons:
                continue
                
            # If not suitable, apply penalty based on smart layering rules
            out_of_season_count += 1
            
            # Layering Exception:
            # A summer/spring top in winter is acceptable if the outfit includes OUTERWEAR
            if target_season == "winter" and category == "TOPS" and has_outerwear:
                # Reduced penalty due to active outerwear layering
                penalties += 0.10
                reasons.append(f"lightweight top successfully layered with winter outerwear")
            elif target_season == "summer" and category == "OUTERWEAR":
                # Heavy outerwear in summer is highly inappropriate
                penalties += 0.40
                reasons.append("heavy outerwear is inappropriate for summer temperatures")
            else:
                # Default out-of-season penalty
                penalties += 0.25
                reasons.append(f"garment not designed for standard {target_season} wear")
                
        # Calculate final score (bounded between 0.0 and 1.0)
        final_score = max(0.0, 1.0 - penalties)
        
        if out_of_season_count == 0:
            reason_str = f"Perfect seasonal alignment for {target_season}."
        elif len(reasons) > 0:
            reason_str = f"Seasonal warnings: {'; '.join(reasons)}."
        else:
            reason_str = f"Satisfactory seasonal alignment for {target_season}."
            
        return {
            "score": round(final_score, 2),
            "reason": reason_str
        }
