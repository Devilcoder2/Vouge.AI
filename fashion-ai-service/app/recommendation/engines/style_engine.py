"""
Style Consistency Engine for Vouge.AI recommendations.
Evaluates aesthetic compatibility using a multi-dimensional Style Compatibility Matrix.
"""
from typing import List, Dict
from app.recommendation.rules.fashion_taxonomy import STYLE_MAP, STYLES

class StyleEngine:
    # Style Compatibility Matrix mapping (Style A, Style B) -> compatibility score (0.0 to 1.0)
    # Undefined symmetric entries will resolve to the same value
    STYLE_MATRIX: Dict[tuple, float] = {
        # Minimalist blends
        ("minimal", "minimal"): 1.0,
        ("minimal", "classic"): 0.95,
        ("minimal", "smart_casual"): 0.95,
        ("minimal", "streetwear"): 0.85,
        ("minimal", "formal"): 0.85,
        ("minimal", "vintage"): 0.80,
        ("minimal", "athleisure"): 0.80,
        
        # Streetwear blends
        ("streetwear", "streetwear"): 1.0,
        ("streetwear", "athleisure"): 0.95,
        ("streetwear", "vintage"): 0.85,
        ("streetwear", "smart_casual"): 0.70,
        ("streetwear", "classic"): 0.60,
        ("streetwear", "formal"): 0.20,  # Serious mismatch
        
        # Formal blends
        ("formal", "formal"): 1.0,
        ("formal", "classic"): 0.95,
        ("formal", "smart_casual"): 0.85,
        ("formal", "vintage"): 0.70,
        ("formal", "athleisure"): 0.15,  # Serious mismatch
        
        # Classic blends
        ("classic", "classic"): 1.0,
        ("classic", "smart_casual"): 0.95,
        ("classic", "vintage"): 0.85,
        ("classic", "athleisure"): 0.50,
        
        # Smart Casual blends
        ("smart_casual", "smart_casual"): 1.0,
        ("smart_casual", "vintage"): 0.80,
        ("smart_casual", "athleisure"): 0.70,
        
        # Athleisure and Vintage
        ("athleisure", "athleisure"): 1.0,
        ("athleisure", "vintage"): 0.60,
        ("vintage", "vintage"): 1.0
    }

    @classmethod
    def get_style_pairing_score(cls, style_a: str, style_b: str) -> float:
        """Helper to fetch bidirectional score from symmetric matrix."""
        # Normalize incoming styles using fashion taxonomy mapping
        sa = STYLE_MAP.get(style_a.lower(), "minimal")
        sb = STYLE_MAP.get(style_b.lower(), "minimal")
        
        # Check standard dictionary combinations bidirectionally
        if (sa, sb) in cls.STYLE_MATRIX:
            return cls.STYLE_MATRIX[(sa, sb)]
        if (sb, sa) in cls.STYLE_MATRIX:
            return cls.STYLE_MATRIX[(sb, sa)]
            
        return 0.70  # Default moderate compatibility score

    @classmethod
    def calculate_style_score(cls, styles_list: List[str]) -> Dict[str, any]:
        """
        Given a list of aesthetic styles from the items,
        returns the ensemble style score (0.0 to 1.0) and descriptive reasoning.
        """
        if not styles_list or len(styles_list) <= 1:
            return {"score": 1.0, "reason": "single item or empty outfit (default style harmony)"}
            
        scores = []
        for i in range(len(styles_list)):
            for j in range(i + 1, len(styles_list)):
                scores.append(cls.get_style_pairing_score(styles_list[i], styles_list[j]))
                
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.90:
            reason = "Highly unified style profile; aesthetically seamless blend."
        elif avg_score >= 0.75:
            reason = "Intentional hybrid styling; well-balanced aesthetic integration."
        elif avg_score >= 0.50:
            reason = "Aesthetic styles clash slightly; elements could look disconnected unless styled intentionally."
        else:
            reason = "Aesthetic style clash; combining highly conflicting styles (e.g. streetwear/activewear with high formalwear)."
            
        return {
            "score": round(avg_score, 2),
            "reason": reason
        }
