import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, update, delete, func, or_, and_, text, cast, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.auth.dependencies import bearer_scheme
from app.auth.security import decode_access_token
from app.database.models import User, ClothingItem, SavedOutfit, WardrobeCategory, WardrobeHistory
from app.database.session import get_db
from app.schemas.wardrobe import (
    PaginationMeta,
    CategoryResponse,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    SecondaryColor,
    WardrobeItemResponse,
    WardrobeItemCreateRequest,
    WardrobeItemUpdateRequest,
    PaginatedItemResponse,
    WardrobeStatsResponse,
    WardrobeHistoryResponse,
    PaginatedHistoryResponse,
    ScanImageResponse,
)
from app.services.storage_service import storage_service

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/api/wardrobe", tags=["Digital Wardrobe"])


# ── Optional Auth Dependency ────────────────────────────────────────────────

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication dependency.
    If a valid JWT is supplied, returns the active User object.
    Otherwise, returns None silently, preserving fallback compatibility.
    """
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


# ── Helper Utilities ─────────────────────────────────────────────────────────

def slugify(text_val: str) -> str:
    """Generates a clean URL slug from input text."""
    text_val = text_val.lower().strip()
    text_val = re.sub(r"[^\w\s-]", "", text_val)
    text_val = re.sub(r"[\s_-]+", "-", text_val)
    return text_val


def get_relative_time_label(dt: datetime) -> str:
    """Computes a dynamic relative time label (e.g. '2 hours ago')."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    diff = now - dt

    if diff.total_seconds() < 0:
        return "Just now"

    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(seconds // 3600)
    days = diff.days

    if seconds < 60:
        return "Just now"
    elif minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif hours < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y")


def map_clothing_item_to_response(item: ClothingItem) -> WardrobeItemResponse:
    """Maps internal ClothingItem database model to WardrobeItemResponse schema."""
    # 1. Name fallback
    name = item.name
    if not name:
        name = f"{item.primary_color} {item.subcategory}".title()

    # 2. Textile fallback
    textile = item.textile or "Cotton Blend"

    # 3. Secondary Colors mapping
    sec_colors = []
    names = item.secondary_colors or []
    hexes = item.secondary_colors_hex or []
    for i in range(max(len(names), len(hexes))):
        c_name = names[i] if i < len(names) else "Unknown"
        c_hex = hexes[i] if i < len(hexes) else "#000000"
        sec_colors.append(SecondaryColor(name=c_name, hex=c_hex))

    # 4. Occasion fallback
    occasion = item.occasion
    if not occasion:
        if item.formality >= 7:
            occasion = "evening"
        elif item.formality >= 4:
            occasion = "work"
        else:
            occasion = "casual"

    # 5. Image URL fallback
    image_url = item.processed_image_url
    if not image_url:
        image_url = item.original_image_url
    if not image_url:
        if item.processed_image_path:
            image_url = f"/v1/media/file/processed/{Path(item.processed_image_path).name}"
        elif item.original_image_path:
            image_url = f"/v1/media/file/raw/{Path(item.original_image_path).name}"

    # 6. Categories tag list fallback
    categories = item.categories
    if not categories:
        categories = [item.category.lower()]

    return WardrobeItemResponse(
        id=item.id,
        name=name,
        textile=textile,
        colorName=item.primary_color,
        colorHex=item.primary_color_hex or "#000000",
        secondaryColors=sec_colors,
        moreDetails=item.more_details or f"A stylish {item.fit} fit {item.style} garment perfect for various occasions.",
        occasion=occasion,
        image=image_url,
        verified=item.verified or False,
        long=item.long or False,
        hasAIService=item.has_ai_service or False,
        categories=categories,
    )


# ── Categories Endpoints ────────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryResponse], status_code=status.HTTP_200_OK)
async def list_categories(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns list of categories. Calculates dynamic count of items belonging to 
    each category matching containment rules.
    """
    query = select(WardrobeCategory)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                WardrobeCategory.name.ilike(search_term),
                WardrobeCategory.subtitle.ilike(search_term)
            )
        )
    result = await db.execute(query)
    categories = result.scalars().all()
    
    response = []
    for cat in categories:
        count_query = select(func.count(ClothingItem.id)).where(
            or_(
                cast(ClothingItem.categories, PG_ARRAY(String)).contains([cat.id]),
                and_(
                    ClothingItem.categories.is_(None),
                    func.lower(ClothingItem.category) == cat.id
                )
            )
        )
        item_count = await db.scalar(count_query) or 0
        
        response.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            subtitle=cat.subtitle,
            status=cat.status,
            image=cat.image,
            count=item_count
        ))
    return response


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new digital closet category/collection."""
    cat_id = slugify(payload.name)
    if not cat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name must contain valid alphanumeric characters."
        )
        
    # Uniqueness check
    existing = await db.execute(
        select(WardrobeCategory).where(
            or_(
                WardrobeCategory.id == cat_id,
                WardrobeCategory.name.ilike(payload.name)
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{payload.name}' or ID '{cat_id}' already exists."
        )
        
    new_cat = WardrobeCategory(
        id=cat_id,
        name=payload.name,
        subtitle=payload.subtitle,
        image=payload.image,
        status="active"
    )
    db.add(new_cat)
    await db.commit()
    await db.refresh(new_cat)
    
    return CategoryResponse(
        id=new_cat.id,
        name=new_cat.name,
        subtitle=new_cat.subtitle,
        status=new_cat.status,
        image=new_cat.image,
        count=0
    )


@router.get("/categories/{categoryId}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def get_category(
    categoryId: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetches category detail metadata by slug ID."""
    result = await db.execute(select(WardrobeCategory).where(WardrobeCategory.id == categoryId))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{categoryId}' not found."
        )
        
    count_query = select(func.count(ClothingItem.id)).where(
        or_(
            cast(ClothingItem.categories, PG_ARRAY(String)).contains([categoryId]),
            and_(
                ClothingItem.categories.is_(None),
                func.lower(ClothingItem.category) == categoryId
            )
        )
    )
    item_count = await db.scalar(count_query) or 0
    
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        subtitle=cat.subtitle,
        status=cat.status,
        image=cat.image,
        count=item_count
    )


@router.put("/categories/{categoryId}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def update_category(
    categoryId: str,
    payload: CategoryUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Updates digital closet category properties."""
    result = await db.execute(select(WardrobeCategory).where(WardrobeCategory.id == categoryId))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{categoryId}' not found."
        )
        
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != cat.name:
        existing = await db.execute(
            select(WardrobeCategory).where(
                and_(
                    WardrobeCategory.name.ilike(update_data["name"]),
                    WardrobeCategory.id != categoryId
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another category with name '{update_data['name']}' already exists."
            )
            
    for field, value in update_data.items():
        setattr(cat, field, value)
        
    await db.commit()
    await db.refresh(cat)
    
    count_query = select(func.count(ClothingItem.id)).where(
        or_(
            cast(ClothingItem.categories, PG_ARRAY(String)).contains([categoryId]),
            and_(
                ClothingItem.categories.is_(None),
                func.lower(ClothingItem.category) == categoryId
            )
        )
    )
    item_count = await db.scalar(count_query) or 0
    
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        subtitle=cat.subtitle,
        status=cat.status,
        image=cat.image,
        count=item_count
    )


@router.delete("/categories/{categoryId}", status_code=status.HTTP_200_OK)
async def delete_category(
    categoryId: str,
    cleanup: str = Query("keep_orphans", enum=["keep_orphans", "delete_items"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes category slug row. If cleanup=delete_items, deletes items contained within. 
    Otherwise trims containment tags cleanly.
    """
    result = await db.execute(select(WardrobeCategory).where(WardrobeCategory.id == categoryId))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{categoryId}' not found."
        )
        
    if cleanup == "delete_items":
        delete_items_query = delete(ClothingItem).where(
            or_(
                cast(ClothingItem.categories, PG_ARRAY(String)).contains([categoryId]),
                and_(
                    ClothingItem.categories.is_(None),
                    func.lower(ClothingItem.category) == categoryId
                )
            )
        )
        await db.execute(delete_items_query)
    else:
        # PostgreSQL array_remove to cleanly trim containment
        await db.execute(text("""
            UPDATE clothing_items 
            SET categories = array_remove(categories, :cat_id) 
            WHERE :cat_id = ANY(categories);
        """), {"cat_id": categoryId})
        
        # Cleanup fallback legacy tags
        await db.execute(text("""
            UPDATE clothing_items
            SET categories = '{}'
            WHERE categories IS NULL AND LOWER(category) = :cat_id;
        """), {"cat_id": categoryId.lower()})

    await db.delete(cat)
    await db.commit()
    
    return {"success": True, "message": f"Category '{categoryId}' successfully deleted."}


# ── Wardrobe Items Endpoints ────────────────────────────────────────────────

@router.get("/items", response_model=PaginatedItemResponse, status_code=status.HTTP_200_OK)
async def list_wardrobe_items(
    categoryId: Optional[str] = None,
    search: Optional[str] = None,
    occasion: Optional[str] = None,
    verified: Optional[bool] = None,
    hasAIService: Optional[bool] = None,
    sortBy: str = Query("created_at", enum=["name", "created_at", "formality"]),
    sortOrder: str = Query("desc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Flat wardrobe item list with search, robust custom filters, sorting, and pagination."""
    query = select(ClothingItem)
    
    # 1. Category Filter
    if categoryId:
        query = query.where(
            or_(
                cast(ClothingItem.categories, PG_ARRAY(String)).contains([categoryId]),
                and_(
                    ClothingItem.categories.is_(None),
                    func.lower(ClothingItem.category) == categoryId.lower()
                )
            )
        )
        
    # 2. Case-insensitive Search (substring against name, subcategory, primary color, details)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                ClothingItem.name.ilike(search_term),
                ClothingItem.textile.ilike(search_term),
                ClothingItem.more_details.ilike(search_term),
                ClothingItem.subcategory.ilike(search_term),
                ClothingItem.primary_color.ilike(search_term),
            )
        )
        
    # 3. Occasion Filter (exact match or formality fallback mapping)
    if occasion:
        query = query.where(
            or_(
                ClothingItem.occasion.ilike(occasion),
                and_(
                    ClothingItem.occasion.is_(None),
                    ClothingItem.formality >= (7 if occasion.lower() == "evening" else 4 if occasion.lower() == "work" else 0)
                )
            )
        )
        
    # 4. Verified Filter
    if verified is not None:
        query = query.where(ClothingItem.verified == verified)
        
    # 5. hasAIService Filter
    if hasAIService is not None:
        query = query.where(ClothingItem.has_ai_service == hasAIService)

    # Compute Total Count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    
    # Apply Sorting Columns
    sort_col = ClothingItem.created_at
    if sortBy == "name":
        sort_col = func.coalesce(ClothingItem.name, ClothingItem.primary_color)
    elif sortBy == "formality":
        sort_col = ClothingItem.formality
        
    if sortOrder == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())
        
    # Apply Pagination Offset
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Envelop paginated response
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    meta = PaginationMeta(
        currentPage=page,
        pageSize=limit,
        totalPages=total_pages,
        totalCount=total_count,
        hasNextPage=page < total_pages,
        hasPrevPage=page > 1
    )
    
    data = [map_clothing_item_to_response(item) for item in items]
    return PaginatedItemResponse(data=data, meta=meta)


@router.post("/items", response_model=WardrobeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_wardrobe_item(
    payload: WardrobeItemCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Registers manual custom wardrobe items directly into closet database."""
    sec_names = [color.name for color in payload.secondaryColors]
    sec_hexes = [color.hex for color in payload.secondaryColors]
    
    legacy_cat = payload.categories[0] if payload.categories else "tops"
    unique_id = uuid.uuid4()
    
    new_item = ClothingItem(
        id=unique_id,
        name=payload.name,
        textile=payload.textile or "Cotton Blend",
        primary_color=payload.colorName,
        primary_color_hex=payload.colorHex,
        secondary_colors=sec_names,
        secondary_colors_hex=sec_hexes,
        more_details=payload.moreDetails,
        occasion=payload.occasion,
        verified=payload.verified or False,
        long=payload.long or False,
        has_ai_service=payload.hasAIService or False,
        categories=payload.categories,
        
        # Absolute backward compatibility requirements
        original_image_path=f"uploads/raw/{unique_id}.png",
        processed_image_path=f"uploads/processed/{unique_id}.png",
        original_image_url=payload.image or "",
        processed_image_url=payload.image or "",
        category=legacy_cat,
        subcategory=legacy_cat,
        fit="standard",
        style="minimalist",
        formality=5,
        seasons=["spring", "summer", "autumn", "winter"],
        pattern="solid",
        embedding_path=f"embeddings/{unique_id}.npy",
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    return map_clothing_item_to_response(new_item)


@router.get("/items/{itemId}", response_model=WardrobeItemResponse, status_code=status.HTTP_200_OK)
async def get_wardrobe_item(
    itemId: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetches details of a garment item. Automatically triggers sidebar logging in the background."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == itemId))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wardrobe item with ID '{itemId}' not found."
        )
        
    # Auto sidebar history logging
    user_id = str(current_user.id) if current_user else "default_user"
    hist_result = await db.execute(
        select(WardrobeHistory).where(
            and_(
                WardrobeHistory.user_id == user_id,
                WardrobeHistory.item_id == itemId
            )
        )
    )
    existing_history = hist_result.scalar_one_or_none()
    
    if existing_history:
        existing_history.viewed_at = datetime.now(timezone.utc)
    else:
        new_hist = WardrobeHistory(
            user_id=user_id,
            item_id=itemId,
            viewed_at=datetime.now(timezone.utc)
        )
        db.add(new_hist)
        
    await db.commit()
    return map_clothing_item_to_response(item)


@router.put("/items/{itemId}", response_model=WardrobeItemResponse, status_code=status.HTTP_200_OK)
async def update_wardrobe_item(
    itemId: UUID,
    payload: WardrobeItemUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Modifies garment item specifications (dominant color, fabrics, etc.)."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == itemId))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wardrobe item with ID '{itemId}' not found."
        )
        
    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle schema conversions to core models
    if "colorName" in update_data:
        item.primary_color = update_data.pop("colorName")
    if "colorHex" in update_data:
        item.primary_color_hex = update_data.pop("colorHex")
    if "secondaryColors" in update_data:
        sec_colors = update_data.pop("secondaryColors") or []
        item.secondary_colors = [c.name for c in sec_colors]
        item.secondary_colors_hex = [c.hex for c in sec_colors]
    if "moreDetails" in update_data:
        item.more_details = update_data.pop("moreDetails")
    if "hasAIService" in update_data:
        item.has_ai_service = update_data.pop("hasAIService")
    if "image" in update_data:
        img = update_data.pop("image")
        item.processed_image_url = img
        item.original_image_url = img
        
    for field, value in update_data.items():
        setattr(item, field, value)
        
    await db.commit()
    await db.refresh(item)
    return map_clothing_item_to_response(item)


@router.delete("/items/{itemId}", status_code=status.HTTP_200_OK)
async def delete_wardrobe_item(
    itemId: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deletes the closet item and cascades cloud storage asset cleanup."""
    result = await db.execute(select(ClothingItem).where(ClothingItem.id == itemId))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wardrobe item with ID '{itemId}' not found."
        )
        
    # Delete uploaded physical assets cleanly
    if item.processed_image_url:
        storage_service.delete_file(item.processed_image_url)
    if item.original_image_url:
        storage_service.delete_file(item.original_image_url)
        
    await db.delete(item)
    await db.commit()
    return {"success": True, "message": f"Wardrobe item '{itemId}' successfully deleted."}


# ── Statistics, Sidebar Logs & Scanning Endpoints ───────────────────────────

@router.get("/stats", response_model=WardrobeStatsResponse, status_code=status.HTTP_200_OK)
async def get_wardrobe_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetches overview metrics of the user's digital wardrobe."""
    user_id = str(current_user.id) if current_user else "default_user"
    
    total_pieces = await db.scalar(select(func.count(ClothingItem.id))) or 0
    verified_pieces = await db.scalar(select(func.count(ClothingItem.id)).where(ClothingItem.verified == True)) or 0
    sync_percentage = (verified_pieces / total_pieces * 100.0) if total_pieces > 0 else 0.0
    outfits_count = await db.scalar(select(func.count(SavedOutfit.id)).where(SavedOutfit.user_id == user_id)) or 0
    
    return WardrobeStatsResponse(
        syncPercentage=round(sync_percentage, 1),
        totalPieces=total_pieces,
        outfitsCount=outfits_count
    )


@router.get("/history", response_model=PaginatedHistoryResponse, status_code=status.HTTP_200_OK)
async def list_wardrobe_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Sidebar viewed logs list sorted chronologically with dynamic relative date labeling."""
    user_id = str(current_user.id) if current_user else "default_user"
    
    # Base select query joining history logs with garment specifications
    query = (
        select(WardrobeHistory, ClothingItem)
        .join(ClothingItem, WardrobeHistory.item_id == ClothingItem.id)
        .where(WardrobeHistory.user_id == user_id)
    )
    
    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    
    # Sort chronologically by views
    query = query.order_by(WardrobeHistory.viewed_at.desc())
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    meta = PaginationMeta(
        currentPage=page,
        pageSize=limit,
        totalPages=total_pages,
        totalCount=total_count,
        hasNextPage=page < total_pages,
        hasPrevPage=page > 1
    )
    
    data = []
    for hist, item in rows:
        relative_label = get_relative_time_label(hist.viewed_at)
        data.append(WardrobeHistoryResponse(
            id=hist.id,
            item=map_clothing_item_to_response(item),
            viewedAt=hist.viewed_at,
            relativeTimeLabel=relative_label
        ))
        
    return PaginatedHistoryResponse(data=data, meta=meta)


@router.post("/scan", response_model=ScanImageResponse, status_code=status.HTTP_200_OK)
async def scan_garment_image(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts raw garment photo upload. Saves to storage and runs instant, non-blocking 
    mock AI classifier recommending color, fabric, and categories for styling.
    """
    mime = image.content_type.lower() if image.content_type else ""
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        ext = image.filename.split(".")[-1].lower() if image.filename else ""
        if ext not in {"jpg", "jpeg", "png", "webp"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Allowed types: jpeg, png, webp."
            )
            
    # Buffer stream size limit check
    file_bytes = await image.read()
    if len(file_bytes) > settings.MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum content length limit."
        )
        
    ext = "png"
    if image.filename:
        parsed_ext = image.filename.split(".")[-1].lower()
        if parsed_ext in {"jpg", "jpeg", "png", "webp"}:
            ext = parsed_ext
            
    unique_filename = f"scan-{uuid.uuid4()}.{ext}"
    
    # Save the file using standard storage service helper
    saved_url = storage_service.upload_file(
        file_data=file_bytes,
        folder="raw",
        filename=unique_filename,
        content_type=image.content_type or f"image/{ext}"
    )
    
    # Classify deterministically based on file keywords
    filename_lower = image.filename.lower() if image.filename else ""
    
    color_name = "Classic Navy"
    color_hex = "#000080"
    textile = "Cashmere Knit"
    category = "tops"
    subcategory = "knitwear"
    confidence = 0.94
    
    if "pant" in filename_lower or "jean" in filename_lower or "trouser" in filename_lower:
        color_name = "Slate Grey"
        color_hex = "#708090"
        textile = "Wool Blend"
        category = "bottoms"
        subcategory = "trousers"
        confidence = 0.89
    elif "shoe" in filename_lower or "boot" in filename_lower or "sneaker" in filename_lower or "foot" in filename_lower:
        color_name = "Formal Black"
        color_hex = "#1A1A1A"
        textile = "Genuine Leather"
        category = "footwear"
        subcategory = "oxford"
        confidence = 0.95
    elif "coat" in filename_lower or "jacket" in filename_lower or "blazer" in filename_lower:
        color_name = "Camel Brown"
        color_hex = "#C19A6B"
        textile = "Tweed"
        category = "outerwear"
        subcategory = "blazer"
        confidence = 0.91
    elif "bag" in filename_lower or "belt" in filename_lower or "hat" in filename_lower:
        color_name = "Tan Leather"
        color_hex = "#B87333"
        textile = "Suede"
        category = "accessories"
        subcategory = "belt"
        confidence = 0.88
        
    return ScanImageResponse(
        colorName=color_name,
        colorHex=color_hex,
        textile=textile,
        category=category,
        subcategory=subcategory,
        confidence=confidence,
        tempFileKey=saved_url,
    )
