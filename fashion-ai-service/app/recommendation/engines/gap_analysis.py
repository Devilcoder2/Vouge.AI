"""
Gap Analysis Engine for Vouge.AI.
Performs hybrid LLM analysis and mathematical wardrobe simulation:
1. Gemini analyzes the user's actual wardrobe to find aesthetic and functional gaps.
2. Gemini dynamically proposes custom target items to buy (categorized with styles, colors, etc.).
3. Our combinatorial engine simulates these proposed items in the user's wardrobe to calculate
   exactly how many outfits they unlock, ranking them for monetization/affiliate styling.
"""
from typing import List, Dict, Any
import logging
import uuid
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings
from app.recommendation.generators.candidate_generator import CandidateGenerator
from app.ai.fashion_taxonomy import CATEGORIES, SUBCATEGORIES, FITS, STYLES, PATTERNS, STANDARD_COLORS

logger = logging.getLogger("fashion-ai-service")

# Pydantic schemas for structured Gemini gap suggestions
class ProposedGapItem(BaseModel):
    name: str = Field(..., description="Descriptive name of the suggested clothing piece to buy (e.g. 'Classic White Linen Shirt')")
    category: str = Field(..., description="Core clothing category (Tops, Bottoms, Outerwear, Shoes, Accessories)")
    subcategory: str = Field(..., description="Specific subcategory of the garment")
    style: str = Field(..., description="Aesthetic style of the item (minimalist, streetwear, classic, formal, athleisure)")
    fit: str = Field(..., description="Fit of the item: slim, standard, or oversized")
    formality: int = Field(..., description="Formality rating integer between 1 and 10", ge=1, le=10)
    seasons: List[str] = Field(..., description="List of suitable seasons: spring, summer, autumn, winter")
    primary_color: str = Field(..., description="Primary standard color name")
    primary_color_hex: str = Field(..., description="Precise matching fabric Hex code")
    pattern: str = Field(..., description="Pattern type (solid, striped, plaid, etc.)")
    reasoning: str = Field(..., description="Personalized stylist reasoning explaining why the user's current closet specifically lacks this category/style and how it helps them.")

class ProposedGapsPayload(BaseModel):
    suggestions: List[ProposedGapItem] = Field(..., description="List of proposed items to buy to complete the wardrobe")

