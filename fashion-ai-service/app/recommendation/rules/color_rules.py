"""
Fashion Color rules and harmonies for Vouge.AI recommendations.
Defines standard color palettes, neutrals, complementary rules, and clash penalties.
"""
from typing import Dict, List, Set

# Central lists of neutral anchor colors
NEUTRALS: Set[str] = {
    "white",
    "black",
    "grey",
    "beige",
    "cream",
    "navy",
    "olive",
    "brown"
}

# Vivid / saturated primary or secondary color classifications
VIVIDS: Set[str] = {
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "light_blue",
    "purple",
    "pink",
    "maroon"
}

# Standard complementary/synergistic color relationships (highly stylish matches)
COLOR_SYNERGY: Dict[str, Set[str]] = {
    "blue": {"beige", "cream", "white", "grey", "orange", "brown", "navy"},
    "light_blue": {"white", "beige", "cream", "navy", "grey", "pink", "olive"},
    "olive": {"cream", "beige", "black", "pink", "white", "navy", "grey", "brown"},
    "navy": {"cream", "beige", "grey", "white", "maroon", "red", "light_blue", "brown"},
    "black": {"white", "grey", "red", "blue", "light_blue", "beige", "cream", "pink", "olive", "navy", "purple"},
    "white": {"black", "navy", "grey", "blue", "light_blue", "olive", "maroon", "pink", "green", "beige", "cream", "purple"},
    "cream": {"navy", "olive", "brown", "grey", "black", "light_blue", "maroon", "pink"},
    "beige": {"navy", "olive", "brown", "grey", "black", "light_blue", "maroon", "pink"},
    "maroon": {"navy", "cream", "beige", "grey", "white", "black", "pink"},
    "pink": {"white", "grey", "navy", "olive", "black", "cream", "beige"},
    "grey": {"white", "black", "navy", "blue", "light_blue", "pink", "red", "cream", "beige"},
    "brown": {"cream", "beige", "navy", "olive", "white", "black", "light_blue"},
    "red": {"black", "white", "navy", "grey"},
    "orange": {"navy", "blue", "white", "grey", "black"},
    "yellow": {"black", "navy", "grey", "white"},
    "green": {"white", "grey", "black", "beige", "cream", "navy"},
    "purple": {"black", "white", "grey", "beige", "cream"}
}

# Clashing color combinations (stylistically risky pairings that receive penalties)
CLASHING_PAIRS: Set[tuple] = {
    # Red and green clash (looks like Christmas costume unless planned)
    ("red", "green"), ("green", "red"),
    # Vivid orange and bright purple
    ("orange", "purple"), ("purple", "orange"),
    # Bright pink and bright yellow
    ("pink", "yellow"), ("yellow", "pink"),
    # Red and orange (too close on wheel and intense)
    ("red", "orange"), ("orange", "red"),
    # Yellow and neon-ish orange
    ("yellow", "orange"), ("orange", "yellow"),
    # Bright green and bright purple
    ("green", "purple"), ("purple", "green")
}

def get_color_compatibility_score(color_a: str, color_b: str) -> tuple:
    """
    Computes a base heuristic compatibility score (0.0 to 1.0) and a reason
    for any pair of standard colors.
    """
    color_a = color_a.lower()
    color_b = color_b.lower()
    
    # 1. Identity match (Monochromatic harmony)
    if color_a == color_b:
        if color_a in NEUTRALS:
            return 0.95, "elegant monochromatic neutral balance"
        return 0.80, "monochromatic style (requires texture contrast)"
        
    # 2. Perfect Synergistic Complements
    if color_b in COLOR_SYNERGY.get(color_a, set()):
        return 0.98, "high-synergy classic color complement"
        
    # 3. Double Neutral Anchor
    if color_a in NEUTRALS and color_b in NEUTRALS:
        return 0.92, "stable double-neutral styling foundation"
        
    # 4. Single Neutral Anchor + Vivid Accent
    if (color_a in NEUTRALS and color_b in VIVIDS) or (color_b in NEUTRALS and color_a in VIVIDS):
        return 0.85, "balanced neutral with vibrant focal accent"
        
    # 5. Direct Clashing Match
    if (color_a, color_b) in CLASHING_PAIRS:
        return 0.30, "clashing color combo (stylistically conflicting high-contrast)"
        
    # 6. Default Vivid + Vivid combination (somewhat risky)
    return 0.60, "moderate pairing (vivid blocks require balancing neutrals)"
