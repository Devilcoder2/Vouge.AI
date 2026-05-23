"""
Formality Consistency Engine for Vouge.AI recommendations.
Prevents awkward style clashes like a high-formality blazer paired with low-formality basketball shorts.
"""
from typing import List, Dict

class FormalityEngine:
    @staticmethod
    def calculate_formality_score(formality_list: List[int]) -> Dict[str, any]:
        """
        Given a list of formality ratings (integers 1-10) for all outfit items,
        returns a formality consistency score (0.0 to 1.0) and reasoning.
        """
        if not formality_list or len(formality_list) <= 1:
            return {"score": 1.0, "reason": "single item or empty outfit (default formality harmony)"}
            
        min_f = min(formality_list)
        max_f = max(formality_list)
        variance = max_f - min_f
        
        # Continuous mathematical scoring curve based on maximum variance
        if variance <= 2:
            score = 1.0
            reason = "Perfect formality balance; highly unified aesthetic tone."
        elif variance <= 4:
            score = 0.85
            reason = "Acceptable formality variance; comfortable hybrid styling (e.g., smart-casual)."
        elif variance <= 6:
            score = 0.45
            reason = f"High formality mismatch (variance: {variance}); contrasting dress codes (e.g., blazer with casual tee)."
        else:
            score = 0.15
            reason = f"Severe formality clash (variance: {variance}); highly conflicting pieces (e.g., formal suit elements with activewear)."
            
        return {
            "score": score,
            "reason": reason
        }
