"""
Wardrobe Versatility Engine for Vouge.AI recommendations.
Identifies and ranks clothes based on their reuse potential across outfit combinations.
"""
from typing import List, Dict, Any
from collections import Counter
import logging
from app.recommendation.generators.candidate_generator import CandidateGenerator

logger = logging.getLogger("fashion-ai-service")

class VersatilityEngine:
    @classmethod
    def calculate_versatility(cls, db_items: List[Any]) -> List[Dict[str, Any]]:
        """
        Ranks all wardrobe items by their outfit reuse frequency across casual, office, and date settings.
        """
        if not db_items:
            return []

        # 1. Generate a large pool of possible outfits across core occasions
        test_occasions = ["casual", "office", "date"]
        all_candidates: List[Dict[str, Any]] = []
        
        for occ in test_occasions:
            # We generate up to 100 candidates per occasion to build a broad statistical base
            all_candidates.extend(
                CandidateGenerator.generate_candidates(db_items, occ, "spring", max_candidates=100)
            )
            
        if not all_candidates:
            # If no outfits can be formed, default versatility score to 0
            return [
                {
                    "item_id": it.id,
                    "category": it.category,
                    "subcategory": it.subcategory,
                    "primary_color": it.primary_color,
                    "versatility_score": 0,
                    "usage_count": 0,
                    "reasoning": "Unlocks 0 outfits. Add matching slots (tops/bottoms/shoes) to start utilizing this piece."
                }
                for it in db_items
            ]

        # 2. Count occurrences of each item ID across all outfits
        item_counter = Counter()
        for cand in all_candidates:
            for it in cand["items"]:
                item_counter[it["id"]] += 1
                
        total_outfits = len(all_candidates)
        results: List[Dict[str, Any]] = []

        # 3. Score and format results
        # We match back the IDs to original item objects
        for item in db_items:
            usage = item_counter[item.id]
            # Calculate versatility score as a percentage of total outfits this item belongs to
            # We add a small category baseline to ensure realistic scaling
            score = round((usage / total_outfits) * 100)
            
            # Stylist commentary based on score
            if score >= 60:
                comment = "Ultimate capsule anchor. Highly versatile foundation piece matching almost anything."
            elif score >= 35:
                comment = "Excellent rotation piece. Pairs easily with multiple styling setups."
            elif score >= 10:
                comment = "Slightly specialized garment. Suited for specific combinations or occasions."
            else:
                comment = "Highly statement or specialized item. Reserved for specific focal styling."

            results.append({
                "item_id": item.id,
                "category": item.category,
                "subcategory": item.subcategory,
                "primary_color": item.primary_color,
                "versatility_score": score,
                "usage_count": usage,
                "reasoning": comment
            })

        # Sort by versatility score descending
        results.sort(key=lambda x: x["versatility_score"], reverse=True)
        return results
