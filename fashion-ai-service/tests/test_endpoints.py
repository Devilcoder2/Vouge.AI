import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io
import uuid
from datetime import datetime, timezone

from app.main import app
from app.routes.processing import get_db
from app.schemas.processing import FashionMetadataExtract, ConfidenceStringField

client = TestClient(app)

@pytest.fixture
def mock_image_bytes():
    """Generates 1x1 transparent pixel PNG bytes for clean uploads."""
    # Standard 1x1 transparent PNG hex representation
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000b49444154789ccb606060000000050001a5f645400000000049454e44ae426082"
    )

def test_health_endpoint():
    """Verifies that the /health endpoint is alive and reporting status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "database_connected" in data

def test_upload_image_only(mock_image_bytes):
    """Verifies basic image upload validates and writes raw file to disk (Step 4 requirement)."""
    response = client.post(
        "/upload-image",
        files={"file": ("test_shirt.png", mock_image_bytes, "image/png")}
    )
    assert response.status_code == 201
    data = response.json()
    assert "saved_path" in data
    assert "test_shirt.png" in data["filename"]
    
    # Verify local file was written
    saved_path = Path(data["saved_path"])
    assert saved_path.exists()
    
    # Clean up written file
    saved_path.unlink()

def test_upload_invalid_extension():
    """Verifies that the file handler strictly rejects unsupported file extensions."""
    response = client.post(
        "/upload-image",
        files={"file": ("bad_format.txt", b"arbitrary text data", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

def test_upload_exceeding_size(mock_image_bytes):
    """Verifies that the file handler strictly rejects uploads larger than 10MB."""
    # Construct massive mock payload exceeding 10MB (11MB)
    large_payload = mock_image_bytes + (b"0" * (11 * 1024 * 1024))
    
    response = client.post(
        "/upload-image",
        files={"file": ("huge_garment.png", large_payload, "image/png")}
    )
    # 413 is Request Entity Too Large / Content Too Large
    assert response.status_code == 413
    assert "exceeds maximum size" in response.json()["detail"]

def test_process_clothing_flow(mock_image_bytes, monkeypatch):
    """
    Tests the complete end-to-end processing pipeline flow.
    We mock the database session because we test API routing in isolation here.
    """
    # Create mock DB session dependencies for independent API route testing
    async def mock_get_db():
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return []  # Return empty list of existing items for duplicate check
                return MockScalars()
        class MockDB:
            async def execute(self, stmt):
                return MockResult()
            async def commit(self): pass
            async def refresh(self, obj): pass
            def add(self, obj):
                obj.id = uuid.uuid4()
                obj.created_at = datetime.now(timezone.utc)
        yield MockDB()
        
    app.dependency_overrides[get_db] = mock_get_db

    # Mock the slow background removal U2-Net process
    from PIL import Image
    monkeypatch.setattr(
        "app.services.pipeline.BackgroundRemover.remove_background",
        lambda raw_bytes: Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    )
    
    # Mock the Gemini Generative AI vision classifier returning Pydantic schema with confidence
    monkeypatch.setattr(
        "app.services.pipeline.FashionClassifier.classify_garment",
        lambda self, pil_img, filename_hint="": FashionMetadataExtract(
            category=ConfidenceStringField(value="Tops", confidence=0.98),
            subcategory=ConfidenceStringField(value="T-Shirts & Tanks", confidence=0.95),
            fit=ConfidenceStringField(value="standard", confidence=0.90),
            style=ConfidenceStringField(value="minimalist", confidence=0.88),
            pattern=ConfidenceStringField(value="solid", confidence=0.99),
            formality=3,
            seasons=["spring", "summer"],
            primary_color="white",
            secondary_colors=[],
            detected_items_count=1
        )
    )
    
    # Mock the OpenCV KMeans color extraction step
    monkeypatch.setattr(
        "app.services.pipeline.ColorExtractor.extract_colors",
        lambda pil_img: ("white", [], "#ffffff", [])
    )
    
    # Mock the local PyTorch CLIP embedding generator
    import numpy as np
    monkeypatch.setattr(
        "app.services.pipeline.FashionEmbeddingService.generate_image_embedding",
        lambda self, pil_img: np.zeros(512, dtype=np.float32)
    )

    response = client.post(
        "/process-clothing",
        files={"file": ("casual_striped_shirt.png", mock_image_bytes, "image/png")}
    )
    
    # Clean overrides
    app.dependency_overrides.clear()
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    
    # Verify new nested structure
    assert data["category"]["value"] == "Tops"
    assert data["category"]["confidence"] == 0.98
    assert data["subcategory"]["value"] == "T-Shirts & Tanks"
    assert data["subcategory"]["confidence"] == 0.95
    assert data["fit"]["value"] == "standard"
    assert data["fit"]["confidence"] == 0.90
    assert data["style"]["value"] == "minimalist"
    
    assert data["primary_color"] == "white"
    assert data["primary_color_hex"] == "#ffffff"
    assert data["prompt_version"] == "v1.0.0"
    assert data["detected_items_count"] == 1
    assert data["is_duplicate"] is False
    assert data["embedding_generated"] is True

def test_process_clothing_flow_multi_item_rejection(mock_image_bytes, monkeypatch):
    """
    Tests that the pipeline strictly rejects uploads where Gemini detects multiple items (> 1).
    """
    async def mock_get_db():
        class MockDB:
            def add(self, obj): pass
        yield MockDB()
        
    app.dependency_overrides[get_db] = mock_get_db

    # Mock the background removal U2-Net process
    from PIL import Image
    monkeypatch.setattr(
        "app.services.pipeline.BackgroundRemover.remove_background",
        lambda raw_bytes: Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    )
    
    # Mock the Gemini classifier returning detected_items_count = 3 (an outfit/flat-lay)
    monkeypatch.setattr(
        "app.services.pipeline.FashionClassifier.classify_garment",
        lambda self, pil_img, filename_hint="": FashionMetadataExtract(
            category=ConfidenceStringField(value="Tops", confidence=0.98),
            subcategory=ConfidenceStringField(value="T-Shirts & Tanks", confidence=0.95),
            fit=ConfidenceStringField(value="standard", confidence=0.90),
            style=ConfidenceStringField(value="minimalist", confidence=0.88),
            pattern=ConfidenceStringField(value="solid", confidence=0.99),
            formality=3,
            seasons=["spring", "summer"],
            primary_color="white",
            secondary_colors=[],
            detected_items_count=3
        )
    )

    response = client.post(
        "/process-clothing",
        files={"file": ("wardrobe_outfit_lay.png", mock_image_bytes, "image/png")}
    )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 400
    assert "Detected 3 clothing items. Please upload one item only." in response.json()["detail"]

def test_patch_clothing_item(monkeypatch):
    """
    Verifies that PATCH /items/{id} correctly overlays metadata edits,
    validates values against the fashion taxonomy, and resets confidence scores to 1.0.
    """
    test_id = uuid.uuid4()
    
    # Define a mock clothing item in the database
    class MockClothingItemModel:
        def __init__(self):
            self.id = test_id
            self.category = "Tops"
            self.confidence_category = 0.85
            self.subcategory = "T-Shirts & Tanks"
            self.confidence_subcategory = 0.90
            self.primary_color = "white"
            self.primary_color_hex = "#ffffff"
            self.secondary_colors = []
            self.secondary_colors_hex = []
            self.fit = "standard"
            self.confidence_fit = 0.92
            self.style = "minimalist"
            self.confidence_style = 0.88
            self.formality = 3
            self.seasons = ["spring", "summer"]
            self.pattern = "solid"
            self.confidence_pattern = 0.99
            self.prompt_version = "v1.0.0"
            self.detected_items_count = 1
            self.is_duplicate = False
            self.duplicate_of_id = None
            self.created_at = datetime.now(timezone.utc)
            self.embedding_path = "mock_path.npy"

    mock_item = MockClothingItemModel()

    async def mock_get_db():
        class MockResult:
            def scalar_one_or_none(self):
                return mock_item
        class MockDB:
            async def execute(self, stmt):
                return MockResult()
            async def commit(self): pass
            async def refresh(self, obj): pass
        yield MockDB()

    app.dependency_overrides[get_db] = mock_get_db

    # Correcting fit to 'oversized' and style to 'streetwear'
    patch_payload = {
        "fit": "oversized",
        "style": "streetwear"
    }

    response = client.patch(f"/items/{test_id}", json=patch_payload)
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    
    # Assert values are updated and confidence is reset to 1.0 for edited fields
    assert data["fit"]["value"] == "oversized"
    assert data["fit"]["confidence"] == 1.0
    assert data["style"]["value"] == "streetwear"
    assert data["style"]["confidence"] == 1.0
    
    # Assert non-edited fields retain their previous values and confidences
    assert data["category"]["value"] == "Tops"
    assert data["category"]["confidence"] == 0.85
    assert data["subcategory"]["value"] == "T-Shirts & Tanks"
    assert data["subcategory"]["confidence"] == 0.90

def test_patch_clothing_item_invalid_taxonomy(monkeypatch):
    """
    Verifies that PATCH /items/{id} strictly rejects values violating the Central Taxonomy.
    """
    test_id = uuid.uuid4()
    
    class MockClothingItemModel:
        def __init__(self):
            self.id = test_id
            self.category = "Tops"
            self.confidence_category = 0.95
            self.subcategory = "T-Shirts & Tanks"
            self.confidence_subcategory = 0.95
            self.primary_color = "white"
            self.primary_color_hex = "#ffffff"
            self.secondary_colors = []
            self.secondary_colors_hex = []
            self.fit = "standard"
            self.confidence_fit = 0.95
            self.style = "minimalist"
            self.confidence_style = 0.95
            self.formality = 3
            self.seasons = ["spring", "summer"]
            self.pattern = "solid"
            self.confidence_pattern = 0.95
            self.prompt_version = "v1.0.0"
            self.detected_items_count = 1
            self.is_duplicate = False
            self.duplicate_of_id = None
            self.created_at = datetime.now(timezone.utc)
            self.embedding_path = "mock_path.npy"

    mock_item = MockClothingItemModel()

    async def mock_get_db():
        class MockResult:
            def scalar_one_or_none(self):
                return mock_item
        class MockDB:
            async def execute(self, stmt):
                return MockResult()
            async def commit(self): pass
            async def refresh(self, obj): pass
        yield MockDB()

    app.dependency_overrides[get_db] = mock_get_db

    # Passing invalid fit ('tight' is not in FITS taxonomy)
    patch_payload = {
        "fit": "tight"
    }

    response = client.patch(f"/items/{test_id}", json=patch_payload)
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 400
    assert "Taxonomy validation failed" in response.json()["detail"]
