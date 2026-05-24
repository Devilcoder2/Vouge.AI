"""
Centralized Guardrails and Hard Validation Firewall for Vouge.AI.
Defines absolute style, category, and seasonal compatibility boundaries.
Rejects absurd outfit configurations prior to scoring or ranking.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("fashion-ai-service")

class RecommendationGuardrails:
    """
    Centralized firewall applying hard block rules to outfit candidates.
    Filters out extreme visual or stylistic clashes that scoring heuristics 
    might otherwise occasionally permit.
    """

    @staticmethod
    def _get_val(item: Any, key: str, default: Any = None) -> Any:
        """
        Helper method to retrieve an attribute from either a dictionary
        or an ORM model instance dynamically.
        """
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    @classmethod
    def is_valid_outfit(cls, items: List[Any]) -> Tuple[bool, Optional[str]]:
        """
        Executes the centralized validation firewall against an outfit.
        Returns:
            (is_valid: bool, rejection_reason: Optional[str])
        """
        if not items or len(items) < 2:
            return True, None

        # 1. Hard Block: Tuxedo + Gym Shorts (Formal Outerwear/Tops + Gym/Athletic Bottoms)
        is_valid, reason = cls._check_tuxedo_gym_shorts(items)
        if not is_valid:
            return False, reason

        # 2. Hard Block: Winter Parka + Beach Shorts (Heavy Winter Outerwear + Summer/Beach Bottoms)
        is_valid, reason = cls._check_winter_parka_beach_shorts(items)
        if not is_valid:
            return False, reason

        # 3. Hard Block: Formal Leather Shoes + Gym Outfit (Formal Shoes + Athletic Top/Bottom)
        is_valid, reason = cls._check_formal_shoes_gym_outfit(items)
        if not is_valid:
            return False, reason

        # 4. Hard Block: Three Loud Patterned Items Together (Visual Noise Overload)
        is_valid, reason = cls._check_three_loud_patterns(items)
        if not is_valid:
            return False, reason

        return True, None

    @classmethod
    def _check_tuxedo_gym_shorts(cls, items: List[Any]) -> Tuple[bool, Optional[str]]:
        """
        Detects formal tuxedo/suit/blazer tops combined with activewear/gym/beach bottoms.
        """
        has_formal_top = False
        has_gym_bottom = False

        for item in items:
            cat = cls._get_val(item, "category", "").upper()
            sub = str(cls._get_val(item, "subcategory", "")).lower()
            style = str(cls._get_val(item, "style", "")).lower()
            formality = int(cls._get_val(item, "formality", 3))

            # Detect highly formal tops/outerwear
            if cat in ("TOPS", "OUTERWEAR"):
                if (
                    formality >= 8 or 
                    style == "formal" or 
                    any(keyword in sub for keyword in ["tuxedo", "suit", "blazer", "dress shirt", "double-breasted"])
                ):
                    has_formal_top = True

            # Detect athletic/gym bottoms
            elif cat == "BOTTOMS":
                if (
                    formality <= 2 or 
                    style == "athleisure" or 
                    any(keyword in sub for keyword in ["gym", "active", "sport", "track", "sweatpants", "jogger", "boardshort", "beach short", "swim"])
                ):
                    has_gym_bottom = True

        if has_formal_top and has_gym_bottom:
            return False, "Absurd combination rejected: Formal blazer/tuxedo tops cannot be paired with athletic gym shorts or sweatpants."

        return True, None

    @classmethod
    def _check_winter_parka_beach_shorts(cls, items: List[Any]) -> Tuple[bool, Optional[str]]:
        """
        Detects extreme weather/season conflicts, specifically heavy winter coats combined with beach/swimwear.
        """
        has_heavy_winter_coat = False
        has_beach_swim_shorts = False

        for item in items:
            cat = cls._get_val(item, "category", "").upper()
            sub = str(cls._get_val(item, "subcategory", "")).lower()
            seasons = cls._get_val(item, "seasons", [])
            if not isinstance(seasons, list):
                seasons = []
            seasons = [s.lower() for s in seasons]

            # Detect heavy winter outerwear
            if cat == "OUTERWEAR":
                if (
                    any(keyword in sub for keyword in ["parka", "puffer", "down jacket", "heavy coat", "overcoat", "winter coat"]) or
                    (len(seasons) == 1 and "winter" in seasons)
                ):
                    has_heavy_winter_coat = True

            # Detect extreme summer/beach bottoms
            elif cat == "BOTTOMS":
                if (
                    any(keyword in sub for keyword in ["beach short", "boardshort", "swim", "bikini"]) or
                    (any(keyword in sub for keyword in ["shorts", "short"]) and len(seasons) == 1 and "summer" in seasons)
                ):
                    has_beach_swim_shorts = True

        if has_heavy_winter_coat and has_beach_swim_shorts:
            return False, "Absurd combination rejected: Heavy winter coats (parkas/puffers) cannot be layered with beach/swimwear shorts."

        return True, None

    @classmethod
    def _check_formal_shoes_gym_outfit(cls, items: List[Any]) -> Tuple[bool, Optional[str]]:
        """
        Detects formal leather dress shoes paired with a gym outfit (athletic tops/bottoms).
        """
        has_formal_shoes = False
        has_gym_clothing = False

        for item in items:
            cat = cls._get_val(item, "category", "").upper()
            sub = str(cls._get_val(item, "subcategory", "")).lower()
            style = str(cls._get_val(item, "style", "")).lower()
            formality = int(cls._get_val(item, "formality", 3))

            # Detect formal shoes
            if cat == "FOOTWEAR":
                if (
                    formality >= 7 or 
                    style == "formal" or 
                    any(keyword in sub for keyword in ["oxford", "derby", "brogue", "dress shoe", "loafer"])
                ):
                    has_formal_shoes = True

            # Detect gym/activewear tops, bottoms, or outerwear
            elif cat in ("TOPS", "BOTTOMS", "OUTERWEAR"):
                if (
                    formality <= 2 or 
                    style == "athleisure" or 
                    any(keyword in sub for keyword in ["gym", "active", "tracksuit", "sweatpants", "jogger", "track", "sport", "workout"])
                ):
                    has_gym_clothing = True

        if has_formal_shoes and has_gym_clothing:
            return False, "Absurd combination rejected: Formal leather dress shoes cannot be paired with an active/gym wear outfit."

        return True, None

    @classmethod
    def _check_three_loud_patterns(cls, items: List[Any]) -> Tuple[bool, Optional[str]]:
        """
        Prevents visual sensory overload by rejecting outfits with 3 or more patterned (non-solid) garments.
        """
        pattern_count = 0
        loud_patterns = ["striped", "checkered", "graphic", "floral", "plaid", "printed", "camo", "animal", "polka dot", "patterned"]

        for item in items:
            pattern = str(cls._get_val(item, "pattern", "solid")).lower()
            if pattern != "solid" and any(loud in pattern for loud in loud_patterns):
                pattern_count += 1

        if pattern_count >= 3:
            return False, f"Visual overload rejected: Outfit contains {pattern_count} highly patterned items. Keep at least two garments solid to anchor the look."

        return True, None
