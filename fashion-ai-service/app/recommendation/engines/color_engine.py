"""
Color Compatibility Engine for Vouge.AI.
Calculates the aesthetic compatibility score between two garment colors using:
1. Heuristic naming rules (Neutrals, Complementaries, Clashes).
2. Precise mathematical distance (Delta-E in CIELAB space) from HEX values.
"""
from typing import Dict, List, Tuple
from app.recommendation.utils.color_utils import hex_to_lab, cie_delta_e, hex_to_hsv
from app.recommendation.rules.color_rules import get_color_compatibility_score, NEUTRALS

class ColorEngine:
    @staticmethod
    def calculate_compatibility(
        color_name_a: str, 
        hex_a: str, 
        color_name_b: str, 
        hex_b: str
    ) -> Dict[str, any]:
        """
        Calculates a compatibility score (0.0 to 1.0) and reasoning
        between two clothing items based on their primary colors.
        """
        # Validate hex inputs
        if not hex_a or not hex_a.startswith("#"):
            hex_a = "#ffffff"
        if not hex_b or not hex_b.startswith("#"):
            hex_b = "#ffffff"

        # 1. Fetch name-based fashion compatibility score
        name_score, reason = get_color_compatibility_score(color_name_a, color_name_b)
        
        try:
            # 2. Perform CIELAB Delta-E distance calculation
            lab_a = hex_to_lab(hex_a)
            lab_b = hex_to_lab(hex_b)
            delta_e = cie_delta_e(lab_a, lab_b)
            
            # Extract Value / Brightness from HSV for contrast comparisons
            _, _, val_a = hex_to_hsv(hex_a)
            _, _, val_b = hex_to_hsv(hex_b)
            
            # Near-Contrast Mismatch Penalty:
            # If two distinct colors are extremely close in shade but not identical,
            # they often clash (e.g., dark navy next to black, or two slightly off Beiges).
            if 1.0 < delta_e < 12.0 and color_name_a.lower() != color_name_b.lower():
                # Apply a slight penalty for "near-miss" shades
                contrast_penalty = 0.25
                name_score = max(0.40, name_score - contrast_penalty)
                reason = f"risky near-miss shades (Delta-E {delta_e:.1f}); lacks intentional contrast"
                
            # Monochromatic high-precision match:
            # If color names are the same and Delta-E is tiny, it's a solid monochrome match
            elif delta_e < 5.0 and color_name_a.lower() == color_name_b.lower():
                name_score = max(name_score, 0.95)
                
        except Exception as err:
            # Fallback gracefully to purely name-based scoring if hex parsing fails
            pass
            
        return {
            "score": round(name_score, 2),
            "reason": reason
        }

    @classmethod
    def evaluate_outfit_colors(cls, items: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Evaluates color harmony across a list of items forming an outfit.
        Each item is expected to be a dict: {"color_name": "...", "hex": "..."}.
        Returns an ensemble score and reason.
        """
        if not items or len(items) <= 1:
            return {"score": 1.0, "reason": "single item or empty outfit (default harmony)"}
            
        scores = []
        clash_detected = False
        reasons = []
        
        # Calculate pairwise compatibility between all items in the outfit
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                res = cls.calculate_compatibility(
                    items[i]["color_name"], items[i]["hex"],
                    items[j]["color_name"], items[j]["hex"]
                )
                scores.append(res["score"])
                reasons.append(res["reason"])
                if res["score"] < 0.50:
                    clash_detected = True
                    
        avg_score = sum(scores) / len(scores)
        
        # If there are any high-clash pairs, pull the entire score down significantly
        if clash_detected:
            final_score = min(avg_score, 0.45)
            # Find the first clashing reason
            clash_reason = next((r for r in reasons if "clash" in r or "near-miss" in r), reasons[0])
            reason_str = f"Color clash detected: {clash_reason}"
        else:
            final_score = avg_score
            # Summarize outfit composition
            unique_colors = {it["color_name"].lower() for it in items}
            neutrals_in_outfit = unique_colors.intersection(NEUTRALS)
            
            if len(unique_colors) <= 2:
                reason_str = "Clean, low-palette minimalist color harmony."
            elif len(neutrals_in_outfit) >= 2:
                reason_str = "Balanced neutral foundation with subtle accents."
            else:
                reason_str = "Multi-color palette (rely on style consistency for balance)."
                
        return {
            "score": round(final_score, 2),
            "reason": reason_str
        }
