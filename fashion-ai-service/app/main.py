import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routes.processing import router as processing_router
from app.routes.recommendation import router as recommendation_router
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.personalization import router as personalization_router
from app.routes.jobs import router as jobs_router

# Configure detailed runtime logging to standard output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fashion-ai-service")

# ── Rate Limiter ──────────────────────────────────────────────────────────────
# Applied on auth endpoints to prevent brute-force attacks.
# Limit: 20 requests per minute per IP address.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Vouge.AI — Fashion Intelligence Service",
    description=(
        "Production-grade backend for AI-powered wardrobe management, outfit recommendations, "
        "and personalized fashion intelligence. Phase 3A: Authentication & User Identity."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static File Mounts ────────────────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/processed", StaticFiles(directory=str(settings.PROCESSED_DIR)), name="processed")

# ── Router Registration ───────────────────────────────────────────────────────
# Phase 2: Clothing Processing & Recommendations (unchanged, no prefix)
app.include_router(processing_router)
app.include_router(recommendation_router)

# Phase 3A: Authentication & User Profile (versioned under /v1)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(personalization_router)
app.include_router(jobs_router)


# ── Lifecycle Events ──────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("═══════════════════════════════════════════════════════")
    logger.info("  Vouge.AI Fashion Intelligence Service — Starting Up  ")
    logger.info("═══════════════════════════════════════════════════════")
    logger.info(f"  Upload dir:    {settings.UPLOAD_DIR}")
    logger.info(f"  Processed dir: {settings.PROCESSED_DIR}")
    logger.info(f"  Previews dir:  {settings.PREVIEWS_DIR}")
    logger.info(f"  Auth: JWT HS256, access={settings.ACCESS_TOKEN_EXPIRE_MINUTES}min, refresh={settings.REFRESH_TOKEN_EXPIRE_DAYS}d")
    logger.info("═══════════════════════════════════════════════════════")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Vouge.AI Fashion Intelligence Service — Gracefully shutting down.")
