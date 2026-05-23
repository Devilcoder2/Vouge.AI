"""
Gap Analysis Engine for Vouge.AI.
Simulates adding ideal wardrobe essentials to the user's current closet
and calculates how many new outfit combinations are unlocked by each item.
"""
from typing import List, Dict, Any
import logging
import uuid
from app.recommendation.generators.candidate_generator import CandidateGenerator
from app.recommendation.rules.fashion_taxonomy import CATEGORY_MAP

logger = logging.getLogger("fashion-ai-service")

# A curated master list of high-value fashion essentials to test as gaps
ESSENTIALS: List[Dict[str, Any]] = [
    {
        "name": "Classic White T-Shirt",
        "category": "Tops",
        "subcategory": "T-Shirts & Tanks",
        "style": "minimalist",
        "fit": "standard",
        "formality": 3,
        "seasons": ["spring", "summer", "autumn", "winter"],
        "primary_color": "white",
        "primary_color_hex": "#ffffff",
        "pattern": "solid"
    },
    {
        "name": "Classic Blue Denim Jeans",
        "category": "Bottoms",
        "subcategory": "Jeans",
        "style": "classic",
        "fit": "standard",
        "formality": 4,
        "seasons": ["spring", "summer", "autumn", "winter"],
        "primary_color": "blue",
        "primary_color_hex": "#1e3a8a",
        "pattern": "solid"
    },
    {
        "name": "Minimalist White Sneakers",
        "category": "Shoes",
        "subcategory": "Sneakers",
        "style": "minimalist",
        "fit": "standard",
        "formality": 3,
        "seasons": ["spring", "summer", "autumn"],
        "primary_color": "white",
        "primary_color_hex": "#ffffff",
        "pattern": "solid"
    },
    {
        "name": "Tailored Black Blazer",
        "category": "Outerwear",
        "subcategory": "Blazers & Suit Jackets",
        "style": "formal",
        "fit": "standard",
        "formality": 8,
        "seasons": ["spring", "autumn", "winter"],
        "primary_color": "black",
        "primary_color_hex": "#000000",
        "pattern": "solid"
    },
    {
        "name": "Classic Black Trousers",
        "category": "Bottoms",
        "subcategory": "Chinos & Trousers",
        "style": "classic",
        "fit": "standard",
        "formality": 6,
        "seasons": ["spring", "summer", "autumn", "winter"],
        "primary_color": "black",
        "primary_color_hex": "#000000",
        "pattern": "solid"
    },
    {
        "name": "Cream Knit Turtleneck",
        "category": "Tops",
        "subcategory": "Turtlenecks",
        "style": "minimalist",
        "fit": "standard",
        "formality": 5,
        "seasons": ["autumn", "winter", "spring"],
        "primary_color": "cream",
        "primary_color_hex": "#fffdd0",
        "pattern": "solid"
    }
]

class GapAnalysisEngine:
    @classmethod
    def analyze_gaps(cls, db_items: List[Any]) -> List[Dict[str, Any]]:
        """
        Runs wardrobe simulations using essential items to rank gaps by outfit unlocking potential.
        """
        if not db_items:
            # If wardrobe is empty, every essential unlocks standard combinations
            return [
                {
                    "item_name": ess["name"],
                    "category": ess["category"],
                    "primary_color": ess["primary_color"],
                    "unlocked_outfits_count": 5,
                    "reasoning": f"An empty wardrobe benefit: adding a {ess['name']} builds your initial clothing capsule."
                }
                for ess in ESSENTIALS
            ]

        # 1. Benchmark baseline: calculate how many outfits can be formed right now
        # We test across three core target occasions
        test_occasions = ["casual", "office", "date"]
        baseline_outfits_count = 0
        for occ in test_occasions:
            baseline_outfits_count += len(CandidateGenerator.generate_candidates(db_items, occ, "spring", max_candidates=200))
            
        suggestions: List[Dict[str, Any]] = []

        # 2. Simulate adding each essential item individually
        for ess in ESSENTIALS:
            # Create a mock database-like model instance for the normalizer
            class MockDbItem:
                def __init__(self, d):
                    self.id = uuid.uuid4()
                    self.category = d["category"]
                    self.subcategory = d["subcategory"]
                    self.style = d["style"]
                    self.fit = d["fit"]
                    self.formality = d["formality"]
                    self.seasons = d["seasons"]
                    self.primary_color = d["primary_color"]
                    self.primary_color_hex = d["primary_color_hex"]
                    self.secondary_colors = []
                    self.secondary_colors_hex = []
                    self.pattern = d["pattern"]
                    self.is_duplicate = False
                    self.confidence_category = 1.0
                    self.embedding_path = "mock.npy"
                    self.created_at = None

            mock_item = MockDbItem(ess)
            simulated_closet = list(db_items) + [mock_item]

            # Calculate how many outfits are formed with the simulated item
            sim_outfits_count = 0
            for occ in test_occasions:
                sim_outfits_count += len(CandidateGenerator.generate_candidates(simulated_closet, occ, "spring", max_candidates=200))

            # Outfits unlocked = simulated count minus baseline
            unlocked = max(0, sim_outfits_count - baseline_outfits_count)
            
            # Formulate stylist suggestion explanation
            reasoning = (
                f"Adding a {ess['name']} in {ess['primary_color']} unlocks {unlocked} new outfit combinations "
                f"across casual, date, and office categories, functioning as a vital anchor piece."
            )
            
            suggestions.append({
                "item_name": ess["name"],
                "category": ess["category"],
                "primary_color": ess["primary_color"],
                "unlocked_outfits_count": unlocked,
                "reasoning": reasoning
            })

        # Sort suggestions by unlocking potential descending
        suggestions.sort(key=lambda x: x["unlocked_outfits_count"], reverse=True)
        return suggestions
