import uuid
from sqlalchemy import Column, String, Integer, ARRAY, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
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
    
    # Path to saved local float32 numpy vector array (.npy file)
    embedding_path = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
