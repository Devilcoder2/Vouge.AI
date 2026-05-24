"""
Pydantic request/response schemas for the Vouge.AI Authentication API.
"""
import re
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Validators ─────────────────────────────────────────────────────────────────

def _validate_username(value: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]{3,50}$", value):
        raise ValueError(
            "Username must be 3-50 characters and contain only letters, digits, or underscores."
        )
    return value.lower()


# ── Request Schemas ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    """Request body for POST /v1/auth/signup."""
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username (letters, digits, underscores)")
    password: str = Field(..., min_length=8, description="Password (min 8 chars, 1 uppercase, 1 digit, 1 special)")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, description="male | female | non_binary | prefer_not_to_say")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return _validate_username(v)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"male", "female", "non_binary", "prefer_not_to_say"}
        if v and v not in allowed:
            raise ValueError(f"gender must be one of: {', '.join(sorted(allowed))}")
        return v


class LoginRequest(BaseModel):
    """Request body for POST /v1/auth/login."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class RefreshRequest(BaseModel):
    """Request body for POST /v1/auth/refresh."""
    refresh_token: str = Field(..., description="Valid refresh token issued at login or previous refresh")


class UpdateProfileRequest(BaseModel):
    """Request body for PATCH /v1/users/me — all fields optional."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, description="male | female | non_binary | prefer_not_to_say")
    date_of_birth: Optional[date] = Field(None)
    height_cm: Optional[int] = Field(None, ge=50, le=300, description="Height in centimetres")
    weight_kg: Optional[float] = Field(None, ge=20.0, le=500.0, description="Weight in kilograms")
    body_type: Optional[str] = Field(
        None,
        description="pear_shape | rectangle | athletic | stocky | lean_tall | hourglass | apple"
    )
    preferred_fit: Optional[str] = Field(None, description="slim | standard | oversized")
    style_personas: Optional[List[str]] = Field(None, description="List of style personas")
    avoided_colors: Optional[List[str]] = Field(None, description="List of avoided colors")
    climate_region: Optional[str] = Field(None, description="tropical | temperate | cold | arid")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"male", "female", "non_binary", "prefer_not_to_say"}
        if v and v not in allowed:
            raise ValueError(f"gender must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("preferred_fit")
    @classmethod
    def validate_fit(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"slim", "standard", "oversized"}
        if v and v not in allowed:
            raise ValueError(f"preferred_fit must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("body_type")
    @classmethod
    def validate_body_type(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"pear_shape", "rectangle", "athletic", "stocky", "lean_tall", "hourglass", "apple"}
        if v and v not in allowed:
            raise ValueError(f"body_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("climate_region")
    @classmethod
    def validate_climate(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"tropical", "temperate", "cold", "arid"}
        if v and v not in allowed:
            raise ValueError(f"climate_region must be one of: {', '.join(sorted(allowed))}")
        return v


# ── Response Schemas ───────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Serialized public representation of a User object."""
    id: UUID
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    body_type: Optional[str] = None
    preferred_fit: Optional[str] = None
    style_personas: List[str] = Field(default_factory=list)
    avoided_colors: List[str] = Field(default_factory=list)
    climate_region: Optional[str] = None
    onboarding_completed: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    """JWT + refresh token pair returned on login/signup/refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class AuthSuccessResponse(BaseModel):
    """Standard envelope for all auth success responses."""
    success: bool = True
    data: dict  # contains user + token fields


class LogoutRequest(BaseModel):
    """Request body for POST /v1/auth/logout."""
    refresh_token: str = Field(..., description="The refresh token to revoke")
