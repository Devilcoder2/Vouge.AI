import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from uuid import UUID

from app.database.session import get_db
from app.database.models import ClothingItem
from app.schemas.processing import (
    ProcessedClothingResponse, 
    HealthCheckResponse,
    ClothingItemPatchRequest
)
from app.utils.file_handler import FileHandler
from app.services.pipeline import FashionIntelligencePipeline

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(tags=["Clothing Processing"])
pipeline = FashionIntelligencePipeline()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Validates api status and verifies active PostgreSQL async database connection."""
    db_connected = False
    try:
        # Simple test query to check PostgreSQL connectivity
        await db.execute(select(1))
        db_connected = True
    except Exception as e:
        # Log database connectivity issues
        logger.error(f"Database health check failed: {str(e)}")
        
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        database_connected=db_connected
    )

@router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_image_only(file: UploadFile = File(...)):
    """
    Step 4 Requirement: Uploads raw image, validates size and extensions, 
    saves to local disk, and returns file path.
    """
    try:
        raw_path = await FileHandler.save_upload(file)
        return {
            "message": "Raw image uploaded successfully.",
            "filename": file.filename,
            "saved_path": str(raw_path)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post(
    "/process-clothing", 
    response_model=ProcessedClothingResponse, 
    status_code=status.HTTP_201_CREATED
)
async def process_clothing_image(
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    Step 11 End-to-End Requirement: Receives image, removes background, pre-processes,
    classifies via Gemini, extracts dominant colors, computes CLIP embeddings, 
    and persists all metadata to PostgreSQL.
    """
    processed_item = await pipeline.process_new_clothing(file, db)
    
    # Return structured nested confidence response
    return ProcessedClothingResponse.model_validate(processed_item)

@router.get("/items/{item_id}", response_model=ProcessedClothingResponse)
async def get_clothing_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves processed garment records from PostgreSQL by UUID."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clothing item with ID '{item_id}' not found."
        )
        
    return ProcessedClothingResponse.model_validate(item)


@router.get("/items", response_model=List[ProcessedClothingResponse])
async def list_wardrobe_items(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = Query(
        None,
        description="Filter by category. One of: Tops, Bottoms, Outerwear, Shoes, Accessories"
    ),
    include_duplicates: bool = Query(
        False,
        description="If false (default), excludes items flagged as duplicates from the results."
    )
):
    """
    Returns all clothing items in the wardrobe.
    Supports optional filtering by category and duplicate exclusion.
    Results are ordered newest-first by upload date.
    """
    stmt = select(ClothingItem).order_by(ClothingItem.created_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all()

    # Filter by category if specified
    if category:
        items = [it for it in items if it.category.lower() == category.lower()]

    # Exclude duplicates unless explicitly requested
    if not include_duplicates:
        items = [it for it in items if not it.is_duplicate]

    return [ProcessedClothingResponse.model_validate(it) for it in items]


@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
async def delete_clothing_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently deletes a clothing item from the wardrobe by UUID.
    Also removes its associated processed image and embedding files from disk.
    """
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clothing item with ID '{item_id}' not found."
        )

    # Clean up associated files from disk
    from pathlib import Path
    for path_attr in ("processed_image_path", "original_image_path", "embedding_path"):
        file_path = getattr(item, path_attr, None)
        if file_path:
            FileHandler.delete_file(Path(file_path))

    await db.delete(item)
    await db.commit()

    logger.info(f"Clothing item {item_id} deleted from wardrobe.")
    return {"message": f"Item '{item_id}' successfully deleted from your wardrobe."}

@router.patch("/items/{item_id}", response_model=ProcessedClothingResponse)
async def patch_clothing_item(
    item_id: UUID,
    payload: ClothingItemPatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 5 Requirement: Metadata Correction Layer (PATCH /items/{id}).
    Allows manual override/corrections of category, subcategory, colors, fit, style, seasons, pattern, formality.
    These manual corrections overlay the model predictions and flag user corrections.
    """
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clothing item with ID '{item_id}' not found."
        )
        
    # Merge existing data and payload data for taxonomy validation
    test_category = payload.category if payload.category is not None else item.category
    test_subcategory = payload.subcategory if payload.subcategory is not None else item.subcategory
    test_fit = payload.fit if payload.fit is not None else item.fit
    test_style = payload.style if payload.style is not None else item.style
    test_seasons = payload.seasons if payload.seasons is not None else item.seasons
    test_pattern = payload.pattern if payload.pattern is not None else item.pattern
    test_primary_color = payload.primary_color if payload.primary_color is not None else item.primary_color
    test_secondary_colors = payload.secondary_colors if payload.secondary_colors is not None else item.secondary_colors
    
    # Strictly validate against Central Fashion Taxonomy
    from app.ai.fashion_taxonomy import validate_taxonomy
    try:
        validate_taxonomy(
            category=test_category,
            subcategory=test_subcategory,
            fit=test_fit,
            style=test_style,
            seasons=test_seasons,
            pattern=test_pattern,
            primary_color=test_primary_color,
            secondary_colors=test_secondary_colors
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Taxonomy validation failed: {str(ve)}"
        )

    # Apply patch updates and set confidence to 1.0 (since they represent manual ground truth corrections)
    if payload.category is not None:
        item.category = payload.category
        item.confidence_category = 1.0
    if payload.subcategory is not None:
        item.subcategory = payload.subcategory
        item.confidence_subcategory = 1.0
    if payload.fit is not None:
        item.fit = payload.fit
        item.confidence_fit = 1.0
    if payload.style is not None:
        item.style = payload.style
        item.confidence_style = 1.0
    if payload.pattern is not None:
        item.pattern = payload.pattern
        item.confidence_pattern = 1.0
        
    if payload.formality is not None:
        item.formality = payload.formality
    if payload.seasons is not None:
        item.seasons = payload.seasons
        
    if payload.primary_color is not None:
        item.primary_color = payload.primary_color
    if payload.primary_color_hex is not None:
        item.primary_color_hex = payload.primary_color_hex
    if payload.secondary_colors is not None:
        item.secondary_colors = payload.secondary_colors
    if payload.secondary_colors_hex is not None:
        item.secondary_colors_hex = payload.secondary_colors_hex

    await db.commit()
    await db.refresh(item)
    
    logger.info(f"User manually corrected metadata for clothing item: {item.id}")
    return ProcessedClothingResponse.model_validate(item)
