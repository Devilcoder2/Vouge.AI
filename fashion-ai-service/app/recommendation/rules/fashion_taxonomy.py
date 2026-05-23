"""
Centralized Fashion Taxonomy rules for the Vouge.AI outfit recommendation engines.
Standardizes allowed enums and categories to ensure recommendation logic consistency.
"""
from typing import Dict, List

# Allowed categories mapped from pipeline categories
CATEGORIES: List[str] = [
    "TOPS",
    "BOTTOMS",
    "FOOTWEAR",
    "OUTERWEAR",
    "ACCESSORIES"
]

# Normalization mapping from raw database categories to recommendation taxonomy
CATEGORY_MAP: Dict[str, str] = {
    "Tops": "TOPS",
    "Bottoms": "BOTTOMS",
    "Outerwear": "OUTERWEAR",
    "Dresses": "TOPS",  # Dresses function as tops/full outfits in basic templates
    "Shoes": "FOOTWEAR",
    "Accessories": "ACCESSORIES",
    # Handles already normalized terms
    "TOPS": "TOPS",
    "BOTTOMS": "BOTTOMS",
    "FOOTWEAR": "FOOTWEAR",
    "OUTERWEAR": "OUTERWEAR",
    "ACCESSORIES": "ACCESSORIES"
}

# Allowed aesthetic styles
STYLES: List[str] = [
    "minimal",
    "streetwear",
    "formal",
    "classic",
    "smart_casual",
    "athleisure",
    "vintage"
]

# Normalization mapping for styles
STYLE_MAP: Dict[str, str] = {
    "minimalist": "minimal",
    "minimal": "minimal",
    "streetwear": "streetwear",
    "formal": "formal",
    "classic": "classic",
    "smart_casual": "smart_casual",
    "athleisure": "athleisure",
    "vintage": "vintage",
    "grunge": "streetwear",
    "preppy": "classic",
    "bohemian": "vintage",
    "chic": "minimal"
}

# Allowed fits
FITS: List[str] = [
    "slim",
    "regular",
    "relaxed",
    "oversized",
    "tailored"
]

# Normalization mapping for fits
FIT_MAP: Dict[str, str] = {
    "slim": "slim",
    "standard": "regular",
    "regular": "regular",
    "relaxed": "relaxed",
    "oversized": "oversized",
    "tailored": "tailored"
}

# Allowed seasons
SEASONS: List[str] = ["spring", "summer", "autumn", "winter"]

# Allowed occasion types
OCCASIONS: List[str] = [
    "casual",
    "office",
    "date",
    "party",
    "travel",
    "gym",
    "wedding",
    "formal_event"
]

# Occasion formality ranges (min, max) on our 1-10 scale
OCCASION_FORMALITY_MAP: Dict[str, tuple] = {
    "gym": (1, 2),
    "travel": (2, 4),
    "casual": (3, 5),
    "party": (4, 7),
    "date": (5, 8),
    "office": (6, 8),
    "wedding": (8, 10),
    "formal_event": (9, 10)
}
