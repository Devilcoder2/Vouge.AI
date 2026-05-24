import io
import os
import uuid
from uuid import UUID
from datetime import datetime, timezone
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.config import settings
from app.auth.security import create_access_token
from app.database.models import User, ClothingItem
from app.database.session import get_db
import app.tasks as tasks_module
from app.services.storage_service import StorageService
from app.services.image_optimizer import ImageOptimizer

client = TestClient(app)

# ── Shared Test Constants & Helper Classes ──────────────────────────────────────
class MockUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.email = "media_tests@vouge.ai"
        self.username = "media_user"
        self.is_active = True
        self.onboarding_completed = True

_DB_ITEMS = []


class MediaMockDB:
    def __init__(self, current_user):
        self.current_user = current_user
        self._added = []

    def add(self, obj):
        self._added.append(obj)

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()
        if "from users" in stmt_str:
            return _MockResult(self.current_user)
        elif "from clothing_items" in stmt_str:
            return _MockResult(_DB_ITEMS)
        return _MockResult(None)

    async def commit(self):
        for obj in self._added:
            if isinstance(obj, ClothingItem):
                if not getattr(obj, "id", None):
                    obj.id = uuid.uuid4()
                _DB_ITEMS.append(obj)
        self._added.clear()

    async def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class _MockResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return self._value if isinstance(self._value, list) else [self._value]


def _smart_override_for_media(current_user: MockUser):
    async def mock_get_db():
        yield MediaMockDB(current_user)

    tasks_module.AsyncSessionLocal = lambda: MediaMockDB(current_user)
    return mock_get_db


@pytest.fixture(autouse=True)
def clean_media_test_state():
    """Wipes global dicts and restores all monkeypatched task handlers."""
    _DB_ITEMS.clear()
    
    # Save original references
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


# ── 1. Secure Image Validation Firewall Tests ──────────────────────────────
def test_image_mime_and_corruptions_validation():
    """
    Verifies MIME validation rejects invalid types (PDF) and Pillow validation
    detects corrupted bytes.
    """
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)
    app.dependency_overrides[get_db] = _smart_override_for_media(user)

    # A. Validate invalid MIME type rejection
    resp = client.post(
        "/v1/media/request-upload-url",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "filename": "document.pdf",
            "content_type": "application/pdf",
            "folder": "raw"
        }
    )
    assert resp.status_code == 400
    assert "Invalid MIME type" in resp.json()["detail"]

    # B. Validate invalid folder path rejection
    resp = client.post(
        "/v1/media/request-upload-url",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "filename": "shirt.png",
            "content_type": "image/png",
            "folder": "invalid_folder"
        }
    )
    assert resp.status_code == 400
    assert "Invalid folder destination" in resp.json()["detail"]

    # C. Validate ImageOptimizer detects corrupted bytes
    with pytest.raises(ValueError) as exc:
        ImageOptimizer.validate_and_load(b"invalid truncated image bytes")
    assert "Corrupted or invalid image" in str(exc.value)

    app.dependency_overrides.pop(get_db, None)


# ── 2. Local Direct PUT Upload Simulation End-To-End ─────────────────────────
def test_local_presigned_upload_and_stream_receiver():
    """
    Simulates direct presigned PUT upload end-to-end in offline local fallback mode.
    """
    settings.USE_S3 = False
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)
    app.dependency_overrides[get_db] = _smart_override_for_media(user)

    # A. Request upload URL
    resp = client.post(
        "/v1/media/request-upload-url",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "filename": "my_tshirt.png",
            "content_type": "image/png",
            "folder": "raw"
        }
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "upload-local/raw/" in body["upload_url"]
    assert "file/raw/" in body["download_url"]

    # B. Perform simulated direct PUT upload stream using the generated URL
    # Create simple solid color PNG image bytes
    img = Image.new("RGBA", (100, 100), color="blue")
    img_io = io.BytesIO()
    img.save(img_io, format="PNG")
    img_bytes = img_io.getvalue()

    # Extract path suffix from mock URL to hit client directly
    local_put_endpoint = body["upload_url"].split("http://localhost:8000")[1]
    
    put_resp = client.put(local_put_endpoint, content=img_bytes)
    assert put_resp.status_code == 200
    assert put_resp.json()["success"] is True

    # C. Verify saved locally
    saved_filename = local_put_endpoint.split("/")[-1]
    local_filepath = settings.UPLOAD_DIR / "raw" / saved_filename
    assert local_filepath.exists()
    assert local_filepath.stat().st_size == len(img_bytes)

    # Cleanup local write
    local_filepath.unlink(missing_ok=True)
    app.dependency_overrides.pop(get_db, None)


