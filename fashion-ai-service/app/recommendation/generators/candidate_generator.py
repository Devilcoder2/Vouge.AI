"""
Combinatorial Candidate Generation Engine for Vouge.AI.
Selects occasion templates and matches wardrobe items using early pruning
to construct a diverse list of 20–50 highly compatible candidate outfits.
"""
from typing import List, Dict, Any, Set
import logging
from app.recommendation.utils.wardrobe_normalizer import WardrobeNormalizer
from app.recommendation.generators.outfit_templates import get_templates_for_occasion, OutfitTemplate
from app.recommendation.engines.color_engine import ColorEngine
from app.recommendation.engines.formality_engine import FormalityEngine

logger = logging.getLogger("fashion-ai-service")

class CandidateGenerator:
    @classmethod
    def generate_candidates(
        cls, 
        db_items: List[Any], 
        occasion: str, 
        season: str, 
        max_candidates: int = 40
    ) -> List[Dict[str, Any]]:
        """
        Orchestrates outfit candidate generation.
        1. Normalizes and groups wardrobe items.
        2. Retrieves outfit templates suited for the occasion.
        3. Iterates through combinations and applies early pruning.
        4. Returns a ranked, pruned candidate list of size <= max_candidates.
        """
        # Step 1: Preprocess and group wardrobe
        grouped_wardrobe = WardrobeNormalizer.normalize_and_group(db_items)
        
        # Step 2: Retrieve templates matching occasion
        templates = get_templates_for_occasion(occasion)
        
        candidates: List[Dict[str, Any]] = []
        
        for template in templates:
            logger.info(f"Generating candidates using template: {template.name}")
            template_candidates = cls._generate_for_template(
                grouped_wardrobe, template, occasion, season
            )
            candidates.extend(template_candidates)
            
        # Step 3: Sort candidate list by preliminary heuristic score and truncate
        # This guarantees we get exactly the top-N high-quality candidates
        candidates.sort(key=lambda x: x["preliminary_score"], reverse=True)
        truncated_candidates = candidates[:max_candidates]
        
        logger.info(f"Generated {len(truncated_candidates)} candidate outfits after pruning and scoring.")
        return truncated_candidates

    @classmethod
    def _generate_for_template(
        cls,
        wardrobe: Dict[str, List[Dict[str, Any]]],
        template: OutfitTemplate,
        occasion: str,
        season: str
    ) -> List[Dict[str, Any]]:
        """
        Performs early-pruned combinatorial generation for a specific template.
        """
        req_slots = template.required_slots
        
        # Guard: Check if the user has at least one item in all required slots
        for slot in req_slots:
            if not wardrobe.get(slot):
                logger.info(f"Template '{template.name}' skipped: user lacks items in required category: {slot}")
                return []
                
        # We support standard slots: TOPS, BOTTOMS, FOOTWEAR
        # Let's pull candidates matching subcategory restrictions
        tops = cls._filter_by_restrictions(wardrobe["TOPS"], template.subcat_restrictions.get("TOPS"))
        bottoms = cls._filter_by_restrictions(wardrobe["BOTTOMS"], template.subcat_restrictions.get("BOTTOMS"))
        shoes = cls._filter_by_restrictions(wardrobe["FOOTWEAR"], template.subcat_restrictions.get("FOOTWEAR"))
        
        if not tops or not bottoms or not shoes:
            return []
            
        generated: List[Dict[str, Any]] = []
        
        # Combinatorial loop with early pruning
        for top in tops:
            for bottom in bottoms:
                # Early Pruning 1: Top & Bottom Formality Check
                f_diff = abs(top["formality"] - bottom["formality"])
                if f_diff > 4:
                    continue  # Prune: Too high variance (e.g. blazer + gym shorts)
                    
                # Early Pruning 2: Top & Bottom Color Check
                color_res = ColorEngine.calculate_compatibility(
                    top["primary_color"], top["primary_color_hex"],
                    bottom["primary_color"], bottom["primary_color_hex"]
                )
                if color_res["score"] < 0.40:
                    continue  # Prune: Hard clashing color matches
                    
                for shoe in shoes:
                    # Early Pruning 3: Shoe & Outfit Formality Check
                    formalities = [top["formality"], bottom["formality"], shoe["formality"]]
                    formality_res = FormalityEngine.calculate_formality_score(formalities)
                    if formality_res["score"] < 0.45:
                        continue  # Prune: Footwear totally mismatches outfit formality
                        
                    # Early Pruning 4: Shoe Color Check
                    shoe_color_res = ColorEngine.calculate_compatibility(
                        bottom["primary_color"], bottom["primary_color_hex"],
                        shoe["primary_color"], shoe["primary_color_hex"]
                    )
                    if shoe_color_res["score"] < 0.40:
                        continue  # Prune: Shoes clash with bottoms
                        
                    # Standard base outfit is formed!
                    outfit_items = [top, bottom, shoe]
                    
                    # Try to add optional OUTERWEAR if required or available
                    outerwear_candidates = wardrobe.get("OUTERWEAR", [])
                    selected_outerwear = None
                    
                    if outerwear_candidates and ("OUTERWEAR" in template.optional_slots or "OUTERWEAR" in template.required_slots):
                        filtered_outerwear = cls._filter_by_restrictions(
                            outerwear_candidates, template.subcat_restrictions.get("OUTERWEAR")
                        )
                        # Find the single best outerwear piece to layer
                        best_outer = None
                        best_outer_score = -1.0
                        
                        for out in filtered_outerwear:
                            # Evaluate compatibility with top and bottom
                            col_a = ColorEngine.calculate_compatibility(
                                top["primary_color"], top["primary_color_hex"],
                                out["primary_color"], out["primary_color_hex"]
                            )["score"]
                            col_b = ColorEngine.calculate_compatibility(
                                bottom["primary_color"], bottom["primary_color_hex"],
                                out["primary_color"], out["primary_color_hex"]
                            )["score"]
                            avg_col = (col_a + col_b) / 2
                            
                            # Formality match
                            f_match = 1.0 - (abs(out["formality"] - sum(formalities)/3) / 10)
                            
                            score = avg_col * 0.6 + f_match * 0.4
                            if score > best_outer_score:
                                best_outer_score = score
                                best_outer = out
                                
                        # If a good outerwear option is found, add it
                        if best_outer and best_outer_score > 0.50:
                            selected_outerwear = best_outer
                            
                    if selected_outerwear:
                        outfit_items.append(selected_outerwear)
                        
                    # Calculate a lightweight heuristic score for preliminary pruning
                    prelim_score = (color_res["score"] + formality_res["score"] + shoe_color_res["score"]) / 3
                    
                    # Store candidate structure
                    generated.append({
                        "template_name": template.name,
                        "items": outfit_items,
                        "preliminary_score": round(prelim_score, 2)
                    })
                    
                    # Safety net to avoid huge candidate list memory blowup
                    if len(generated) >= 150:
                        break
                if len(generated) >= 150:
                    break
            if len(generated) >= 150:
                break
                
        return generated

    @staticmethod
    def _filter_by_restrictions(items: List[Dict[str, Any]], allowed_subcats: List[str] = None) -> List[Dict[str, Any]]:
        """Filters a list of items to match allowed subcategories, if specified."""
        if not allowed_subcats:
            return items
        return [it for it in items if it.get("subcategory") in allowed_subcats]
