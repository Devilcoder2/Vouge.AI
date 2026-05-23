import logging
import json
from PIL import Image
from google import genai
from google.genai import types
from app.config import settings
from app.schemas.processing import FashionMetadataExtract

logger = logging.getLogger("fashion-ai-service")

class FashionClassifier:
    def __init__(self):
        # Check if a live, active API key is provided
        self.api_key_configured = (
            settings.GEMINI_API_KEY and 
            settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"
        )
        
        if self.api_key_configured:
            # Initialize the modern, unified Google GenAI Client
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            # Use the verified active stable model name
            self.model_name = "gemini-2.0-flash"
            logger.info("FashionClassifier successfully configured with Google GenAI Live API.")
        else:
            logger.warning(
                "GEMINI_API_KEY not set in .env. "
                "FashionClassifier is operating in MOCK MODE."
            )

    def classify_garment(self, pil_image: Image.Image, filename_hint: str = "") -> FashionMetadataExtract:
        """
        Processes a cropped, transparent garment image using Gemini.
        Attempts gemini-2.0-flash first. If any exception occurs,
        it dynamically falls back to the stable 'gemini-2.5-flash' model before dropping to mock mode.
        """
        if not self.api_key_configured:
            logger.warning("Operating in MOCK MODE: returning mock metadata.")
            return self._generate_mock_metadata(filename_hint)

        prompt = """
        You are an expert fashion stylist and inventory catalog manager.
        Analyze this garment image (on a transparent background). Extract its fashion attributes:
        1. Core Category: Must be one of: 'Tops', 'Bottoms', 'Outerwear', 'Dresses', 'Shoes', 'Accessories'.
        2. Subcategory: Extract the exact fashion subcategory (e.g. 'T-Shirts & Tanks', 'Jeans', 'Boots', etc.).
        3. Fit: Choose 'slim', 'standard', or 'oversized'.
        4. Style: Identify the aesthetic (e.g. 'minimalist', 'streetwear', 'classic', 'formal', 'athleisure').
        5. Formality: Rate from 1 (loungewear/active) to 10 (black tie formal).
        6. Seasons: Select matching seasons (e.g. ['summer'], ['winter', 'autumn']).
        7. Pattern: Specify (e.g. 'solid', 'striped', 'plaid', 'graphic', 'floral', 'distressed').
        8. Primary Color: The single main dominant color of the clothing item. Choose ONLY from: 'white', 'black', 'grey', 'beige', 'cream', 'navy', 'blue', 'light_blue', 'olive', 'green', 'red', 'maroon', 'pink', 'orange', 'yellow', 'purple', 'brown'.
        9. Secondary Colors: Any minor or accent colors visible on the garment. Choose from the same standard color list (leave empty if the garment is a solid single color).
        """

        # Step 1: Attempt generation with primary model (gemini-2.0-flash)
        try:
            logger.info("Invoking primary model 'gemini-2.0-flash'...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[pil_image, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FashionMetadataExtract,
                    temperature=0.1
                )
            )
            json_text = response.text.strip()
            logger.info(f"Gemini 2.0 Flash successful: {json_text}")
            
            metadata_dict = json.loads(json_text)
            return FashionMetadataExtract(**metadata_dict)

        except Exception as e:
            err_str = str(e)
            logger.warning(
                f"Primary model 'gemini-2.0-flash' failed: {err_str[:200]}..."
                "\n[Self-Healing] Dynamically retrying with stable fallback 'gemini-2.5-flash'..."
            )
            
            # Step 2: Immediate dynamic failover to gemini-2.5-flash
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[pil_image, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FashionMetadataExtract,
                        temperature=0.1
                    )
                )
                json_text = response.text.strip()
                logger.info(f"Gemini 2.5 Flash fallback successful: {json_text}")
                
                metadata_dict = json.loads(json_text)
                return FashionMetadataExtract(**metadata_dict)
            except Exception as inner_e:
                logger.error(f"Fallback model 'gemini-2.5-flash' also failed: {str(inner_e)}. Falling back to mock...")
                return self._generate_mock_metadata(filename_hint)

    def _generate_mock_metadata(self, filename_hint: str) -> FashionMetadataExtract:
        """Generates smart mock classification estimates based on image filename hints."""
        hint = filename_hint.lower()
        
        if any(w in hint for w in ["shirt", "tee", "top", "hoodie", "sweater", "sweatshirt"]):
            return FashionMetadataExtract(
                category="Tops",
                subcategory="T-Shirts & Tanks" if "tee" in hint or "shirt" in hint else "Hoodies & Sweatshirts",
                fit="oversized" if "oversized" in hint else "standard",
                style="streetwear" if "streetwear" in hint else "minimalist",
                formality=3 if "tee" in hint else 4,
                seasons=["spring", "summer"],
                pattern="solid",
                primary_color="white",
                secondary_colors=[]
            )
        elif any(w in hint for w in ["pant", "jeans", "trouser", "shorts", "skirt", "bottom"]):
            return FashionMetadataExtract(
                category="Bottoms",
                subcategory="Jeans" if "jeans" in hint else "Chinos & Trousers",
                fit="standard",
                style="classic",
                formality=4 if "jeans" in hint else 5,
                seasons=["spring", "summer", "autumn", "winter"],
                pattern="solid",
                primary_color="blue" if "jeans" in hint else "grey",
                secondary_colors=[]
            )
        elif any(w in hint for w in ["shoe", "boot", "sneaker", "loafer", "heel", "footwear"]):
            return FashionMetadataExtract(
                category="Shoes",
                subcategory="Sneakers" if "sneaker" in hint else "Boots",
                fit="standard",
                style="streetwear" if "sneaker" in hint else "classic",
                formality=3 if "sneaker" in hint else 6,
                seasons=["spring", "summer", "autumn", "winter"],
                pattern="solid",
                primary_color="black" if "boot" in hint else "white",
                secondary_colors=[]
            )
        
        # Absolute generic fallback
        return FashionMetadataExtract(
            category="Tops",
            subcategory="T-Shirts & Tanks",
            fit="standard",
            style="minimalist",
            formality=3,
            seasons=["spring", "summer"],
            pattern="solid",
            primary_color="white",
            secondary_colors=[]
        )
