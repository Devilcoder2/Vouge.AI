"""
Unit tests for the centralized Hard Validation Firewall (RecommendationGuardrails)
of the Vouge.AI outfit recommendation engine.
"""
import pytest
import uuid
from app.recommendation.rules.recommendation_guardrails import RecommendationGuardrails
from app.recommendation.generators.candidate_generator import CandidateGenerator

class MockGarment:
    """Helper mock representing a clothing item for guardrail evaluation."""
    def __init__(self, category, subcategory, style, formality, seasons, pattern):
        self.id = uuid.uuid4()
        self.category = category
        self.subcategory = subcategory
        self.style = style
        self.formality = formality
        self.seasons = seasons
        self.pattern = pattern

def test_tuxedo_gym_shorts_rejection():
    """
    Verifies that Tuxedo + Gym Shorts (formal top/outerwear + gym/activewear bottoms)
    is successfully blocked by the firewall.
    """
    # 1. Formal Blazer (formality 9) + Athletic Shorts (formality 2)
    blazer = MockGarment("TOPS", "Tuxedo Jacket & Blazers", "formal", 9, ["spring", "autumn", "winter"], "solid")
    gym_shorts = MockGarment("BOTTOMS", "Gym Shorts", "athleisure", 1, ["summer"], "solid")
    shoes = MockGarment("FOOTWEAR", "Sneakers", "streetwear", 3, ["spring", "summer", "autumn", "winter"], "solid")
    
    outfit = [blazer, gym_shorts, shoes]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit)
    assert not is_valid
    assert "blazer/tuxedo" in reason.lower()

    # 2. Formal Blazer as Outerwear + Sweatpants
    top = MockGarment("TOPS", "T-Shirts", "minimal", 3, ["spring", "summer"], "solid")
    outer = MockGarment("OUTERWEAR", "Blazers & Jackets", "formal", 8, ["autumn", "winter"], "solid")
    sweatpants = MockGarment("BOTTOMS", "Sweatpants & Joggers", "athleisure", 2, ["winter"], "solid")
    
    outfit_2 = [top, outer, sweatpants, shoes]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit_2)
    assert not is_valid
    assert "athletic" in reason.lower()

def test_winter_parka_beach_shorts_rejection():
    """
    Verifies that Winter Parka + Beach Shorts (extreme weather conflicts)
    is successfully blocked by the firewall.
    """
    top = MockGarment("TOPS", "T-Shirts", "minimal", 3, ["summer"], "solid")
    parka = MockGarment("OUTERWEAR", "Parka Jackets & Heavy Coats", "classic", 5, ["winter"], "solid")
    boardshorts = MockGarment("BOTTOMS", "Boardshorts & Beachwear", "athleisure", 1, ["summer"], "solid")
    shoes = MockGarment("FOOTWEAR", "Sandals", "minimal", 1, ["summer"], "solid")

    outfit = [top, parka, boardshorts, shoes]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit)
    assert not is_valid
    assert "heavy winter coats" in reason.lower()

def test_formal_leather_shoes_gym_outfit_rejection():
    """
    Verifies that Formal Leather Shoes + Gym Outfit is successfully blocked by the firewall.
    """
    # Oxford Shoes + Gym Shorts + T-Shirt
    oxford = MockGarment("FOOTWEAR", "Oxfords & Derbys", "formal", 9, ["spring", "autumn", "winter"], "solid")
    gym_shorts = MockGarment("BOTTOMS", "Athletic Active Shorts", "athleisure", 2, ["summer"], "solid")
    top = MockGarment("TOPS", "Gym Tee", "athleisure", 2, ["summer"], "solid")

    outfit = [oxford, gym_shorts, top]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit)
    assert not is_valid
    assert "formal leather dress shoes" in reason.lower()

def test_three_loud_patterned_items_rejection():
    """
    Verifies that outfits containing 3 or more non-solid loud patterns are blocked to avoid sensory overload.
    """
    striped_top = MockGarment("TOPS", "Striped Tee", "minimal", 3, ["spring", "summer"], "striped")
    checked_bottom = MockGarment("BOTTOMS", "Checkered Pants", "streetwear", 4, ["autumn"], "checkered")
    floral_outer = MockGarment("OUTERWEAR", "Floral Bomber", "vintage", 4, ["spring"], "floral")
    shoes = MockGarment("FOOTWEAR", "Sneakers", "streetwear", 3, ["spring", "summer", "autumn", "winter"], "solid")

    outfit = [striped_top, checked_bottom, floral_outer, shoes]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit)
    assert not is_valid
    assert "visual overload" in reason.lower()

def test_safe_clean_outfits_allowed():
    """
    Verifies that standard, stylish, non-absurd outfits pass through the firewall successfully.
    """
    # 1. Everyday Casual Look (Tee + Jeans + Sneakers)
    top = MockGarment("TOPS", "Basic T-Shirt", "minimal", 3, ["summer"], "solid")
    bottom = MockGarment("BOTTOMS", "Jeans", "minimal", 4, ["spring", "autumn", "winter"], "solid")
    shoes = MockGarment("FOOTWEAR", "Sneakers", "streetwear", 3, ["spring", "summer", "autumn", "winter"], "solid")
    
    outfit_1 = [top, bottom, shoes]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit_1)
    assert is_valid
    assert reason is None

    # 2. Smart Office Look (Oxford Shirt + Chinos + Blazers + Loafers)
    shirt = MockGarment("TOPS", "Dress Shirts", "classic", 6, ["spring", "autumn", "winter"], "solid")
    chinos = MockGarment("BOTTOMS", "Chinos & Trousers", "classic", 6, ["spring", "autumn", "winter"], "solid")
    blazer = MockGarment("OUTERWEAR", "Blazers & Jackets", "formal", 8, ["spring", "autumn", "winter"], "solid")
    loafers = MockGarment("FOOTWEAR", "Loafers & Slip-ons", "classic", 6, ["spring", "summer", "autumn"], "solid")

    outfit_2 = [shirt, chinos, blazer, loafers]
    is_valid, reason = RecommendationGuardrails.is_valid_outfit(outfit_2)
    assert is_valid
    assert reason is None
