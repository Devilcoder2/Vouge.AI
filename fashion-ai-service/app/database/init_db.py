import asyncio
import sys
from pathlib import Path

# Add root folder to python path for standard execution
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import text
from app.database.session import Base, async_engine

# Import ALL models so Base.metadata picks them up for create_all
from app.database.models import (
    ClothingItem,
    SavedOutfit,
    SavedOutfitItem,
    UserProfile,
    UserFeedback,
    # Phase 3A — Auth & Identity
    User,
    RefreshToken,
    UserSession,
    RecommendationFeedback,
    UserBehaviorEvent,
    UserStyleProfile,
    BackgroundJob,
    # Phase 3B — Digital Wardrobe REST API
    WardrobeCategory,
    WardrobeHistory,
    # Social Models
    UserFollow,
    SocialPost,
    ExternalProduct,
    PostTaggedItem,
    PostLike,
    PostComment,
    PostSave,
    FashionCommunity,
    CommunityMember,
)

async def init_models():
    """
    Connects to the database and creates all tables mapped in SQLAlchemy models.
    Uses CREATE TABLE IF NOT EXISTS semantics — safe to run on an existing database.
    """
    print("Connecting to database engine and initializing schemas...")
    try:
        async with async_engine.begin() as conn:
            # Create all tables (safe — IF NOT EXISTS)
            await conn.run_sync(Base.metadata.create_all)

            # Safe online migrations for previously added columns
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS perceptual_hash VARCHAR(64);"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS original_image_url VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS processed_image_url VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS preview_url VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE saved_outfits ADD COLUMN IF NOT EXISTS preview_url VARCHAR;"
            ))

            # Safe online migrations for user social attributes
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS vanity_username VARCHAR(50) UNIQUE;"
            ))
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;"
            ))
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_badge BOOLEAN DEFAULT FALSE;"
            ))
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS favorite_brands VARCHAR[] DEFAULT '{}';"
            ))
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS wardrobe_visibility VARCHAR(20) DEFAULT 'public';"
            ))

            # Phase 3B attribute extensions on clothing_items
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS name VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS textile VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS more_details TEXT;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS occasion VARCHAR;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS long BOOLEAN DEFAULT FALSE;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS has_ai_service BOOLEAN DEFAULT FALSE;"
            ))
            await conn.execute(text(
                "ALTER TABLE clothing_items ADD COLUMN IF NOT EXISTS categories VARCHAR[];"
            ))

            # safe online migrations for social posts community extensions
            await conn.execute(text(
                "ALTER TABLE social_posts ADD COLUMN IF NOT EXISTS community_id UUID;"
            ))

            # Seed default categories
            await conn.execute(text("""
                INSERT INTO wardrobe_categories (id, name, subtitle, status) VALUES
                ('tops', 'Tops', 'Shirts, t-shirts, knits, and blouses', 'active'),
                ('bottoms', 'Bottoms', 'Pants, jeans, shorts, and skirts', 'active'),
                ('footwear', 'Footwear', 'Shoes, boots, sneakers, and sandals', 'active'),
                ('outerwear', 'Outerwear', 'Coats, jackets, parkas, and blazers', 'active'),
                ('accessories', 'Accessories', 'Bags, belts, hats, and jewelry', 'active')
                ON CONFLICT (id) DO NOTHING;
            """))

        print("✓ PostgreSQL tables successfully initialized and seeded.")
        print("  Tables managed:")
        for table in Base.metadata.sorted_tables:
            print(f"    • {table.name}")

    except Exception as e:
        print(f"✗ Database initialization failed: {str(e)}", file=sys.stderr)
        print("\n[Tip] Verify your PostgreSQL server is running and 'vouge' database exists.", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(init_models())

