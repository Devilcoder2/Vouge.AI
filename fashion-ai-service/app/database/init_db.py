import asyncio
import sys
from pathlib import Path

# Add root folder to python path for standard execution
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.database.session import Base, async_engine
from app.database.models import ClothingItem

async def init_models():
    """
    Connects to the database and creates all tables mapped in our SQLAlchemy models.
    """
    print("Connecting to database engine and initializing schemas...")
    try:
        async with async_engine.begin() as conn:
            # Execute standard create_all using async runner
            await conn.run_sync(Base.metadata.create_all)
        print("PostgreSQL tables successfully initialized.")
    except Exception as e:
        print(f"Database initialization failed: {str(e)}", file=sys.stderr)
        print("\n[Tip] Please verify that your local PostgreSQL server is running and the database 'vouge' is created.", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(init_models())
