"""
Quality and Diversity Evaluator for Vouge.AI recommendations.
Computes diversity index benchmarks across recommendation lists.
"""
from typing import List, Dict, Any

class QualityEvaluator:
    @staticmethod
    def evaluate_recommendations_diversity(outfits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates the stylistic diversity and score quality of a recommendation list.
        """
        if not outfits:
            return {
                "diversity_index": 0.0,
                "average_score": 0.0,
                "unique_items_ratio": 0.0,
                "verdict": "No outfits provided for evaluation."
            }
            
        total_outfits = len(outfits)
        scores = [o["score"] for o in outfits]
        avg_score = sum(scores) / total_outfits
        
        # Count all unique items recommended
        recommended_item_ids = set()
        categories_count = {}
        
        for outfit in outfits:
            for item in outfit["items"]:
                recommended_item_ids.add(item["id"])
                cat = item["category"]
                categories_count[cat] = categories_count.get(cat, 0) + 1
                
        # Total unique items divided by (total outfits * average items per outfit)
        total_possible_slots = sum(len(o["items"]) for o in outfits)
        unique_ratio = len(recommended_item_ids) / total_possible_slots if total_possible_slots > 0 else 0.0
        
        # Enforce diversity thresholds:
        # A high unique ratio (> 0.40) indicates excellent recommendation variety
        if unique_ratio >= 0.45:
            verdict = "Excellent stylistic diversity; recommendations span multiple capsule variations."
        elif unique_ratio >= 0.25:
            verdict = "Good diversity; subtle modifications but broad wardrobe coverage."
        else:
            verdict = "Low diversity; recommendations focus heavily on repeating same garments."
            
        return {
            "diversity_index": round(unique_ratio * 100, 1),
            "average_score": round(avg_score, 1),
            "unique_items_ratio": round(unique_ratio, 2),
            "verdict": verdict
        }
