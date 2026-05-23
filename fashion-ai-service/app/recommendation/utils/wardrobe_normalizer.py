"""
Wardrobe Normalizer Preprocessing layer for Vouge.AI recommendations.
Cleans raw database records, rejects duplicate and low-confidence predictions,
normalizes strings using rule maps, and groups items by slot categories.
"""
from typing import List, Dict, Any
import logging
from app.recommendation.rules.fashion_taxonomy import CATEGORY_MAP, STYLE_MAP, FIT_MAP

logger = logging.getLogger("fashion-ai-service")

class WardrobeNormalizer:
    @staticmethod
    def normalize_and_group(db_items: List[Any], min_confidence: float = 0.45) -> Dict[str, List[Dict[str, Any]]]:
        """
        Preprocesses raw SQLAlchemy database rows representing clothing items.
        1. Filters out duplicate flags.
        2. Rejects low-confidence entries (confidence < min_confidence).
        3. Standardizes fits, styles, and categories.
        4. Groups items by normalized category slots (TOPS, BOTTOMS, FOOTWEAR, etc.).
        """
        grouped_wardrobe: Dict[str, List[Dict[str, Any]]] = {
            "TOPS": [],
            "BOTTOMS": [],
            "FOOTWEAR": [],
            "OUTERWEAR": [],
            "ACCESSORIES": []
        }
        
        normalized_count = 0
        filtered_count = 0
        
        for item in db_items:
            # 1. Filter out flagged duplicates
            if getattr(item, "is_duplicate", False):
                filtered_count += 1
                logger.info(f"Normalizer: Filtered duplicate item ID: {item.id}")
                continue
                
            # 2. Filter out low-confidence categorizations (unless manually corrected to 1.0)
            confidence = float(getattr(item, "confidence_category", 1.0) or 1.0)
            if confidence < min_confidence:
                filtered_count += 1
                logger.warning(
                    f"Normalizer: Recommender filtering out low-confidence item ID: {item.id} "
                    f"(Category confidence: {confidence:.2f} < threshold: {min_confidence:.2f})"
                )
                continue
                
            # 3. Normalize metadata elements using taxonomy mapping rules
            raw_cat = getattr(item, "category", "Tops")
            normalized_cat = CATEGORY_MAP.get(raw_cat, "TOPS")
            
            raw_style = getattr(item, "style", "minimalist")
            normalized_style = STYLE_MAP.get(raw_style, "minimal")
            
            raw_fit = getattr(item, "fit", "standard")
            normalized_fit = FIT_MAP.get(raw_fit, "regular")
            
            # Map into a clean dictionary payload
            clean_item = {
                "id": item.id,
                "original_category": raw_cat,
                "category": normalized_cat,
                "subcategory": getattr(item, "subcategory", ""),
                "style": normalized_style,
                "fit": normalized_fit,
                "formality": int(getattr(item, "formality", 3)),
                "seasons": getattr(item, "seasons", ["spring", "summer"]),
                "primary_color": getattr(item, "primary_color", "white").lower(),
                "primary_color_hex": getattr(item, "primary_color_hex", "#ffffff"),
                "secondary_colors": [c.lower() for c in getattr(item, "secondary_colors", []) if c],
                "secondary_colors_hex": getattr(item, "secondary_colors_hex", []),
                "pattern": getattr(item, "pattern", "solid"),
                "embedding_path": getattr(item, "embedding_path", None)
            }
            
            # 4. Group in the matching slot
            if normalized_cat in grouped_wardrobe:
                grouped_wardrobe[normalized_cat].append(clean_item)
                normalized_count += 1
                
        logger.info(
            f"Wardrobe Normalization Complete: Normalized/grouped {normalized_count} items. "
            f"Filtered out {filtered_count} duplicates/low-confidence items."
        )
        return grouped_wardrobe
