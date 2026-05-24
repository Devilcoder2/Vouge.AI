"""
Phase 3A — Feature 3: Async AI Processing System Tests.
Uses FastAPI TestClient with dependency_overrides to prevent asyncpg event-loop conflicts
and tests in-process local execution and local BackgroundTasks queues without requiring Redis.
"""
import uuid
from uuid import UUID
from datetime import datetime, timezone, timedelta
from io import BytesIO
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.auth.dependencies import get_current_active_user
from app.auth.security import create_access_token
from app.database.session import get_db
from app.database.models import User, BackgroundJob, ClothingItem
from app.schemas.jobs import JobStatusResponse
import app.tasks as tasks_module
from app.tasks import (
    clothing_processing_job,
    outfit_generation_job,
    gap_analysis_job,
    dead_job_recovery_job,
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_mocks():
    # Save original references
    import app.tasks as tasks_module
    orig_session = getattr(tasks_module, "AsyncSessionLocal", None)
    
    from app.ai.background_removal import BackgroundRemover
    orig_remove_bg = BackgroundRemover.remove_background
    
    from app.ai.preprocessing import ImagePreprocessor
    orig_preprocess = ImagePreprocessor.preprocess_image
    
    from app.ai.classifier import FashionClassifier
    orig_classify = FashionClassifier.classify_garment
    
    from app.ai.color_extractor import ColorExtractor
    orig_extract_colors = ColorExtractor.extract_colors
    
    from app.ai.embedding_service import FashionEmbeddingService
    orig_gen_embedding = FashionEmbeddingService.generate_image_embedding
    orig_save_embedding = FashionEmbeddingService.save_embedding_to_disk
    
    from app.services.duplicate_detector import DuplicateDetector
    orig_calc_dhash = DuplicateDetector.calculate_dhash
    orig_check_dup = DuplicateDetector.check_duplicates
    
    from app.recommendation.explainers.outfit_explainer import OutfitExplainer
    orig_explain = OutfitExplainer.explain_recommendations
    
    from app.recommendation.engines.gap_analysis import GapAnalysisEngine
    orig_analyze_gaps = GapAnalysisEngine.analyze_gaps

    from app.services.image_optimizer import ImageOptimizer
    orig_validate_load = ImageOptimizer.validate_and_load
    orig_gen_variants = ImageOptimizer.generate_variants
    
    yield
    
    # Restore original references
    if orig_session is not None:
        tasks_module.AsyncSessionLocal = orig_session
    BackgroundRemover.remove_background = orig_remove_bg
    ImagePreprocessor.preprocess_image = orig_preprocess
    FashionClassifier.classify_garment = orig_classify
    ColorExtractor.extract_colors = orig_extract_colors
    FashionEmbeddingService.generate_image_embedding = orig_gen_embedding
    FashionEmbeddingService.save_embedding_to_disk = orig_save_embedding
    DuplicateDetector.calculate_dhash = orig_calc_dhash
    DuplicateDetector.check_duplicates = orig_check_dup
    OutfitExplainer.explain_recommendations = orig_explain
    GapAnalysisEngine.analyze_gaps = orig_analyze_gaps
    ImageOptimizer.validate_and_load = orig_validate_load
    ImageOptimizer.generate_variants = orig_gen_variants

# ── Shared In-Memory Stores for Test State ─────────────────────────────────────
_USERS: dict = {}
_JOBS: dict = {}             # job_id -> BackgroundJob-like object
_CLOTHING_ITEMS: list = []


class MockUser:
    def __init__(self, email="tasks@vouge.ai", username="tasks_user"):
        self.id = uuid.uuid4()
        self.email = email
        self.username = username
        self.hashed_password = "hashed_password"
        self.is_active = True
        self.onboarding_completed = True
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockClothingItem:
    def __init__(self, category="top", subcategory="shirt", primary_color="white", style="minimalist", formality=3, fit="standard"):
        self.id = uuid.uuid4()
        self.category = category
        self.subcategory = subcategory
        self.primary_color = primary_color
        self.primary_color_hex = "#ffffff"
        self.secondary_colors = []
        self.secondary_colors_hex = []
        self.fit = fit
        self.style = style
        self.formality = formality
        self.seasons = ["summer"]
        self.pattern = "solid"
        self.original_image_path = "raw.png"
        self.processed_image_path = "processed.png"
        self.embedding_path = "embed.npy"
        self.perceptual_hash = "fake"
        self.is_duplicate = False


# ── Mock DB Results Helper ───────────────────────────────────────────────────
class _MockResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value

    def scalars(self):
        return self

    def all(self):
        if isinstance(self._value, list):
            return self._value
        return [self._value] if self._value is not None else []


# ── Unified Mock DB Session with Context Manager Support ──────────────────────
class JobsMockDB:
    def __init__(self, current_user):
        self.current_user = current_user
        self._added = []

    def add(self, obj):
        self._added.append(obj)

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()

        # Parse job id from compiled statement params if present
        job_uuid = None
        if hasattr(stmt, "compile"):
            try:
                params = stmt.compile().params
                for val in params.values():
                    if isinstance(val, UUID) and val in _JOBS:
                        job_uuid = val
                        break
            except Exception:
                pass

        # Fallback to scanning statement string
        if not job_uuid:
            for key in _JOBS.keys():
                if str(key) in stmt_str:
                    job_uuid = key
                    break

        # 1. User lookup
        if "from users" in stmt_str:
            return _MockResult(self.current_user)

        # 2. BackgroundJob lookup
        elif "from background_jobs" in stmt_str:
            if job_uuid:
                return _MockResult(_JOBS.get(job_uuid))
            
            # Return stuck jobs based on creation date comparison
            # stuck job query has <= parameter. For testing, stuck job test only registers stuck job + healthy job,
            # so we can filter in-memory by status and age:
            now = datetime.now(timezone.utc)
            stuck_jobs_list = []
            for j in _JOBS.values():
                if j.status in ["queued", "processing"] and j.created_at <= now - timedelta(hours=1):
                    stuck_jobs_list.append(j)
            
            # If not a stuck job query, return all
            if "stuck" in stmt_str or "<=" in stmt_str or "completed_at" in stmt_str or len(stuck_jobs_list) > 0:
                return _MockResult(stuck_jobs_list)
                
            return _MockResult(list(_JOBS.values()))

        # 3. ClothingItem lookup
        elif "from clothing_items" in stmt_str:
            return _MockResult(_CLOTHING_ITEMS)

        return _MockResult(None)

    async def commit(self):
        for obj in self._added:
            if isinstance(obj, BackgroundJob) or hasattr(obj, "job_type"):
                if not getattr(obj, "id", None):
                    obj.id = uuid.uuid4()
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = datetime.now(timezone.utc)
                _JOBS[obj.id] = obj
            elif isinstance(obj, ClothingItem) or hasattr(obj, "embedding_path"):
                if not getattr(obj, "id", None):
                    obj.id = uuid.uuid4()
                _CLOTHING_ITEMS.append(obj)
        self._added.clear()

    async def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)

    # Context manager entry
    async def __aenter__(self):
        return self

    # Context manager exit
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def _smart_override_for_jobs(current_user: MockUser):
    """Creates a get_db override and binds AsyncSessionLocal for tasks."""
    async def mock_get_db():
        yield JobsMockDB(current_user)

    # Monkeypatch tasks session factory to use the same mock DB
    tasks_module.AsyncSessionLocal = lambda: JobsMockDB(current_user)

    return mock_get_db


