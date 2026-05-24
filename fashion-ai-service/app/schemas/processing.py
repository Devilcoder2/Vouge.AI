from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# A nested field for classification attributes containing a value and confidence score
class ConfidenceStringField(BaseModel):
    value: str = Field(..., description="The classified value of the attribute")
    confidence: float = Field(..., description="The LLM confidence score between 0.0 and 1.0", ge=0.0, le=1.0)

# 1. Pydantic schema enforced on the Gemini AI extraction results
class FashionMetadataExtract(BaseModel):
    category: ConfidenceStringField = Field(
        ..., 
        description="Core clothing category (Tops, Bottoms, Outerwear, Dresses, Shoes, Accessories) and confidence."
    )
    subcategory: ConfidenceStringField = Field(
        ..., 
        description="Specific subcategory of the garment and confidence."
    )
    fit: ConfidenceStringField = Field(
        ..., 
        description="Fit of the item: 'slim', 'standard', or 'oversized' and confidence."
    )
    style: ConfidenceStringField = Field(
        ..., 
        description="Aesthetic style of the item (e.g. 'minimalist', 'streetwear', 'classic', 'formal', 'athleisure') and confidence."
    )
    pattern: ConfidenceStringField = Field(
        ..., 
        description="Pattern type (e.g., 'solid', 'striped', 'plaid', 'floral', 'graphic', 'distressed') and confidence."
    )
    formality: int = Field(
        3, 
        description="Formality rating integer between 1 (lounge/sleepwear) and 10 (black tie/formal suit)",
        ge=1,
        le=10
    )
    seasons: List[str] = Field(
        ..., 
        description="List of seasons suitable for this item: 'spring', 'summer', 'autumn', 'winter'"
    )
    primary_color: str = Field(
        ...,
        description="The primary dominant color of the garment. Choose strictly from: 'white', 'black', 'grey', 'beige', 'cream', 'navy', 'blue', 'light_blue', 'olive', 'green', 'red', 'maroon', 'pink', 'orange', 'yellow', 'purple', 'brown'"
    )
    secondary_colors: List[str] = Field(
        default_factory=list,
        description="List of secondary colors from standard list."
    )
    detected_items_count: int = Field(
        1,
        description="Count of distinct clothing items detected in the image. e.g., 1 for a single shirt, 3 for an outfit with a shirt, pants, and shoes."
    )

# 2. Main API response structure for processed clothing items
class ProcessedClothingResponse(BaseModel):
    id: UUID
    category: ConfidenceStringField
    subcategory: ConfidenceStringField
    primary_color: str
    primary_color_hex: str
    secondary_colors: List[str]
    secondary_colors_hex: List[str]
    fit: ConfidenceStringField
    style: ConfidenceStringField
    formality: int
    seasons: List[str]
    pattern: ConfidenceStringField
    processed_image_url: str
    embedding_generated: bool
    is_duplicate: bool
    duplicate_of_id: Optional[UUID] = None
    perceptual_hash: Optional[str] = None
    prompt_version: str

    detected_items_count: int
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def from_orm_custom(cls, data):
        """
        Dynamically packs the flat DB fields into the structured nested response format.
        """
        if not isinstance(data, dict):
            # Map from SQLAlchemy ORM object attributes
            category_val = getattr(data, "category", "")
            category_conf = float(getattr(data, "confidence_category", 1.0) or 1.0)
            
            subcategory_val = getattr(data, "subcategory", "")
            subcategory_conf = float(getattr(data, "confidence_subcategory", 1.0) or 1.0)
            
            fit_val = getattr(data, "fit", "standard")
            fit_conf = float(getattr(data, "confidence_fit", 1.0) or 1.0)
            
            style_val = getattr(data, "style", "minimal")
            style_conf = float(getattr(data, "confidence_style", 1.0) or 1.0)
            
            pattern_val = getattr(data, "pattern", "solid")
            pattern_conf = float(getattr(data, "confidence_pattern", 1.0) or 1.0)
            
            return {
                "id": data.id,
                "category": {"value": category_val, "confidence": category_conf},
                "subcategory": {"value": subcategory_val, "confidence": subcategory_conf},
                "primary_color": data.primary_color,
                "primary_color_hex": data.primary_color_hex or "#ffffff",
                "secondary_colors": data.secondary_colors or [],
                "secondary_colors_hex": data.secondary_colors_hex or [],
                "fit": {"value": fit_val, "confidence": fit_conf},
                "style": {"value": style_val, "confidence": style_conf},
                "formality": data.formality,
                "seasons": data.seasons or [],
                "pattern": {"value": pattern_val, "confidence": pattern_conf},
                "processed_image_url": f"/processed/{data.id}_processed.png",
                "embedding_generated": True,
                "is_duplicate": getattr(data, "is_duplicate", False),
                "duplicate_of_id": getattr(data, "duplicate_of_id", None),
                "perceptual_hash": getattr(data, "perceptual_hash", None),
                "prompt_version": getattr(data, "prompt_version", "v1.0.0"),
                "detected_items_count": getattr(data, "detected_items_count", 1),
                "created_at": data.created_at,
            }

        return data

    class Config:
        from_attributes = True

# 3. Simple health check schema
class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database_connected: bool

# 4. Schema for manual metadata correction requests (PATCH /items/{id})
class ClothingItemPatchRequest(BaseModel):
    category: Optional[str] = Field(None, description="Corrected high-level category")
    subcategory: Optional[str] = Field(None, description="Corrected subcategory")
    fit: Optional[str] = Field(None, description="Corrected fit ('slim', 'standard', 'oversized')")
    style: Optional[str] = Field(None, description="Corrected aesthetic style")
    primary_color: Optional[str] = Field(None, description="Corrected primary color name")
    primary_color_hex: Optional[str] = Field(None, description="Corrected primary color hex code")
    secondary_colors: Optional[List[str]] = Field(None, description="Corrected secondary color names")
    secondary_colors_hex: Optional[List[str]] = Field(None, description="Corrected secondary color hex codes")
    pattern: Optional[str] = Field(None, description="Corrected pattern type")
    formality: Optional[int] = Field(None, description="Corrected formality rating (1-10)", ge=1, le=10)
    seasons: Optional[List[str]] = Field(None, description="Corrected seasons suitability list")
