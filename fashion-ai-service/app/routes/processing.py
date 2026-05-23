from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.database.session import get_db
from app.database.models import ClothingItem
from app.schemas.processing import (
    ProcessedClothingResponse, 
    HealthCheckResponse
)
from app.utils.file_handler import FileHandler
from app.services.pipeline import FashionIntelligencePipeline

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
        import logging
        logging.getLogger("fashion-ai-service").error(f"Database health check failed: {str(e)}")
        
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
    
    # Render static path to local file for display in Swagger UI
    # In production, this would resolve to a CDN / S3 Pre-signed URL
    return ProcessedClothingResponse(
        id=processed_item.id,
        category=processed_item.category,
        subcategory=processed_item.subcategory,
        primary_color=processed_item.primary_color,
        primary_color_hex=processed_item.primary_color_hex or "#ffffff",
        secondary_colors=processed_item.secondary_colors,
        secondary_colors_hex=processed_item.secondary_colors_hex or [],
        fit=processed_item.fit,
        style=processed_item.style,
        formality=processed_item.formality,
        seasons=processed_item.seasons,
        pattern=processed_item.pattern,
        processed_image_url=f"/processed/{processed_item.id}_processed.png",
        embedding_generated=True,
        created_at=processed_item.created_at
    )

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
        
    return ProcessedClothingResponse(
        id=item.id,
        category=item.category,
        subcategory=item.subcategory,
        primary_color=item.primary_color,
        primary_color_hex=item.primary_color_hex or "#ffffff",
        secondary_colors=item.secondary_colors,
        secondary_colors_hex=item.secondary_colors_hex or [],
        fit=item.fit,
        style=item.style,
        formality=item.formality,
        seasons=item.seasons,
        pattern=item.pattern,
        processed_image_url=f"/processed/{item.id}_processed.png",
        embedding_generated=True,
        created_at=item.created_at
    )
