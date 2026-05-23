import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes.processing import router as processing_router

# Configure detailed runtime logging to standard output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fashion-ai-service")

# Initialize FastAPI App with descriptive Open-API documentation tags
app = FastAPI(
    title="AI Fashion Assistant - Clothing Intelligence Service",
    description="Microservice responsible for background removal, metadata classification, color extraction, and CLIP vector embeddings.",
    version="1.0.0"
)

# Configure Cross-Origin Resource Sharing (CORS)
# Critical for future Web (Next.js) or Mobile (React Native) UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount local directories as static file routes to allow asset inspection in Swagger
# E.g. viewing a processed cropped garment via http://localhost:8000/processed/some_id.png
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/processed", StaticFiles(directory=str(settings.PROCESSED_DIR)), name="processed")

# Register core application routing endpoints
app.include_router(processing_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Clothing Intelligence Service API framework...")
    logger.info(f"Target upload storage directory: {settings.UPLOAD_DIR}")
    logger.info(f"Target processed storage directory: {settings.PROCESSED_DIR}")
    logger.info(f"Target embedding vector directory: {settings.EMBEDDING_DIR}")
    logger.info("Fashion Intelligence Service successfully initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Gracefully shutting down Fashion Intelligence Service...")
