"""
Pydantic Schemas for VOGUE.AI Dynamic Calendar Planner.
"""
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date as date_type, datetime
from typing import List, Optional, Dict, Any


class PlannerItemResponse(BaseModel):
    id: UUID
    name: str
    category: str
    processed_image_url: Optional[str] = None


class PlannerWearLogResponse(BaseModel):
    log_id: UUID
    image_url: str
    notes: Optional[str] = None
    logged_at: datetime


class PlannerSlotResponse(BaseModel):
    planned_outfit_id: UUID
    time_slot: str
    occasion: str
    outfit_source: str
    outfit_id: Optional[UUID] = None
    notes: Optional[str] = None
    vogue_score: int
    items: List[PlannerItemResponse] = []
    wear_log: Optional[PlannerWearLogResponse] = None


class DailyPlannerResponse(BaseModel):
    date: date_type
    day_of_week: str
    planned_slots: List[PlannerSlotResponse] = []


class PlannerRangeResponse(BaseModel):
    start_date: date_type
    end_date: date_type
    calendar: List[DailyPlannerResponse]


class PlannerScheduleRequest(BaseModel):
    user_id: Optional[str] = Field("default_user", description="Identifier of the user")
    date: date_type = Field(..., description="Target planner date YYYY-MM-DD")
    time_slot: str = Field(..., description="Occasion slot name, e.g. Dinner Gala, Morning Jog")
    occasion: str = Field(..., description="Aesthetic dress code, e.g. FORMAL, WORKOUT, CASUAL")
    outfit_source: str = Field("custom_user", description="Either custom_user or saved_outfit")
    outfit_id: Optional[UUID] = Field(None, description="Optional pre-existing saved outfit to schedule")
    clothing_item_ids: Optional[List[UUID]] = Field(None, description="List of clothing item ids for custom coordinate planning")
    notes: Optional[str] = Field(None, description="Optional visual or aesthetic remarks")


class PlannerScheduleResponse(BaseModel):
    message: str
    planned_outfit_id: UUID
    date: date_type
    time_slot: str
    items_count: int


class PlannerScheduleUpdateRequest(BaseModel):
    date: Optional[date_type] = Field(None, description="Rescheduled date YYYY-MM-DD")
    time_slot: Optional[str] = Field(None, description="Rescheduled time slot name")
    clothing_item_ids: Optional[List[UUID]] = Field(None, description="Updated list of clothing item ids")
    notes: Optional[str] = Field(None, description="Updated visual remarks")


class PlannerScheduleUpdateResponse(BaseModel):
    message: str
    planned_outfit_id: UUID
    updated_fields: List[str]


class AgendaSlotRequest(BaseModel):
    time_slot: str
    occasion: str


class AgendaDayRequest(BaseModel):
    date: date_type
    slots: List[AgendaSlotRequest]


class PlannerAutoGenerateRequest(BaseModel):
    user_id: Optional[str] = Field("default_user", description="Identifier of the user")
    start_date: date_type = Field(..., description="Target start date YYYY-MM-DD")
    days_count: int = Field(..., description="Number of days to auto-plan")
    agendas: List[AgendaDayRequest] = Field(..., description="Day-by-day occasion slots to fill")


class PlannerAutoGenerateResponse(BaseModel):
    message: str
    auto_scheduled_count: int
    planned_days: List[date_type]


class WearLogResponse(BaseModel):
    message: str
    log_id: UUID
    date: date_type
    image_url: str
    notes: Optional[str] = None
    planned_outfit_id: Optional[UUID] = None
