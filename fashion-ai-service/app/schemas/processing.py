from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# 1. Pydantic schema enforced on the Gemini AI extraction results
class FashionMetadataExtract(BaseModel):
    category: str = Field(
        ..., 
        description="Core clothing category (e.g., 'Tops', 'Bottoms', 'Outerwear', 'Dresses', 'Shoes', 'Accessories')"
    )
    subcategory: str = Field(
        ..., 
        description="Specific subcategory of the garment (e.g., 'T-Shirts & Tanks', 'Jeans', 'Blazers & Suit Jackets', 'Sneakers')"
    )
    fit: str = Field(
        "standard", 
        description="Fit of the item: 'slim', 'standard', or 'oversized'"
    )
    style: str = Field(
        "minimal", 
        description="Aesthetic style of the item (e.g., 'minimalist', 'streetwear', 'classic', 'formal', 'athleisure')"
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
    pattern: str = Field(
        "solid", 
        description="Pattern type (e.g., 'solid', 'striped', 'plaid', 'floral', 'graphic', 'distressed')"
    )
    primary_color: str = Field(
        ...,
        description="The primary dominant color of the garment. Must map to standard fashion colors: 'white', 'black', 'grey', 'beige', 'cream', 'navy', 'blue', 'light_blue', 'olive', 'green', 'red', 'maroon', 'pink', 'orange', 'yellow', 'purple', 'brown'"
    )
    secondary_colors: List[str] = Field(
        default_factory=list,
        description="List of secondary or accent colors visible on the garment. Choose from the same standard color list."
    )

# 2. Main API response structure for processed clothing items
class ProcessedClothingResponse(BaseModel):
    id: UUID
    category: str
    subcategory: str
    primary_color: str
    primary_color_hex: str
    secondary_colors: List[str]
    secondary_colors_hex: List[str]
    fit: str
    style: str
    formality: int
    seasons: List[str]
    pattern: str
    processed_image_url: str
    embedding_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True

# 3. Simple health check schema
class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
