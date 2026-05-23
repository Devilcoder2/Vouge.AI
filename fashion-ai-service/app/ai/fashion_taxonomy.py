"""
Centralized Fashion Taxonomy configuration for the Vouge.AI wardrobe platform.
Serves as the single source of truth for allowed categories, subcategories, fits, styles, patterns, and colors.
"""
from typing import Dict, List

# Allowed high-level categories
CATEGORIES: List[str] = [
    "Tops",
    "Bottoms",
    "Outerwear",
    "Dresses",
    "Shoes",
    "Accessories"
]

# Mapping of categories to their allowed subcategories
SUBCATEGORIES: Dict[str, List[str]] = {
    "Tops": [
        "T-Shirts & Tanks",
        "Shirts & Blouses",
        "Hoodies & Sweatshirts",
        "Sweaters & Knitwear",
        "Polos",
        "Crops & Tanks",
        "Turtlenecks"
    ],
    "Bottoms": [
        "Jeans",
        "Chinos & Trousers",
        "Shorts",
        "Skirts",
        "Sweatpants & Joggers",
        "Leggings"
    ],
    "Outerwear": [
        "Blazers & Suit Jackets",
        "Coats & Trenches",
        "Jackets & Bombers",
        "Vests",
        "Cardigans"
    ],
    "Dresses": [
        "Casual Dresses",
        "Formal Dresses",
        "Jumpsuits & Rompers"
    ],
    "Shoes": [
        "Sneakers",
        "Boots",
        "Dress Shoes & Oxfords",
        "Loafers & Slip-ons",
        "Sandals & Slides",
        "Heels"
    ],
    "Accessories": [
        "Bags & Backpacks",
        "Belts",
        "Hats & Caps",
        "Scarves & Gloves",
        "Sunglasses",
        "Jewelry",
        "Watches"
    ]
}

# Allowed fits
FITS: List[str] = ["slim", "standard", "oversized"]

# Allowed aesthetic styles
STYLES: List[str] = [
    "minimalist",
    "streetwear",
    "classic",
    "formal",
    "athleisure",
    "vintage",
    "bohemian",
    "chic",
    "grunge",
    "preppy"
]

# Allowed seasons
SEASONS: List[str] = ["spring", "summer", "autumn", "winter"]

# Allowed pattern types
PATTERNS: List[str] = [
    "solid",
    "striped",
    "plaid",
    "floral",
    "graphic",
    "distressed",
    "checkered",
    "camo",
    "polka_dot",
    "animal_print",
    "tie_dye"
]

# Allowed standard color names
STANDARD_COLORS: List[str] = [
    "white",
    "black",
    "grey",
    "beige",
    "cream",
    "navy",
    "blue",
    "light_blue",
    "olive",
    "green",
    "red",
    "maroon",
    "pink",
    "orange",
    "yellow",
    "purple",
    "brown"
]

def validate_taxonomy(category: str, subcategory: str, fit: str, style: str, seasons: List[str], pattern: str, primary_color: str, secondary_colors: List[str]) -> bool:
    """
    Validates a set of clothing metadata attributes against the master taxonomy.
    Returns True if valid, raises ValueError if any attribute violates the taxonomy.
    """
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Allowed categories: {CATEGORIES}")
    
    allowed_subs = SUBCATEGORIES.get(category, [])
    if subcategory not in allowed_subs:
        raise ValueError(f"Invalid subcategory '{subcategory}' for category '{category}'. Allowed subcategories: {allowed_subs}")
    
    if fit not in FITS:
        raise ValueError(f"Invalid fit '{fit}'. Allowed fits: {FITS}")
        
    if style not in STYLES:
        raise ValueError(f"Invalid style '{style}'. Allowed styles: {STYLES}")
        
    for season in seasons:
        if season not in SEASONS:
            raise ValueError(f"Invalid season '{season}'. Allowed seasons: {SEASONS}")
            
    if pattern not in PATTERNS:
        raise ValueError(f"Invalid pattern '{pattern}'. Allowed patterns: {PATTERNS}")
        
    if primary_color not in STANDARD_COLORS:
        raise ValueError(f"Invalid primary color '{primary_color}'. Allowed colors: {STANDARD_COLORS}")
        
    for sc in secondary_colors:
        if sc not in STANDARD_COLORS:
            raise ValueError(f"Invalid secondary color '{sc}'. Allowed colors: {STANDARD_COLORS}")
            
    return True