# ══════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Pipeline execution synchronous mock test ────────────────────────────────
def test_process_clothing_job_lifecycle():
    """
    Tests garment processing job lifecycle.
    Disables Celery queue to force direct background execution fallback,
    asserting the status updates, progress reaches 100%, and results are persisted.
    """
    settings.USE_CELERY = False  # Force FastAPI BackgroundTasks/Sync fallback
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)
    
    # Isolate stores
    _JOBS.clear()
    _CLOTHING_ITEMS.clear()

    # Mock all heavy AI pipeline methods to prevent network calls to Gemini & PyTorch loads
    from app.ai.background_removal import BackgroundRemover
    from app.ai.preprocessing import ImagePreprocessor
    from app.ai.classifier import FashionClassifier
    from app.schemas.processing import FashionMetadataExtract, ConfidenceStringField
    from app.ai.color_extractor import ColorExtractor
    from app.ai.embedding_service import FashionEmbeddingService
    from app.services.duplicate_detector import DuplicateDetector

    class MockPILImage:
        def save(self, *args, **kwargs):
            pass

    # Standard Mocking
    BackgroundRemover.remove_background = lambda b: "transparent_bytes"
    ImagePreprocessor.preprocess_image = lambda i, target_size: MockPILImage()
    
    mock_metadata = FashionMetadataExtract(
        category=ConfidenceStringField(value="Tops", confidence=0.9),
        subcategory=ConfidenceStringField(value="tee", confidence=0.9),
        fit=ConfidenceStringField(value="standard", confidence=0.9),
        style=ConfidenceStringField(value="minimalist", confidence=0.9),
        pattern=ConfidenceStringField(value="solid", confidence=0.9),
        formality=3,
        seasons=["summer"],
        primary_color="white",
        secondary_colors=[],
        detected_items_count=1
    )
    FashionClassifier.classify_garment = lambda self, img, filename_hint: mock_metadata
    ColorExtractor.extract_colors = lambda img: ("white", [], "#ffffff", [])
    FashionEmbeddingService.generate_image_embedding = lambda self, img: [0.1] * 512
    FashionEmbeddingService.save_embedding_to_disk = lambda emb, stem: "embeddings/fake.npy"
    DuplicateDetector.calculate_dhash = lambda img: "fake_dhash"
    DuplicateDetector.check_duplicates = lambda img, emb, existing: (False, None)
    from app.services.image_optimizer import ImageOptimizer
    ImageOptimizer.validate_and_load = lambda b: MockPILImage()
    ImageOptimizer.generate_variants = lambda b: {"thumbnail": b"thumb", "mobile": b"mobile", "web": b"web"}

    # File Upload Mocking
    file_bytes = BytesIO(b"fake image content")
    file_payload = {"file": ("white_shirt.png", file_bytes, "image/png")}

    # Register Mock DB Override
    app.dependency_overrides[get_db] = _smart_override_for_jobs(user)

    # Post processing request
    resp = client.post(
        "/v1/jobs/process-clothing",
        headers={"Authorization": f"Bearer {access_token}"},
        files=file_payload
    )

    assert resp.status_code == 201, resp.json()
    job_id = resp.json()["job_id"]
    assert resp.json()["status"] == "queued"

    # Verify the job was executed and successfully committed inside mock jobs store
    assert UUID(job_id) in _JOBS
    job = _JOBS[UUID(job_id)]
    
    # Assert status was successfully marked as completed & result populated
    assert job.status == "completed"
    assert job.progress == 100
    assert "item_id" in job.result_reference
    assert len(_CLOTHING_ITEMS) == 1

    app.dependency_overrides.pop(get_db, None)


