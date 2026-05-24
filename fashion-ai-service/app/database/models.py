import uuid
from datetime import date
from sqlalchemy import Column, String, Integer, ARRAY, Date, DateTime, Numeric, Boolean, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSON, JSONB
from sqlalchemy.orm import relationship
from app.database.session import Base

class ClothingItem(Base):
    """
    SQLAlchemy model representing a digitized clothing item in a user's wardrobe.
    Contains metadata extracted from the image and paths to physical assets.
    """
    __tablename__ = "clothing_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_image_path = Column(String, nullable=False)
    processed_image_path = Column(String, nullable=False)
    
    # Metadata extracted by Gemini & OpenCV
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    primary_color = Column(String, nullable=False)
    primary_color_hex = Column(String, nullable=True)
    secondary_colors = Column(ARRAY(String), nullable=False, default=list)
    secondary_colors_hex = Column(ARRAY(String), nullable=True, default=list)
    fit = Column(String, nullable=False)
    style = Column(String, nullable=False)
    formality = Column(Integer, nullable=False)
    seasons = Column(ARRAY(String), nullable=False, default=list)
    pattern = Column(String, nullable=False)
    
    # Confidence metrics for LLM metadata extraction
    confidence_category = Column(Numeric(3, 2), nullable=True)
    confidence_subcategory = Column(Numeric(3, 2), nullable=True)
    confidence_fit = Column(Numeric(3, 2), nullable=True)
    confidence_style = Column(Numeric(3, 2), nullable=True)
    confidence_pattern = Column(Numeric(3, 2), nullable=True)
    
    # Traceability & validation metrics
    prompt_version = Column(String(50), nullable=False, default="v1.0.0")
    detected_items_count = Column(Integer, nullable=False, default=1)
    
    # Duplicate checking
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of_id = Column(UUID(as_uuid=True), nullable=True)
    perceptual_hash = Column(String(64), nullable=True)

    
    # Path to saved local float32 numpy vector array (.npy file)
    embedding_path = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=func.now())

class SavedOutfit(Base):
    """
    SQLAlchemy model representing a saved outfit curated by a user.
    """
    __tablename__ = "saved_outfits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, default="default_user")
    name = Column(String, nullable=False)
    occasion = Column(String, nullable=False)
    season = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    reasoning = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationship to intermediate items
    items = relationship("SavedOutfitItem", back_populates="outfit", cascade="all, delete-orphan", lazy="selectin")

class SavedOutfitItem(Base):
    """
    SQLAlchemy intermediate model mapping SavedOutfits to ClothingItems.
    """
    __tablename__ = "saved_outfit_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outfit_id = Column(UUID(as_uuid=True), ForeignKey("saved_outfits.id", ondelete="CASCADE"), nullable=False)
    clothing_item_id = Column(UUID(as_uuid=True), ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    outfit = relationship("SavedOutfit", back_populates="items")
    clothing_item = relationship("ClothingItem", lazy="selectin")

class UserProfile(Base):
    """
    SQLAlchemy model representing a user's styling profile, including body archetype, fit, and style preferences.
    """
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, unique=True, nullable=False)
    height_cm = Column(Integer, nullable=True)
    body_archetype = Column(String, nullable=True)  # pear_shape, rectangle, athletic, stocky, lean_tall
    fit_preference = Column(String, nullable=True)  # slim, standard, oversized
    style_persona = Column(String, nullable=True)   # minimalist, old_money, streetwear, quiet_luxury, etc.
    avoided_colors = Column(ARRAY(String), nullable=False, default=list)
    favorite_styles = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=func.now())

class UserFeedback(Base):
    """
    SQLAlchemy model representing a user's outfit styling feedback (likes, saves, dismissals).
    """
    __tablename__ = "user_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    outfit_item_ids = Column(ARRAY(String), nullable=False)  # array of garment UUID strings
    feedback_type = Column(String, nullable=False)  # like, save, dismiss
    created_at = Column(DateTime(timezone=True), default=func.now())


# ── Phase 3A: Authentication & Identity ──────────────────────────────────────

class User(Base):
    """
    Core user identity model for Vouge.AI.
    Stores account credentials, body metrics, and style preferences.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    # Personal details
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    gender = Column(String(30), nullable=True)          # male, female, non_binary, prefer_not_to_say
    date_of_birth = Column(Date, nullable=True)

    # Body metrics
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Numeric(5, 2), nullable=True)
    body_type = Column(String(50), nullable=True)       # pear_shape, rectangle, athletic, stocky, lean_tall
    preferred_fit = Column(String(20), nullable=True)   # slim, standard, oversized

    # Style intelligence
    style_personas = Column(ARRAY(String), nullable=False, default=list)  # minimalist, old_money, etc.
    avoided_colors = Column(ARRAY(String), nullable=False, default=list)
    climate_region = Column(String(30), nullable=True)  # tropical, temperate, cold, arid

    # Account state
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    style_profile = relationship("UserStyleProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    background_jobs = relationship("BackgroundJob", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """
    Stores hashed refresh tokens for secure session rotation.
    The raw token is sent to the client exactly once and never persisted.
    """
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hex
    device_name = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=True)       # supports IPv6
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")


class UserSession(Base):
    """
    Tracks active user sessions for device management and audit logging.
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_info = Column(String(500), nullable=True)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="sessions")


class RecommendationFeedback(Base):
    """
    SQLAlchemy model representing recommendation feedback (like, save, dismiss, regenerate).
    """
    __tablename__ = "recommendation_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    outfit_id = Column(String, nullable=True)  # SavedOutfit ID or temporary generated outfit ID
    action_type = Column(String, nullable=False)  # like, save, dismiss, regenerate
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserBehaviorEvent(Base):
    """
    SQLAlchemy model representing tracked user behavior events (view, clicks, etc.).
    """
    __tablename__ = "user_behavior_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # outfit_viewed, item_added, etc.
    event_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserStyleProfile(Base):
    """
    SQLAlchemy model representing the user's persistently learned style profile preferences.
    """
    __tablename__ = "user_style_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    preferred_colors = Column(ARRAY(String), nullable=False, default=list)
    disliked_colors = Column(ARRAY(String), nullable=False, default=list)
    preferred_styles = Column(ARRAY(String), nullable=False, default=list)
    preferred_formality_range = Column(ARRAY(Integer), nullable=False, default=list)
    favorite_categories = Column(ARRAY(String), nullable=False, default=list)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship back to User
    user = relationship("User", back_populates="style_profile")


class BackgroundJob(Base):
    """
    SQLAlchemy model representing asynchronous background job telemetry.
    """
    __tablename__ = "background_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String, nullable=False)  # clothing_processing_job, outfit_generation_job, gap_analysis_job
    status = Column(String, nullable=False, default="queued")  # queued, processing, completed, failed, cancelled
    progress = Column(Integer, nullable=False, default=0)  # 0 to 100
    error_message = Column(String, nullable=True)
    result_reference = Column(JSON, nullable=True)  # References to finished entities / JSON structures
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship back to User
    user = relationship("User", back_populates="background_jobs")
