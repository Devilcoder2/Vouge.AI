"""
Outfit Template definitions for Vouge.AI.
Establishes standardized combinations (slots) for various occasion dress codes,
ensuring combinatorial generation is aesthetically structured and fast.
"""
from typing import List, Dict, Set

class OutfitTemplate:
    def __init__(
        self, 
        name: str, 
        occasions: Set[str], 
        required_slots: List[str], 
        optional_slots: List[str] = None,
        subcat_restrictions: Dict[str, List[str]] = None,
        formality_range: tuple = (1, 10)
    ):
        self.name = name
        self.occasions = occasions
        self.required_slots = required_slots
        self.optional_slots = optional_slots or []
        self.subcat_restrictions = subcat_restrictions or {}
        self.formality_range = formality_range

# Define standard templates matching various fashion contexts
TEMPLATES: List[OutfitTemplate] = [
    # 1. Casual Basic Template: TOPS + BOTTOMS + FOOTWEAR (with optional outerwear/accessories)
    OutfitTemplate(
        name="casual_basic",
        occasions={"casual", "travel", "party", "date"},
        required_slots=["TOPS", "BOTTOMS", "FOOTWEAR"],
        optional_slots=["OUTERWEAR", "ACCESSORIES"],
        subcat_restrictions={
            "FOOTWEAR": ["Sneakers", "Loafers & Slip-ons", "Sandals & Slides", "Boots"]
        },
        formality_range=(2, 6)
    ),
    
    # 2. Smart Casual/Date: TOPS + BOTTOMS + FOOTWEAR (elevated shoes & shirts)
    OutfitTemplate(
        name="smart_casual",
        occasions={"date", "office", "party"},
        required_slots=["TOPS", "BOTTOMS", "FOOTWEAR"],
        optional_slots=["OUTERWEAR", "ACCESSORIES"],
        subcat_restrictions={
            "TOPS": ["Shirts & Blouses", "Polos", "Sweaters & Knitwear", "Turtlenecks"],
            "BOTTOMS": ["Chinos & Trousers", "Jeans", "Skirts"],
            "FOOTWEAR": ["Loafers & Slip-ons", "Dress Shoes & Oxfords", "Boots", "Sneakers"]
        },
        formality_range=(5, 8)
    ),
    
    # 3. Office Professional: TOPS + BOTTOMS + FOOTWEAR + OUTERWEAR (Blazers, Chinos, etc.)
    OutfitTemplate(
        name="office_professional",
        occasions={"office", "formal_event"},
        required_slots=["TOPS", "BOTTOMS", "FOOTWEAR"],
        optional_slots=["OUTERWEAR", "ACCESSORIES"],
        subcat_restrictions={
            "TOPS": ["Shirts & Blouses", "Turtlenecks", "Polos"],
            "BOTTOMS": ["Chinos & Trousers", "Skirts"],
            "FOOTWEAR": ["Dress Shoes & Oxfords", "Loafers & Slip-ons", "Heels", "Boots"],
            "OUTERWEAR": ["Blazers & Suit Jackets", "Coats & Trenches"]
        },
        formality_range=(6, 9)
    ),
    
    # 4. Winter Layered: Layered top + warm outerwear
    OutfitTemplate(
        name="winter_layered",
        occasions={"casual", "travel", "office"},
        required_slots=["TOPS", "OUTERWEAR", "BOTTOMS", "FOOTWEAR"],
        optional_slots=["ACCESSORIES"],
        subcat_restrictions={
            "TOPS": ["Sweaters & Knitwear", "Hoodies & Sweatshirts", "Turtlenecks", "Shirts & Blouses"],
            "OUTERWEAR": ["Coats & Trenches", "Jackets & Bombers", "Cardigans"],
            "FOOTWEAR": ["Boots", "Sneakers", "Dress Shoes & Oxfords"]
        },
        formality_range=(3, 8)
    ),
    
    # 5. Gym Active: Athleisure tops & bottoms & sneakers
    OutfitTemplate(
        name="gym_active",
        occasions={"gym", "travel"},
        required_slots=["TOPS", "BOTTOMS", "FOOTWEAR"],
        optional_slots=["ACCESSORIES"],
        subcat_restrictions={
            "TOPS": ["T-Shirts & Tanks", "Crops & Tanks", "Hoodies & Sweatshirts"],
            "BOTTOMS": ["Sweatpants & Joggers", "Leggings", "Shorts"],
            "FOOTWEAR": ["Sneakers"]
        },
        formality_range=(1, 3)
    ),

    # 6. Ultra Formal: Black Tie / Suit Setups
    OutfitTemplate(
        name="ultra_formal",
        occasions={"wedding", "formal_event"},
        required_slots=["TOPS", "BOTTOMS", "FOOTWEAR"],
        optional_slots=["OUTERWEAR", "ACCESSORIES"],
        subcat_restrictions={
            "TOPS": ["Shirts & Blouses", "Turtlenecks"],
            "BOTTOMS": ["Chinos & Trousers", "Skirts"],
            "FOOTWEAR": ["Dress Shoes & Oxfords", "Heels", "Loafers & Slip-ons"],
            "OUTERWEAR": ["Blazers & Suit Jackets", "Coats & Trenches"]
        },
        formality_range=(8, 10)
    )
]

def get_templates_for_occasion(occasion: str) -> List[OutfitTemplate]:
    """Finds all standard template configurations that support the target occasion."""
    occ = occasion.lower()
    matches = [t for t in TEMPLATES if occ in t.occasions]
    # Fallback to casual basic if no match found
    if not matches:
        matches = [TEMPLATES[0]]
    return matches
