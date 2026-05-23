"""
Style Persona Engine for Vouge.AI recommendations.
Audits outfit candidates against specific user styling identities (personas)
like minimalist, old_money, quiet_luxury, streetwear, techwear, smart_casual, and avant_garde.
"""
from typing import List, Dict, Any

class StylePersonaEngine:
    @classmethod
    def calculate_persona_compatibility(
        cls,
        items: List[Dict[str, Any]],
        persona: str
    ) -> Dict[str, Any]:
        """
        Scores outfit compatibility (0.0 to 1.0) against a specific style persona.
        """
        if not items or not persona:
            return {"score": 1.0, "reason": "No style persona or items provided for analysis.", "why_selected": []}

        persona_lower = persona.lower()
        score = 1.0
        boosts = 0.0
        penalties = 0.0
        reasons = []
        why_selected = []

        for it in items:
            it_cat = it.get("category", "").upper()
            it_subcat = it.get("subcategory", "").lower()
            it_style = it.get("style", "").lower()
            it_fit = it.get("fit", "").lower()
            it_color = it.get("primary_color", "").lower()
            it_pattern = it.get("pattern", "").lower()

            # Normalize standard fit to regular fit
            normalized_fit = "regular" if it_fit == "standard" else it_fit

            # Standard Neutors List
            neutral_anchors = {"white", "black", "grey", "beige", "cream", "navy", "olive", "brown"}

            # 1. Old Money / Quiet Luxury Persona
            if persona_lower in ["old_money", "quiet_luxury"]:
                # Loves classic styles, neutrals, shirts, knitwear, trousers, blazers
                if it_style == "classic" or it_style == "minimalist":
                    boosts += 0.08
                if it_color in neutral_anchors:
                    boosts += 0.04
                if it_pattern == "solid":
                    boosts += 0.04
                if it_subcat in ["shirts & blouses", "chinos & trousers", "sweaters & knitwear", "blazers & suit jackets", "loafers & slip-ons", "oxfords & derby shoes"]:
                    boosts += 0.08
                
                # Penalizes graphics, excessive activewear/sneakers, streetwear tags, oversized fits
                if it_style in ["streetwear", "athleisure"] or it_pattern in ["graphic", "distressed"]:
                    penalties += 0.15
                    reasons.append(f"Streetwear / graphic aesthetic of {it_subcat} clashes with {persona.replace('_', ' ')} refinement.")
                if normalized_fit == "oversized":
                    penalties += 0.05

            # 2. Streetwear Persona
            elif persona_lower == "streetwear":
                # Loves relaxed/oversized fits, streetwear styles, cargo, hoodies, t-shirts, sneakers, graphic/plaid patterns
                if it_style == "streetwear" or it_style == "athleisure":
                    boosts += 0.10
                if normalized_fit == "oversized" or normalized_fit == "relaxed":
                    boosts += 0.08
                if it_pattern in ["graphic", "camo", "plaid"]:
                    boosts += 0.06
                if it_subcat in ["t-shirts & tanks", "hoodies & sweatshirts", "sweatpants & joggers", "sneakers", "boots"]:
                    boosts += 0.08

                # Penalizes extremely formal attire (blazers, oxfords, suit trousers, formal style)
                if it_style == "formal" or it_subcat in ["blazers & suit jackets", "oxfords & derby shoes"]:
                    penalties += 0.12
                    reasons.append(f"Formal drape of {it_subcat} clashes with streetwear comfort.")

            # 3. Minimalist Persona
            elif persona_lower == "minimalist":
                # Loves pure neutrals, absolute solid patterns, clean minimalist styling
                if it_style == "minimalist" or it_style == "classic":
                    boosts += 0.10
                if it_color in neutral_anchors:
                    boosts += 0.06
                if it_pattern == "solid":
                    boosts += 0.08
                
                # Penalizes patterns like camo, plaid, distressed, graphics, and neon/clashing styling
                if it_pattern in ["graphic", "camo", "plaid", "distressed", "striped"]:
                    penalties += 0.12
                    reasons.append(f"Patterned {it_subcat} goes against minimalist solid norms.")

            # 4. Techwear Persona
            elif persona_lower == "techwear":
                # Loves utility colors (black, grey, olive), synthetic/cargo categories
                if it_color in ["black", "grey", "olive"]:
                    boosts += 0.08
                if "cargo" in it_subcat or it_subcat in ["hoodies & sweatshirts", "windbreakers", "boots", "sneakers"]:
                    boosts += 0.10
                if it_style in ["athleisure", "streetwear"]:
                    boosts += 0.06

                # Penalizes classic, formal tailoring (linen, blazers, dress shoes)
                if it_style == "formal" or it_subcat in ["blazers & suit jackets", "oxfords & derby shoes", "loafers & slip-ons"]:
                    penalties += 0.15
                    reasons.append(f"Classic structured {it_subcat} does not fit techwear utility.")

            # 5. Avant Garde Persona
            elif persona_lower == "avant_garde":
                # Loves oversized fits, asymmetrical/unconventional shapes, solid dark black
                if normalized_fit == "oversized":
                    boosts += 0.12
                if it_color == "black":
                    boosts += 0.08
                if it_style in ["avant_garde", "minimalist", "streetwear"]:
                    boosts += 0.06

        final_score = max(0.0, min(1.0, score + boosts - penalties))

        if boosts > penalties:
            why_selected.append(f"Perfect match for your preferred {persona.replace('_', ' ')} aesthetic.")

        return {
            "score": final_score,
            "reason": "; ".join(reasons) if reasons else f"Outfit aligns beautifully with your {persona.replace('_', ' ')} identity.",
            "why_selected": why_selected
        }
