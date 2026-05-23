"""
Gemini Stylist Explanation & Reranking Engine for Vouge.AI.
Uses gemini-2.0-flash with structured Pydantic outputs to evaluate and
humanize deterministic outfit recommendations. Features a high-quality mock fallback.
"""
from typing import List, Dict, Any
import logging
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger("fashion-ai-service")

# Pydantic schemas for structured Gemini explanation output
class OutfitExplanationItem(BaseModel):
    index: int = Field(..., description="The original 0-indexed index of the outfit in the input list")
    reranked_score: int = Field(..., description="Reranked outfit score (0-100) adjusted by LLM based on visual style chemistry")
    reasoning: str = Field(..., description="Rich, humanized explanation of why this outfit works and how to style it.")

class OutfitExplanationPayload(BaseModel):
    outfits: List[OutfitExplanationItem] = Field(..., description="List of explanations matching input candidate outfits")

class OutfitExplainer:
    def __init__(self):
        self.api_key_configured = (
            settings.GEMINI_API_KEY and 
            settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"
        )
        
        if self.api_key_configured:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model_name = "gemini-2.0-flash"
            logger.info("OutfitExplainer successfully configured with Google GenAI Live API.")
        else:
            logger.warning("GEMINI_API_KEY not configured. OutfitExplainer operating in MOCK MODE.")

    def explain_recommendations(
        self, 
        candidates: List[Dict[str, Any]], 
        occasion: str, 
        season: str
    ) -> List[Dict[str, Any]]:
        """
        Takes deterministic outfit candidates, feeds them into Gemini,
        receives structured stylist explanations and refined scores, and merges them.
        """
        if not candidates:
            return []
            
        if not self.api_key_configured:
            logger.warning("OutfitExplainer in Mock Mode: generating mock stylist justifications.")
            return self._generate_mock_explanations(candidates, occasion, season)

        # Build list representing each outfit briefly for prompt efficiency
        outfit_prompts = []
        for idx, cand in enumerate(candidates):
            items_str = []
            for it in cand["items"]:
                items_str.append(
                    f"- {it['category']}: {it['subcategory']} ({it['primary_color']}, {it['style']} style, fit: {it['fit']}, formality: {it['formality']})"
                )
            outfit_prompts.append(
                f"Outfit #{idx} (Heuristic Score: {cand['total_score']}):\n" + "\n".join(items_str)
            )

        prompt = f"""
        You are the Editor-in-Chief of a premium fashion editorial and the Head Stylist for Vouge.AI.
        You have been presented with a list of deterministic outfit candidates generated from a user's wardrobe.
        
        Your task:
        1. Review the {len(candidates)} outfit candidates proposed for a {occasion} occasion during {season} weather.
        2. Adjust the scores (0-100) based on expert fashion styling theories (e.g. silhouette proportions, visual weight, color coordination).
        3. Write a stylish, premium, and humanized explanation for *each* outfit. Tell the user *why* these specific items work together and how to carry the look.
        
        Strict Rules:
        - DO NOT invent or add any new clothing items. Rely strictly on the items provided in each outfit.
        - Respond ONLY in the requested Pydantic JSON structure containing explanations and adjusted scores.
        
        Outfit Candidate List:
        {"="*40}
        {"\n\n".join(outfit_prompts)}
        {"="*40}
        """

        json_text = ""
        # Step 1: Attempt generation with primary model (gemini-2.0-flash)
        try:
            logger.info("Invoking primary model 'gemini-2.0-flash' to explain recommendations...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=OutfitExplanationPayload,
                    temperature=0.2
                )
            )
            json_text = response.text.strip()
            logger.info("Gemini 2.0 Flash successful for outfit explanation.")
        except Exception as e:
            err_str = str(e)
            logger.warning(
                f"Primary model 'gemini-2.0-flash' failed to explain: {err_str[:200]}..."
                "\n[Self-Healing] Dynamically retrying with stable fallback 'gemini-2.5-flash'..."
            )
            # Step 2: Dynamic failover to stable fallback
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=OutfitExplanationPayload,
                        temperature=0.2
                    )
                )
                json_text = response.text.strip()
                logger.info("Gemini 2.5 Flash fallback successful for outfit explanation.")
            except Exception as inner_e:
                logger.error(f"Fallback model 'gemini-2.5-flash' also failed to explain: {str(inner_e)}. Falling back to mock...")
                return self._generate_mock_explanations(candidates, occasion, season)

        try:
            payload_dict = json.loads(json_text)
            explanations = {item["index"]: item for item in payload_dict.get("outfits", [])}
            
            # Merge Gemini results back into candidates list
            final_outfits = []
            for idx, cand in enumerate(candidates):
                expl = explanations.get(idx, {
                    "reranked_score": cand["total_score"],
                    "reasoning": "A highly synergistic blend of colors and silhouettes curated for this occasion."
                })
                
                # Construct finalized output object
                outfit_data = {
                    "score": int(expl.get("reranked_score", cand["total_score"])),
                    "items": cand["items"],
                    "reasoning": expl.get("reasoning", "A balanced monochrome palette with clean silhouette."),
                    "template_name": cand["template_name"],
                    "breakdown": cand["breakdown"]
                }
                for k, v in cand.items():
                    if k not in outfit_data:
                        outfit_data[k] = v
                final_outfits.append(outfit_data)
                
            # Re-sort list based on updated LLM scores
            final_outfits.sort(key=lambda x: x["score"], reverse=True)
            return final_outfits
        except Exception as parse_e:
            logger.error(f"Error parsing Gemini response: {str(parse_e)}. Falling back to mock explanations...")
            return self._generate_mock_explanations(candidates, occasion, season)

    def _generate_mock_explanations(
        self, 
        candidates: List[Dict[str, Any]], 
        occasion: str, 
        season: str
    ) -> List[Dict[str, Any]]:
        """Generates premium mock stylist justifications if Gemini is offline."""
        final_outfits = []
        
        for cand in candidates:
            items = cand["items"]
            top = next((it for it in items if it["category"] == "TOPS"), None)
            bottom = next((it for it in items if it["category"] == "BOTTOMS"), None)
            shoe = next((it for it in items if it["category"] == "FOOTWEAR"), None)
            
            top_desc = f"{top['primary_color']} {top['subcategory'].lower()}" if top else "top"
            bottom_desc = f"{bottom['primary_color']} {bottom['subcategory'].lower()}" if bottom else "bottom"
            shoe_desc = f"{shoe['primary_color']} {shoe['subcategory'].lower()}" if shoe else "shoes"
            
            # Formulate occasion-specific rich styling logic
            if occasion.lower() == "date":
                reasoning = (
                    f"This outfit pairs the {top_desc} with the {bottom_desc} to create an elevated yet approachable romantic tone. "
                    f"The {shoe_desc} grounds the look with clean contrast, perfect for a smart-casual dinner or evening outing."
                )
            elif occasion.lower() == "office":
                reasoning = (
                    f"An excellent workplace composition. The structured silhouette of the {top_desc} works beautifully "
                    f"with the clean drape of the {bottom_desc}. Rounded off by the refined {shoe_desc} to maintain professional standards."
                )
            elif occasion.lower() == "gym":
                reasoning = (
                    f"Designed for maximum utility and movement. The breathable comfort of the {top_desc} pairs perfectly "
                    f"with the flexible {bottom_desc}, while the high-grip {shoe_desc} guarantees support during active drills."
                )
            else:
                reasoning = (
                    f"A balanced monochrome palette and clean silhouette. The relaxed drape of the {top_desc} "
                    f"harmonizes beautifully with the {bottom_desc}, creating a timeless {season} aesthetic that is effortless to wear."
                )
                
            outfit_data = {
                "score": cand["total_score"],
                "items": items,
                "reasoning": reasoning,
                "template_name": cand["template_name"],
                "breakdown": cand["breakdown"]
            }
            for k, v in cand.items():
                if k not in outfit_data:
                    outfit_data[k] = v
            final_outfits.append(outfit_data)
            
        return final_outfits

