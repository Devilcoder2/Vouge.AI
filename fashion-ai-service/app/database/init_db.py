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

        print("✓ PostgreSQL tables successfully initialized.")
        print("  Tables managed:")
        for table in Base.metadata.sorted_tables:
            print(f"    • {table.name}")

    except Exception as e:
        print(f"✗ Database initialization failed: {str(e)}", file=sys.stderr)
        print("\n[Tip] Verify your PostgreSQL server is running and 'vouge' database exists.", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(init_models())
