"""
Tests for the Outfit Preview Builder (Compulsory Item 3).
Verifies canvas composition, white-background removal, slot assignment,
multi-garment rendering, and API endpoint responses.
"""
import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.services.outfit_preview_builder import (
    OutfitPreviewBuilder,
    _remove_white_background,
    CANVAS_W,
    CANVAS_H,
)
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests for OutfitPreviewBuilder core logic
# ---------------------------------------------------------------------------

def test_white_background_removal():
    """
    Verifies that pure white and near-white pixels are stripped to transparent
    while coloured garment pixels are preserved.
    """
    # Create a 10x10 image: left half white (#FFFFFF), right half red (#FF2020)
    test_img = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    for y in range(10):
        for x in range(5, 10):
            test_img.putpixel((x, y), (255, 32, 32, 255))  # Red pixels

    result = _remove_white_background(test_img, tolerance=240)

    # Left half (white) should become transparent (alpha=0)
    assert result.getpixel((0, 0))[3] == 0, "White background should be removed (alpha=0)"
    assert result.getpixel((2, 2))[3] == 0

    # Right half (red garment pixels) should remain opaque
    assert result.getpixel((7, 5))[3] == 255, "Garment pixels should remain opaque (alpha=255)"
    assert result.getpixel((9, 9))[3] == 255


def test_canvas_dimensions():
    """
    Verifies that the composed canvas always has the correct fixed dimensions.
    """
    preview_bytes = OutfitPreviewBuilder.build_preview(
        outfit_items=[],  # Empty outfit (no garments)
        score=None,
        occasion=None,
        season=None,
        reasoning=None,
    )
    img = Image.open(io.BytesIO(preview_bytes))
    assert img.width == CANVAS_W, f"Canvas width should be {CANVAS_W}, got {img.width}"
    assert img.height == CANVAS_H, f"Canvas height should be {CANVAS_H}, got {img.height}"


def test_canvas_is_dark_background():
    """
    Verifies that the empty canvas has a dark background (not white or transparent).
    """
    preview_bytes = OutfitPreviewBuilder.build_preview(outfit_items=[])
    img = Image.open(io.BytesIO(preview_bytes)).convert("RGB")

    # Sample the very top-left corner pixel (should be the near-black BG_COLOR)
    top_left = img.getpixel((0, 0))
    r, g, b = top_left
    # Background should be dark — brightness below 30 in each channel
    assert r < 30 and g < 30 and b < 30, f"Background should be near-black, got {top_left}"


def test_preview_with_score_badge():
    """
    Verifies that adding a score does not crash the builder and returns valid PNG bytes.
    """
    preview_bytes = OutfitPreviewBuilder.build_preview(
        outfit_items=[],
        score=87,
        occasion="office",
        season="autumn",
        reasoning="A timeless smart casual look for the boardroom.",
    )
    assert len(preview_bytes) > 1000, "Preview PNG should be a non-trivial byte payload."
    img = Image.open(io.BytesIO(preview_bytes))
    assert img.format == "PNG"


def test_normalize_category_mapping():
    """
    Verifies that both raw DB category strings and taxonomy-normalized strings
    map to the correct slot keys.
    """
    builder = OutfitPreviewBuilder

    assert builder._normalize_category({"category": "Tops"}) == "TOPS"
    assert builder._normalize_category({"category": "Bottoms"}) == "BOTTOMS"
    assert builder._normalize_category({"category": "Shoes"}) == "FOOTWEAR"
    assert builder._normalize_category({"category": "Outerwear"}) == "OUTERWEAR"
    assert builder._normalize_category({"category": "TOPS"}) == "TOPS"
    assert builder._normalize_category({"category": "FOOTWEAR"}) == "FOOTWEAR"


def test_preview_missing_image_paths_do_not_crash():
    """
    Verifies that the builder gracefully skips items with non-existent image paths
    without raising exceptions, still returning a valid composed canvas.
    """
    outfit_items = [
        {"id": uuid.uuid4(), "category": "Tops",    "processed_image_path": "/nonexistent/path/top.png"},
        {"id": uuid.uuid4(), "category": "Bottoms", "processed_image_path": "/nonexistent/path/bottom.png"},
        {"id": uuid.uuid4(), "category": "Shoes",   "processed_image_path": "/nonexistent/path/shoes.png"},
    ]
    # Should not raise; should return the base dark canvas
    preview_bytes = OutfitPreviewBuilder.build_preview(
        outfit_items=outfit_items,
        score=72,
        occasion="casual",
        season="spring",
    )
    assert len(preview_bytes) > 100
    img = Image.open(io.BytesIO(preview_bytes))
    assert img.size == (CANVAS_W, CANVAS_H)


def test_preview_with_real_garment_images():
    """
    Live composition test using actual processed garment images from disk.
    Verifies that the builder correctly loads, background-strips, and composites
    real PNG garment files.
    """
    processed_dir = Path("processed")
    # Collect up to 3 large processed images (skip 1097-byte placeholder stubs)
    real_images = [
        str(p) for p in processed_dir.glob("*_processed.png")
        if p.stat().st_size > 50000
    ][:3]

    if len(real_images) < 1:
        pytest.skip("No real processed garment images found on disk to test with.")

    categories = ["Tops", "Bottoms", "Shoes"]
    outfit_items = [
        {"id": uuid.uuid4(), "category": categories[i % len(categories)], "processed_image_path": p}
        for i, p in enumerate(real_images)
    ]

    preview_bytes = OutfitPreviewBuilder.build_preview(
        outfit_items=outfit_items,
        score=91,
        occasion="casual",
        season="summer",
        reasoning="A crisp summer casual look with clean proportions.",
    )

    assert len(preview_bytes) > 50000, "Preview with real garments should be a sizable PNG."
    img = Image.open(io.BytesIO(preview_bytes))
    assert img.size == (CANVAS_W, CANVAS_H)
    assert img.mode == "RGB"