# ── 2. Outfit Generation Job Lifecycle Mock Test ─────────────────────────────
@pytest.mark.anyio
async def test_outfit_generation_job_lifecycle():
    """
    Tests outfit generation background job, assuring scoring, personalization,
    and ranking execute asynchronously and save outputs to result_reference.
    """
    settings.USE_CELERY = False
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)
    
    _JOBS.clear()
    _CLOTHING_ITEMS.clear()

    # Prepopulate wardrobe items
    item_top = MockClothingItem("Tops", "shirt", "blue", "minimalist", 4, "standard")
    item_bottom = MockClothingItem("Bottoms", "pants", "black", "minimalist", 4, "standard")
    item_shoes = MockClothingItem("Shoes", "Sneakers", "white", "minimalist", 4, "standard")
    _CLOTHING_ITEMS.extend([item_top, item_bottom, item_shoes])

    # Mock Explainer Layer
    from app.recommendation.explainers.outfit_explainer import OutfitExplainer
    OutfitExplainer.explain_recommendations = lambda self, candidates, occ, seas: [
        {
            "score": 90,
            "items": [
                {"id": item_top.id, "category": "Tops", "subcategory": "shirt", "primary_color": "blue", "primary_color_hex": "#0000ff", "fit": "standard", "style": "minimalist", "formality": 4, "pattern": "solid"},
                {"id": item_bottom.id, "category": "Bottoms", "subcategory": "pants", "primary_color": "black", "primary_color_hex": "#000000", "fit": "standard", "style": "minimalist", "formality": 4, "pattern": "solid"},
                {"id": item_shoes.id, "category": "Shoes", "subcategory": "Sneakers", "primary_color": "white", "primary_color_hex": "#ffffff", "fit": "standard", "style": "minimalist", "formality": 4, "pattern": "solid"}
            ],
            "reasoning": "Classic minimalist coordination.",
            "template_name": "smart_casual",
            "breakdown": {"color_score": 90, "style_score": 90, "occasion_score": 90, "formality_score": 90, "season_score": 90}
        }
    ]

    # Register Mock DB Override
    app.dependency_overrides[get_db] = _smart_override_for_jobs(user)

    # Post outfit generation request
    resp = client.post(
        "/v1/jobs/generate-outfits",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "user_id": str(user.id),
            "occasion": "casual",
            "season": "summer"
        }
    )

    assert resp.status_code == 201, resp.json()
    job_id = resp.json()["job_id"]
    assert resp.json()["status"] == "queued"

    # Verify background execution results
    assert UUID(job_id) in _JOBS
    job = _JOBS[UUID(job_id)]
    assert job.status == "completed"
    assert job.progress == 100
    assert "outfits" in job.result_reference
    assert len(job.result_reference["outfits"]) == 1
    assert job.result_reference["outfits"][0]["score"] == 90

    app.dependency_overrides.pop(get_db, None)


