from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class PaginationMeta(BaseModel):
    currentPage: int
    pageSize: int
    totalPages: int
    totalCount: int
    hasNextPage: bool
    hasPrevPage: bool

class CategoryResponse(BaseModel):
    id: str
    name: str
    subtitle: Optional[str] = None
    status: Optional[str] = None
    image: Optional[str] = None
    count: int

    class Config:
        from_attributes = True

class CategoryCreateRequest(BaseModel):
    name: str
    subtitle: Optional[str] = None
    image: Optional[str] = None

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    subtitle: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None

class SecondaryColor(BaseModel):
    name: str
    hex: str

class WardrobeItemResponse(BaseModel):
    id: UUID
    name: str
    textile: Optional[str] = None
    colorName: str
    colorHex: str
    secondaryColors: List[SecondaryColor] = []
    moreDetails: Optional[str] = None
    occasion: Optional[str] = None
    image: Optional[str] = None
    verified: bool
    long: bool
    hasAIService: bool
    categories: List[str]

    class Config:
        from_attributes = True

class WardrobeItemCreateRequest(BaseModel):
    name: str
    textile: Optional[str] = None
    colorName: str
    colorHex: str
    secondaryColors: List[SecondaryColor] = []
    moreDetails: Optional[str] = None
    occasion: Optional[str] = None
    image: Optional[str] = None
    verified: Optional[bool] = False
    long: Optional[bool] = False
    hasAIService: Optional[bool] = False
    categories: List[str]

class WardrobeItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    textile: Optional[str] = None
    colorName: Optional[str] = None
    colorHex: Optional[str] = None
    secondaryColors: Optional[List[SecondaryColor]] = None
    moreDetails: Optional[str] = None
    occasion: Optional[str] = None
    image: Optional[str] = None
    verified: Optional[bool] = None
    long: Optional[bool] = None
    hasAIService: Optional[bool] = None
    categories: Optional[List[str]] = None

class PaginatedItemResponse(BaseModel):
    data: List[WardrobeItemResponse]
    meta: PaginationMeta

class WardrobeStatsResponse(BaseModel):
    syncPercentage: float
    totalPieces: int
    outfitsCount: int

class WardrobeHistoryResponse(BaseModel):
    id: UUID
    item: WardrobeItemResponse
    viewedAt: datetime
    relativeTimeLabel: str

    class Config:
        from_attributes = True

class PaginatedHistoryResponse(BaseModel):
    data: List[WardrobeHistoryResponse]
    meta: PaginationMeta

class ScanImageResponse(BaseModel):
    colorName: str
    colorHex: str
    textile: str
    category: str
    subcategory: str
    confidence: float
    tempFileKey: str