# ── 3. Pillow Variants Image Optimization Scaling ──────────────────────────────
def test_pillow_variant_resolutions():
    """
    Tests ImageOptimizer outputs correctly scaled thumbnails, mobile, and web variant dimensions.
    """
    # Create high-resolution image
    high_res_img = Image.new("RGB", (2000, 1000), color="red")
    img_io = io.BytesIO()
    high_res_img.save(img_io, format="JPEG")
    raw_bytes = img_io.getvalue()

    # Generate variants
    variants = ImageOptimizer.generate_variants(raw_bytes)

    assert "thumbnail" in variants
    assert "mobile" in variants
    assert "web" in variants

    # A. Validate thumbnail (150x150 exact square crop aspect)
    thumb_img = Image.open(io.BytesIO(variants["thumbnail"]))
    assert thumb_img.size == (150, 150)

    # B. Validate mobile (scaled down to max-width 750px)
    mobile_img = Image.open(io.BytesIO(variants["mobile"]))
    assert mobile_img.size[0] == 750
    assert mobile_img.size[1] == 375  # Aspect ratio 2:1 locked perfectly

    # C. Validate web (scaled down to max-width 1200px)
    web_img = Image.open(io.BytesIO(variants["web"]))
    assert web_img.size[0] == 1200
    assert web_img.size[1] == 600  # Aspect ratio 2:1 locked perfectly


# ── 4. Storage Service Cloud S3 Mocking ──────────────────────────────────────────
@patch("boto3.client")
def test_cloud_s3_upload_mock(mock_boto_client):
    """
    Verifies boto3 integration is called correctly when USE_S3 = True.
    """
    settings.USE_S3 = True
    settings.AWS_ACCESS_KEY_ID = "test_access_key"
    settings.AWS_SECRET_ACCESS_KEY = "test_secret_key"
    settings.AWS_S3_BUCKET_NAME = "vouge-testing"
    settings.AWS_S3_REGION_NAME = "eu-west-1"
    settings.CDN_BASE_URL = "https://cdn.vouge.ai"

    # Mock S3 Client returned by boto3
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    # Generate presigned upload URL
    mock_s3.generate_presigned_url.return_value = "https://s3.signed-url.com/put"

    storage = StorageService()
    assert storage.use_s3 is True

    # Validate presigned upload url generation
    upload_url = storage.generate_presigned_upload_url("raw", "garment.jpg", "image/jpeg")
    assert upload_url == "https://s3.signed-url.com/put"
    mock_s3.generate_presigned_url.assert_called_once_with(
        ClientMethod="put_object",
        Params={
            "Bucket": "vouge-testing",
            "Key": "raw/garment.jpg",
            "ContentType": "image/jpeg"
        },
        ExpiresIn=3600
    )

    # Validate upload file
    mock_data = b"image_data_bytes"
    cdn_url = storage.upload_file(mock_data, "processed", "garment.png", "image/png")
    assert cdn_url == "https://cdn.vouge.ai/processed/garment.png"
    mock_s3.put_object.assert_called_once_with(
        Bucket="vouge-testing",
        Key="processed/garment.png",
        Body=mock_data,
        ContentType="image/png"
    )

    # Reset configuration variables to local development mode defaults
    settings.USE_S3 = False