class GapAnalysisEngine:
    @classmethod
    def analyze_gaps(cls, db_items: List[Any]) -> List[Dict[str, Any]]:
        """
        Orchestrates hybrid gap analysis.
        1. Queries Gemini to dynamically propose wardrobe gaps based on the user's actual clothes.
        2. Simulates each proposed item mathematically to calculate unlocked outfit metrics.
        3. Returns ranked suggestions with style tags, unlock counts, and affiliate-ready properties.
        """
        # If the closet is completely empty, suggest initial foundational pieces
        if not db_items:
            return cls._get_default_capsule_suggestions()

        # Step 1: Query Gemini to dynamically generate gap items based on closet contents
        proposed_gaps = cls._query_gemini_for_gaps(db_items)
        
        # Step 2: Calculate baseline count of outfits currently formable (across casual, office, date)
        test_occasions = ["casual", "office", "date"]
        baseline_outfits_count = 0
        for occ in test_occasions:
            baseline_outfits_count += len(CandidateGenerator.generate_candidates(db_items, occ, "spring", max_candidates=200))
            
        final_suggestions: List[Dict[str, Any]] = []

        # Step 3: Run dynamic math simulations on each LLM-proposed item
        for ess in proposed_gaps:
            # Create a mock database-like model instance for the normalizer
            class MockDbItem:
                def __init__(self, d):
                    self.id = uuid.uuid4()
                    self.category = d.category
                    self.subcategory = d.subcategory
                    self.style = d.style
                    self.fit = d.fit
                    self.formality = d.formality
                    self.seasons = d.seasons
                    self.primary_color = d.primary_color
                    self.primary_color_hex = d.primary_color_hex
                    self.secondary_colors = []
                    self.secondary_colors_hex = []
                    self.pattern = d.pattern
                    self.is_duplicate = False
                    self.confidence_category = 1.0
                    self.embedding_path = "mock.npy"
                    self.created_at = None

            mock_item = MockDbItem(ess)
            simulated_closet = list(db_items) + [mock_item]

            # Calculate outfit combinations formed with the simulated item
            sim_outfits_count = 0
            for occ in test_occasions:
                sim_outfits_count += len(CandidateGenerator.generate_candidates(simulated_closet, occ, "spring", max_candidates=200))

            # Outfits unlocked = simulated count minus baseline
            unlocked = max(0, sim_outfits_count - baseline_outfits_count)
            
            # Combine Gemini stylist reasoning with math-proven metrics
            final_reasoning = (
                f"{ess.reasoning} Mathematically, adding this piece to your current wardrobe "
                f"unlocks {unlocked} new outfit combinations across casual, date, and office settings."
            )
            
            final_suggestions.append({
                "item_name": ess.name,
                "category": ess.category,
                "subcategory": ess.subcategory,
                "style": ess.style,
                "fit": ess.fit,
                "formality": ess.formality,
                "primary_color": ess.primary_color,
                "primary_color_hex": ess.primary_color_hex,
                "pattern": ess.pattern,
                "unlocked_outfits_count": unlocked,
                "reasoning": final_reasoning
            })

        # Step 4: Sort recommendations by mathematical unlock counts descending
        final_suggestions.sort(key=lambda x: x["unlocked_outfits_count"], reverse=True)
        return final_suggestions

    @classmethod
    def _query_gemini_for_gaps(cls, db_items: List[Any]) -> List[ProposedGapItem]:
        """
        Sends the user's current closet items to Gemini and requests custom essential additions.
        """
        api_key_configured = (
            settings.GEMINI_API_KEY and 
            settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"
        )
        
        if not api_key_configured:
            logger.warning("OutfitExplainer in Mock Mode: returning default mock gap proposals.")
            return cls._get_mock_gap_items()

        # Build list representing each closet item for Gemini's context
        closet_descriptions = []
        for idx, it in enumerate(db_items):
            closet_descriptions.append(
                f"- Category: {it.category}, Subcategory: {it.subcategory} (Color: {it.primary_color}, Style: {it.style}, Formality: {it.formality}, Seasons: {it.seasons})"
            )

        prompt = f"""
        You are Vouge's Head Personal Stylist and AI Wardrobe Consultant.
        You have been presented with a list of all digitized clothing items currently owned by the user.
        
        Your task:
        1. Deeply analyze the user's closet composition (look for gaps in colors, category imbalances, lack of formal vs casual foundations, weather mismatches).
        2. Propose exactly 5 highly-curated, custom styling pieces for the user to BUY. These items should round out their wardrobe and act as high-value capsule anchors.
        3. For each proposed item, fill out standard database parameters, select appropriate fits, colors, hex codes, and explain exactly why their wardrobe lacks this piece.
        
        Rules:
        - Do NOT suggest items they already have duplicates of. Focus on completing gaps.
        - Categories must map to: {CATEGORIES}.
        - Styles must map to: {STYLES}.
        - Fits must map to: {FITS}.
        - Standard colors must map to: {STANDARD_COLORS}.
        - Respond ONLY in the requested Pydantic JSON structure containing suggestions.
        
        User's Closet Composition:
        {"="*50}
        {"\n".join(closet_descriptions)}
        {"="*50}
        """

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        json_text = ""
        
        # Step 1: Attempt primary model (gemini-2.0-flash)
        try:
            logger.info("Invoking primary model 'gemini-2.0-flash' to analyze wardrobe gaps...")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ProposedGapsPayload,
                    temperature=0.3
                )
            )
            json_text = response.text.strip()
            logger.info("Gemini 2.0 Flash successful for wardrobe gap analysis.")
        except Exception as e:
            err_str = str(e)
            logger.warning(
                f"Primary model 'gemini-2.0-flash' failed to analyze gaps: {err_str[:200]}..."
                "\n[Self-Healing] Dynamically retrying with stable fallback 'gemini-2.5-flash'..."
            )
            # Step 2: Dynamic failover to stable fallback
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ProposedGapsPayload,
                        temperature=0.3
                    )
                )
                json_text = response.text.strip()
                logger.info("Gemini 2.5 Flash fallback successful for wardrobe gap analysis.")
            except Exception as inner_e:
                logger.error(f"Fallback model 'gemini-2.5-flash' also failed to analyze: {str(inner_e)}. Falling back to mock...")
                return cls._get_mock_gap_items()

        try:
            payload_dict = json.loads(json_text)
            suggestions_list = []
            for d in payload_dict.get("suggestions", []):
                suggestions_list.append(ProposedGapItem(**d))
            return suggestions_list
        except Exception as parse_e:
            logger.error(f"Error parsing Gemini gap response: {str(parse_e)}. Falling back to mock items...")
            return cls._get_mock_gap_items()

    @classmethod
    def _get_mock_gap_items(cls) -> List[ProposedGapItem]:
        """Default mock proposed items to buy if LLM is offline."""
        return [
            ProposedGapItem(
                name="Classic White Linen Shirt",
                category="Tops",
                subcategory="Shirts & Blouses",
                style="minimalist",
                fit="standard",
                formality=5,
                seasons=["spring", "summer"],
                primary_color="white",
                primary_color_hex="#ffffff",
                pattern="solid",
                reasoning="A white linen shirt is a vital smart-casual wardrobe pillar that introduces texture and breathability to your summer fits."
            ),
            ProposedGapItem(
                name="Tailored Black Chinos",
                category="Bottoms",
                subcategory="Chinos & Trousers",
                style="classic",
                fit="standard",
                formality=6,
                seasons=["spring", "summer", "autumn", "winter"],
                primary_color="black",
                primary_color_hex="#000000",
                pattern="solid",
                reasoning="These chinos provide a highly-adaptable dressy alternative to blue denim, bridging the gap between casual and corporate settings."
            ),
            ProposedGapItem(
                name="Minimalist White Leather Sneakers",
                category="Shoes",
                subcategory="Sneakers",
                style="minimalist",
                fit="standard",
                formality=4,
                seasons=["spring", "summer", "autumn"],
                primary_color="white",
                primary_color_hex="#ffffff",
                pattern="solid",
                reasoning="Clean white sneakers act as the ultimate footwear baseline, matching easily with both relaxed jeans and formal suit items."
            ),
            ProposedGapItem(
                name="Charcoal Grey Crewneck Sweater",
                category="Tops",
                subcategory="Sweaters & Knitwear",
                style="classic",
                fit="standard",
                formality=5,
                seasons=["autumn", "winter", "spring"],
                primary_color="grey",
                primary_color_hex="#808080",
                pattern="solid",
                reasoning="A grey crewneck knit is a layering anchor, providing core warmth and style synergy under coats or over shirts."
            ),
            ProposedGapItem(
                name="Structured Navy Blazer",
                category="Outerwear",
                subcategory="Blazers & Suit Jackets",
                style="formal",
                fit="standard",
                formality=8,
                seasons=["spring", "autumn", "winter"],
                primary_color="navy",
                primary_color_hex="#000080",
                pattern="solid",
                reasoning="Injects instant structural formality to your silhouette. Perfect for date nights, work, or semi-formal gatherings."
            )
        ]

    @classmethod
    def _get_default_capsule_suggestions(cls) -> List[Dict[str, Any]]:
        """Fallback capsule recommendations for a completely empty wardrobe."""
        mock_items = cls._get_mock_gap_items()
        return [
            {
                "item_name": ess.name,
                "category": ess.category,
                "subcategory": ess.subcategory,
                "style": ess.style,
                "fit": ess.fit,
                "formality": ess.formality,
                "primary_color": ess.primary_color,
                "primary_color_hex": ess.primary_color_hex,
                "pattern": ess.pattern,
                "unlocked_outfits_count": 5,
                "reasoning": f"{ess.reasoning} As your closet is currently empty, this will serve as a core initial styling anchor (+5 capsule outfits)."
            }
            for ess in mock_items
        ]
