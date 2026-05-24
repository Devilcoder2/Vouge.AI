import uuid
from sqlalchemy import Column, String, Integer, ARRAY, DateTime, Numeric, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
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