# ── 5. Full Asynchronous Processing Pipeline URL Mappings ─────────────────────────
@pytest.mark.anyio
async def test_clothing_pipeline_stores_variant_urls():
    """
    E2E integration test: runs async garment background processing, verifying that
    ImageOptimizer, S3 Storage client, and PostgreSQL updates populate variant URL columns.
    """
    settings.USE_S3 = False
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)

    # Mock all heavy AI pipeline models
    from app.ai.background_removal import BackgroundRemover
    from app.ai.preprocessing import ImagePreprocessor
    from app.ai.classifier import FashionClassifier
    from app.schemas.processing import FashionMetadataExtract, ConfidenceStringField
    from app.ai.color_extractor import ColorExtractor
    from app.ai.embedding_service import FashionEmbeddingService
    from app.services.duplicate_detector import DuplicateDetector

    # Create standard solid PNG bytes
    img = Image.new("RGBA", (300, 300), color="green")
    img_io = io.BytesIO()
    img.save(img_io, format="PNG")
    img_bytes = img_io.getvalue()

    # Save to raw uploads mock filepath
    job_uuid = uuid.uuid4()
    raw_filename = f"{job_uuid}_raw.png"
    raw_filepath = settings.UPLOAD_DIR / "raw" / raw_filename
    with open(raw_filepath, "wb") as f:
        f.write(img_bytes)

    # Set up AI Mocks
    BackgroundRemover.remove_background = lambda b: img_bytes
    ImagePreprocessor.preprocess_image = lambda i, target_size: img
    
    mock_metadata = FashionMetadataExtract(
        category=ConfidenceStringField(value="Tops", confidence=0.9),
        subcategory=ConfidenceStringField(value="tee", confidence=0.9),
        fit=ConfidenceStringField(value="standard", confidence=0.9),
        style=ConfidenceStringField(value="minimalist", confidence=0.9),
        pattern=ConfidenceStringField(value="solid", confidence=0.9),
        formality=3,
        seasons=["summer"],
        primary_color="green",
        secondary_colors=[],
        detected_items_count=1
    )
    FashionClassifier.classify_garment = lambda self, img, filename_hint: mock_metadata
    ColorExtractor.extract_colors = lambda img: ("green", [], "#00ff00", [])
    FashionEmbeddingService.generate_image_embedding = lambda self, img: [0.1] * 512
    FashionEmbeddingService.save_embedding_to_disk = lambda emb, stem: "embeddings/fake.npy"
    DuplicateDetector.calculate_dhash = lambda img: "fake_dhash"
    DuplicateDetector.check_duplicates = lambda img, emb, existing: (False, None)

    # Set DB Overrides
    _smart_override_for_media(user)

    # Run the raw background garment task directly
    await tasks_module.run_async_clothing_processing(job_uuid, str(raw_filepath), user.id)

    # Assert database populated URL fields
    assert len(_DB_ITEMS) == 1
    db_item = _DB_ITEMS[0]

    assert db_item.original_image_url is not None
    assert db_item.processed_image_url is not None
    assert db_item.thumbnail_url is not None
    assert db_item.preview_url is not None

    assert "/v1/media/file/raw/" in db_item.original_image_url
    assert "/v1/media/file/processed/" in db_item.processed_image_url
    assert "/v1/media/file/thumbnails/" in db_item.thumbnail_url
    assert "/v1/media/file/previews/" in db_item.preview_url

    # Cleanup local raw file
    raw_filepath.unlink(missing_ok=True)
    # Cleanup variant local files generated by storage client fallback
    processed_file = settings.UPLOAD_DIR / "processed" / f"{job_uuid}_raw_processed.png"
    thumb_file = settings.UPLOAD_DIR / "thumbnails" / f"{job_uuid}_raw_thumb.png"
    preview_file = settings.UPLOAD_DIR / "previews" / f"{job_uuid}_raw_preview.png"
    processed_file.unlink(missing_ok=True)
    thumb_file.unlink(missing_ok=True)
    preview_file.unlink(missing_ok=True)
