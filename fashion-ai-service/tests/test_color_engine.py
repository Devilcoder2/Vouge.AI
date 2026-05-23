import pytest
from app.recommendation.engines.color_engine import ColorEngine
from app.recommendation.rules.color_rules import NEUTRALS, VIVIDS

def test_classic_synergistic_pairs():
    """Verifies that classic high-synergy fashion combinations score extremely high (>= 0.95)."""
    synergy_pairs = [
        ("black", "#000000", "white", "#ffffff"),
        ("navy", "#000080", "cream", "#fffdd0"),
        ("blue", "#0000ff", "beige", "#f5f5dc"),
        ("olive", "#808000", "cream", "#fffdd0"),
        ("grey", "#808080", "pink", "#ffc0cb"),
        ("brown", "#a52a2a", "beige", "#f5f5dc")
    ]
    
    for c_a, h_a, c_b, h_b in synergy_pairs:
        res = ColorEngine.calculate_compatibility(c_a, h_a, c_b, h_b)
        assert res["score"] >= 0.95, f"Expected high synergy for {c_a} + {c_b}, got {res['score']}"
        assert "harmony" in res["reason"] or "complement" in res["reason"] or "neutral" in res["reason"]

def test_clashing_pairs():
    """Verifies that high-contrast clashing color pairs are penalized severely (<= 0.40)."""
    clash_pairs = [
        ("red", "#ff0000", "green", "#00ff00"),
        ("orange", "#ffa500", "purple", "#800080"),
        ("pink", "#ffc0cb", "yellow", "#ffff00"),
        ("red", "#ff0000", "orange", "#ffa500"),
        ("green", "#00ff00", "purple", "#800080")
    ]
    
    for c_a, h_a, c_b, h_b in clash_pairs:
        res = ColorEngine.calculate_compatibility(c_a, h_a, c_b, h_b)
        assert res["score"] <= 0.40, f"Expected clash penalty for {c_a} + {c_b}, got {res['score']}"
        assert "clash" in res["reason"]

def test_near_contrast_mismatch():
    """Verifies that nearly identical shades that are not the same color are flagged as near-miss clashes."""
    # Dark navy (#000020) next to black (#000000)
    res_navy_black = ColorEngine.calculate_compatibility("navy", "#000015", "black", "#000000")
    assert res_navy_black["score"] <= 0.70
    assert "near-miss" in res_navy_black["reason"]

    # Off-beige next to cream (very close Delta-E)
    res_cream_beige = ColorEngine.calculate_compatibility("cream", "#fffdda", "beige", "#fcf8dc")
    # Should be flagged as near-miss clash due to very low Delta-E distance
    assert "near-miss" in res_cream_beige["reason"]

def test_monochromatic_harmony():
    """Verifies that same-color pairs receive high ratings, particularly for neutrals."""
    res_white = ColorEngine.calculate_compatibility("white", "#ffffff", "white", "#f5f5f5")
    assert res_white["score"] >= 0.95
    assert "monochromatic" in res_white["reason"]

def test_color_engine_matrix_grid():
    """
    Dynamically tests 100+ color combinations across a grid of standard fashion colors
    to verify absolute stability, ensuring no NaNs, infinite scores, or out-of-bound values.
    """
    colors = [
        ("white", "#ffffff"),
        ("black", "#000000"),
        ("grey", "#808080"),
        ("beige", "#f5f5dc"),
        ("cream", "#fffdd0"),
        ("navy", "#000080"),
        ("blue", "#0000ff"),
        ("light_blue", "#add8e6"),
        ("olive", "#808000"),
        ("green", "#008000"),
        ("red", "#ff0000"),
        ("maroon", "#800000"),
        ("pink", "#ffc0cb"),
        ("orange", "#ffa500"),
        ("yellow", "#ffff00"),
        ("purple", "#800080"),
        ("brown", "#a52a2a")
    ]
    
    pair_count = 0
    for i in range(len(colors)):
        for j in range(len(colors)):
            c_a, h_a = colors[i]
            c_b, h_b = colors[j]
            
            res = ColorEngine.calculate_compatibility(c_a, h_a, c_b, h_b)
            pair_count += 1
            
            # Assert mathematical bounds
            assert 0.0 <= res["score"] <= 1.0, f"Score out of bounds for {c_a} + {c_b}: {res['score']}"
            assert isinstance(res["reason"], str)
            assert len(res["reason"]) > 0
            
    # Verify we evaluated 17 x 17 = 289 pairs (exceeding the 100+ target)
    assert pair_count == 289
    print(f"\nSuccessfully verified compatibility scores for {pair_count} color coordinates.")
