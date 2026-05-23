"""
Ensemble Outfit Scorer for Vouge.AI recommendations.
Integrates all 5 specialized compatibility engines to calculate a final score (0-100)
using weighted parameters: 30% Color, 25% Style, 20% Occasion, 15% Formality, 10% Season.
"""
from typing import List, Dict, Any

from app.recommendation.engines.color_engine import ColorEngine
from app.recommendation.engines.formality_engine import FormalityEngine
from app.recommendation.engines.style_engine import StyleEngine
from app.recommendation.engines.season_engine import SeasonEngine
from app.recommendation.engines.occasion_engine import OccasionEngine

class OutfitScorer:
    # Component weights as defined in specifications
    WEIGHT_COLOR = 0.30
    WEIGHT_STYLE = 0.25
    WEIGHT_OCCASION = 0.20
    WEIGHT_FORMALITY = 0.15
    WEIGHT_SEASON = 0.10

    @classmethod
    def score_outfit(
        cls, 
        items: List[Dict[str, Any]], 
        occasion: str, 
        season: str
    ) -> Dict[str, Any]:
        """
        Calculates a detailed, multi-engine fashion compatibility breakdown and final score.
        Input format: list of normalized item dicts.
        """
        if not items:
            return {
                "total_score": 0,
                "breakdown": {
                    "color_score": 0,
                    "style_score": 0,
                    "occasion_score": 0,
                    "formality_score": 0,
                    "season_score": 0
                },
                "reasons": ["empty outfit"]
            }

        # 1. Color Harmony Scoring
        color_items = [{"color_name": it["primary_color"], "hex": it["primary_color_hex"]} for it in items]
        color_res = ColorEngine.evaluate_outfit_colors(color_items)
        color_score = color_res["score"]

        # 2. Formality Variance Scoring
        formalities = [it["formality"] for it in items]
        formality_res = FormalityEngine.calculate_formality_score(formalities)
        formality_score = formality_res["score"]

        # 3. Style Synergy Scoring
        styles = [it["style"] for it in items]
        style_res = StyleEngine.calculate_style_score(styles)
        style_score = style_res["score"]

        # 4. Seasonal Layering Scoring
        season_res = SeasonEngine.calculate_season_score(items, season)
        season_score = season_res["score"]

        # 5. Occasion Fit Scoring
        occasion_res = OccasionEngine.calculate_occasion_score(items, occasion)
        occasion_score = occasion_res["score"]

        # 6. Ensemble Weighted Total
        weighted_sum = (
            color_score * cls.WEIGHT_COLOR +
            style_score * cls.WEIGHT_STYLE +
            occasion_score * cls.WEIGHT_OCCASION +
            formality_score * cls.WEIGHT_FORMALITY +
            season_score * cls.WEIGHT_SEASON
        )
        
        # Convert total to integer scale 0 - 100
        total_score = round(weighted_sum * 100)

        # Assemble clean explanations list
        reasons = [
            f"Color: {color_res['reason']}",
            f"Style: {style_res['reason']}",
            f"Occasion: {occasion_res['reason']}",
            f"Formality: {formality_res['reason']}",
            f"Season: {season_res['reason']}"
        ]

        return {
            "total_score": total_score,
            "breakdown": {
                "color_score": round(color_score * 100),
                "style_score": round(style_score * 100),
                "occasion_score": round(occasion_score * 100),
                "formality_score": round(formality_score * 100),
                "season_score": round(season_score * 100)
            },
            "reasons": reasons
        }
