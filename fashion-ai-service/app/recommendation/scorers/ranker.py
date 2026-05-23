"""
Recommendation Ranker and Diversity Filter for Vouge.AI.
Ranks outfit candidates, deduplicates highly repetitive outputs,
and ensures visual/stylistic variety in generated recommendations.
"""
from typing import List, Dict, Any, Set

class RecommendationRanker:
    @staticmethod
    def diversify_and_rank(
        scored_candidates: List[Dict[str, Any]], 
        max_outputs: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Ranks outfit recommendations and enforces diversity boundaries.
        Prevents repetitive outfits (e.g., having identical Top + Bottom with only a shoe swap).
        """
        # Sort by total score descending
        scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)
        
        ranked_outputs: List[Dict[str, Any]] = []
        
        # Track combinations we have already included to enforce diversity
        # We store hashes of (top_id, bottom_id) pairs to limit repetitions
        included_combos: Set[tuple] = set()
        
        for candidate in scored_candidates:
            items = candidate["items"]
            
            # Find garment IDs inside the candidate outfit
            top_id = None
            bottom_id = None
            for it in items:
                cat = it["category"]
                if cat == "TOPS":
                    top_id = it["id"]
                elif cat == "BOTTOMS":
                    bottom_id = it["id"]
                    
            # Enforce diversity filter:
            # If we already have an outfit featuring the exact same top AND bottom combination,
            # skip this candidate to avoid flooding the user with minor shoe/accessory swaps.
            if top_id and bottom_id:
                combo_key = (top_id, bottom_id)
                if combo_key in included_combos:
                    continue  # Filter out: redundant top + bottom combination
                included_combos.add(combo_key)
                
            # If diverse, append
            ranked_outputs.append(candidate)
            
            # Break if we have filled the requested list size
            if len(ranked_outputs) >= max_outputs:
                break
                
        return ranked_outputs
