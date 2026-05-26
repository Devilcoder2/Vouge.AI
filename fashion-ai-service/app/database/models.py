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
    
    # Cloud Storage CDN-ready URLs
    original_image_url = Column(String, nullable=True)
    processed_image_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    preview_url = Column(String, nullable=True)
    
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
    
    # Frontend wardrobe attribute extensions
    name = Column(String, nullable=True)
    textile = Column(String, nullable=True)
    more_details = Column(Text, nullable=True)
    occasion = Column(String, nullable=True)  # casual, work, evening, event
    verified = Column(Boolean, default=False)
    long = Column(Boolean, default=False)
    has_ai_service = Column(Boolean, default=False)
    categories = Column(ARRAY(String), nullable=True)  # Many-to-Many categories array (strings)
    
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
    preview_url = Column(String, nullable=True)
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

    # Social details
    vanity_username = Column(String(50), unique=True, nullable=True, index=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    verified_badge = Column(Boolean, default=False)
    favorite_brands = Column(ARRAY(String), nullable=False, default=list)
    wardrobe_visibility = Column(String(20), nullable=False, default="public")

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
    
    # Social relationships
    posts = relationship("SocialPost", back_populates="user", cascade="all, delete-orphan")


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


# ── Phase 3B: Digital Wardrobe REST API ──────────────────────────────────────

class WardrobeCategory(Base):
    """
    SQLAlchemy model representing a custom wardrobe collection/category.
    """
    __tablename__ = "wardrobe_categories"

    id = Column(String, primary_key=True)  # URL-friendly slug, e.g. "tops", "evening-wear"
    name = Column(String, nullable=False, unique=True)
    subtitle = Column(String, nullable=True)
    image = Column(String, nullable=True)
    status = Column(String, nullable=True)  # e.g., active, archived
    created_at = Column(DateTime(timezone=True), default=func.now())


class WardrobeHistory(Base):
    """
    SQLAlchemy model tracking recently viewed wardrobe items.
    """
    __tablename__ = "wardrobe_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class UserFollow(Base):
    """
    Association model representing follower/following relationships.
    """
    __tablename__ = "user_follows"

    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


class SocialPost(Base):
    """
    SQLAlchemy model representing an outfit social post.
    """
    __tablename__ = "social_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String, nullable=False)
    caption = Column(Text, nullable=True)
    weather_context = Column(String(50), nullable=True)
    occasion_tag = Column(String(50), nullable=True)
    style_persona = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    community_id = Column(UUID(as_uuid=True), ForeignKey("fashion_communities.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="posts")
    tagged_items = relationship("PostTaggedItem", back_populates="post", cascade="all, delete-orphan", lazy="selectin")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan", lazy="selectin")
    saves = relationship("PostSave", back_populates="post", cascade="all, delete-orphan")
    community = relationship("FashionCommunity", back_populates="posts")


class ExternalProduct(Base):
    """
    SQLAlchemy model representing scraped affiliate products from external brands.
    """
    __tablename__ = "external_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)
    source_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    url = Column(Text, nullable=False)
    scraped_at = Column(DateTime(timezone=True), default=func.now())


class PostTaggedItem(Base):
    """
    SQLAlchemy model representing interactive item hotspots tagged in social posts.
    """
    __tablename__ = "post_tagged_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Points to either a digitized wardrobe item or an external affiliate item
    wardrobe_item_id = Column(UUID(as_uuid=True), ForeignKey("clothing_items.id", ondelete="SET NULL"), nullable=True)
    external_product_id = Column(UUID(as_uuid=True), ForeignKey("external_products.id", ondelete="SET NULL"), nullable=True)
    
    x_coord = Column(Numeric(5, 2), nullable=False)
    y_coord = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    post = relationship("SocialPost", back_populates="tagged_items")
    wardrobe_item = relationship("ClothingItem", lazy="selectin")


class PostLike(Base):
    """
    Association model representing social likes.
    """
    __tablename__ = "post_likes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    post = relationship("SocialPost", back_populates="likes")


class PostComment(Base):
    """
    SQLAlchemy model representing comments on social posts.
    Supports nested threads using self-referencing hierarchy.
    """
    __tablename__ = "post_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("post_comments.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    post = relationship("SocialPost", back_populates="comments")
    user = relationship("User", lazy="selectin")


class PostSave(Base):
    """
    Association model representing saved posts.
    """
    __tablename__ = "post_saves"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    post = relationship("SocialPost", back_populates="saves")


class FashionCommunity(Base):
    """
    SQLAlchemy model representing a styling fashion community (e.g. Streetwear, Quiet Luxury).
    """
    __tablename__ = "fashion_communities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String, nullable=True)
    rules = Column(Text, nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    posts = relationship("SocialPost", back_populates="community")
    members = relationship("CommunityMember", back_populates="community", cascade="all, delete-orphan")


class CommunityMember(Base):
    """
    SQLAlchemy model representing community membership and roles (member, moderator, admin).
    """
    __tablename__ = "community_members"

    community_id = Column(UUID(as_uuid=True), ForeignKey("fashion_communities.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(30), nullable=False, default="member")  # member, moderator, admin
    joined_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    community = relationship("FashionCommunity", back_populates="members")
    user = relationship("User", lazy="selectin")