# ── 3. Wardrobe Gap Analysis Job Mock Test ────────────────────────────────────
def test_gap_analysis_job_lifecycle():
    """
    Tests async wardrobe gap analysis background task execution.
    """
    settings.USE_CELERY = False
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)
    
    _JOBS.clear()
    _CLOTHING_ITEMS.clear()

    # Mock Gap Analysis calculations
    from app.recommendation.engines.gap_analysis import GapAnalysisEngine
    GapAnalysisEngine.analyze_gaps = lambda db_items: [
        {
            "missing_item": {"category": "outerwear", "subcategory": "blazer", "primary_color": "navy", "style": "classic", "formality": 7},
            "outfits_unlocked_count": 5,
            "unlocked_outfits_sample": []
        }
    ]

    app.dependency_overrides[get_db] = _smart_override_for_jobs(user)

    resp = client.post(
        "/v1/jobs/gap-analysis",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert resp.status_code == 201, resp.json()
    job_id = resp.json()["job_id"]
    assert UUID(job_id) in _JOBS
    job = _JOBS[UUID(job_id)]
    
    assert job.status == "completed"
    assert "gaps" in job.result_reference
    assert len(job.result_reference["gaps"]) == 1

    app.dependency_overrides.pop(get_db, None)


# ── 4. Endpoint: Get Job Status ───────────────────────────────────────────────
def test_get_job_status():
    """
    Tests GET /v1/jobs/{job_id} endpoint status mapping.
    """
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)

    _JOBS.clear()

    # Manually register a job in our mock database store
    job_uuid = uuid.uuid4()
    mock_job = BackgroundJob(
        id=job_uuid,
        user_id=user.id,
        job_type="outfit_generation_job",
        status="processing",
        progress=45,
        created_at=datetime.now(timezone.utc)
    )
    _JOBS[job_uuid] = mock_job

    app.dependency_overrides[get_db] = _smart_override_for_jobs(user)

    resp = client.get(
        f"/v1/jobs/{job_uuid}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["job_id"] == str(job_uuid)
    assert body["status"] == "processing"
    assert body["progress"] == 45
    assert body["job_type"] == "outfit_generation_job"


# ── 5. Endpoint: Cancel Background Job ────────────────────────────────────────
def test_cancel_job():
    """
    Tests POST /v1/jobs/{job_id}/cancel endpoint.
    Verifies state updates to cancelled, blocking final results.
    """
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)

    _JOBS.clear()

    job_uuid = uuid.uuid4()
    mock_job = BackgroundJob(
        id=job_uuid,
        user_id=user.id,
        job_type="clothing_processing_job",
        status="queued",
        progress=0,
        created_at=datetime.now(timezone.utc)
    )
    _JOBS[job_uuid] = mock_job

    app.dependency_overrides[get_db] = _smart_override_for_jobs(user)

    # Trigger cancellation
    resp = client.post(
        f"/v1/jobs/{job_uuid}/cancel",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert resp.status_code == 200, resp.json()
    assert resp.json()["success"] is True

    # Assert status updated to cancelled in the memory store
    assert _JOBS[job_uuid].status == "cancelled"

    app.dependency_overrides.pop(get_db, None)


# ── 6. Task: Stuck Job Recovery (Reaper) ───────────────────────────────────────
def test_dead_job_recovery():
    """
    Tests stuck job recovery task.
    Creates a stuck job older than 1 hour, runs reaper task, and asserts it is marked failed.
    """
    user = MockUser()
    
    _JOBS.clear()

    # Create two jobs:
    # 1. Stuck job (processing, created 2 hours ago) -> should fail
    # 2. Healthy job (processing, created 5 min ago) -> should remain unchanged
    
    stuck_id = uuid.uuid4()
    stuck_job = BackgroundJob(
        id=stuck_id,
        user_id=user.id,
        job_type="clothing_processing_job",
        status="processing",
        progress=30,
        created_at=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    
    healthy_id = uuid.uuid4()
    healthy_job = BackgroundJob(
        id=healthy_id,
        user_id=user.id,
        job_type="clothing_processing_job",
        status="processing",
        progress=30,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    
    _JOBS[stuck_id] = stuck_job
    _JOBS[healthy_id] = healthy_job

    app.dependency_overrides[get_db] = _smart_override_for_jobs(user)

    # Run the dead job recovery reaper task (sync execution)
    dead_job_recovery_job()

    app.dependency_overrides.pop(get_db, None)

    # Verify Stuck job was reclaimed
    assert _JOBS[stuck_id].status == "failed"
    assert "timed out" in _JOBS[stuck_id].error_message
    assert _JOBS[stuck_id].completed_at is not None

    # Verify Healthy job remains active
    assert _JOBS[healthy_id].status == "processing"
    assert _JOBS[healthy_id].completed_at is None
