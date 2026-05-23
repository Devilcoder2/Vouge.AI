import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

from app.main import app
from app.routes.processing import get_db

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
    # Construct massive mock payload exceeding 10MB (10.5MB)
    large_payload = mock_image_bytes + (b"0" * (11 * 1024 * 1024))
    
    response = client.post(
        "/upload-image",
        files={"file": ("huge_garment.png", large_payload, "image/png")}
    )
    # 413 is Request Entity Too Large
    assert response.status_code == 413
    assert "exceeds maximum size" in response.json()["detail"]

def test_process_clothing_flow(mock_image_bytes, monkeypatch):
    """
    Tests the complete end-to-end processing pipeline flow.
    We mock the database session because we test API routing in isolation here.
    """
    # Create mock DB session dependencies for independent API route testing
    async def mock_get_db():
        class MockDB:
            async def commit(self): pass
            async def refresh(self, obj): pass
            def add(self, obj):
                import uuid
                from datetime import datetime
                obj.id = uuid.uuid4()
                obj.created_at = datetime.utcnow()
        yield MockDB()
        
    app.dependency_overrides[get_db] = mock_get_db

    # Mock the slow background removal U2-Net process
    from PIL import Image
    monkeypatch.setattr(
        "app.services.pipeline.BackgroundRemover.remove_background",
        lambda raw_bytes: Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    )
    
    # Mock the Gemini Generative AI vision classifier
    from app.schemas.processing import FashionMetadataExtract
    monkeypatch.setattr(
        "app.services.pipeline.FashionClassifier.classify_garment",
        lambda self, pil_img, filename_hint="": FashionMetadataExtract(
            category="Tops",
            subcategory="T-Shirts & Tanks",
            fit="standard",
            style="minimalist",
            formality=3,
            seasons=["spring", "summer"],
            pattern="solid",
            primary_color="white",
            secondary_colors=[]
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
    assert data["category"] == "Tops"
    assert data["subcategory"] == "T-Shirts & Tanks"
    assert "primary_color" in data
    assert "pattern" in data
    assert data["embedding_generated"] is True
    assert "processed_image_url" in data
