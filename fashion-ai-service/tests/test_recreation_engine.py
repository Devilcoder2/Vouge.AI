import pytest
import numpy as np
import uuid
from pathlib import Path
from unittest.mock import MagicMock

from app.services.recreation import OutfitRecreationService
from app.database.models import ClothingItem, PostTaggedItem

def test_hex_to_hsl_conversion():
    """Verifies that hexadecimal color strings map to accurate HSL channels."""
    # White hex
    h, s, l = OutfitRecreationService.hex_to_hsl("#FFFFFF")
    assert round(l, 1) == 100.0
    assert round(s, 1) == 0.0

    # Red hex
    h, s, l = OutfitRecreationService.hex_to_hsl("#FF0000")
    assert round(h, 1) == 0.0
    assert round(s, 1) == 100.0
    assert round(l, 1) == 50.0

    # Navy hex
    h, s, l = OutfitRecreationService.hex_to_hsl("#000080")
    assert round(h, 1) == 240.0
    assert round(s, 1) == 100.0
    assert round(l, 1) == 25.1


def test_circular_hsl_distance():
    """Verifies HSL distance metrics handle circular hue looped boundaries correctly."""
    # Hues 5 and 355 are only 10 degrees apart circular, but 350 degrees apart linear.
    # Our circular math should find a very low distance!
    hsl1 = (5.0, 100.0, 50.0)
    hsl2 = (355.0, 100.0, 50.0)
    
    distance = OutfitRecreationService.calculate_hsl_distance(hsl1, hsl2)
    assert distance < 0.10  # High compatibility index


def test_cosine_similarity_calculation():
    """Verifies cosine vector dot products."""
    vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    # Identical vectors
    assert OutfitRecreationService.calculate_cosine_similarity(vec1, vec2) == 1.0
    
    # Orthogonal vectors
    assert OutfitRecreationService.calculate_cosine_similarity(vec1, vec3) == 0.0


def test_recreate_slot_matching(monkeypatch):
    """
    Verifies that OutfitRecreationService maps appropriate matched items 
    and classifies threshold substitute values correctly.
    """
    import asyncio

    async def run_test():
        # 1. Setup mock items
        creator_item = ClothingItem(
            id=uuid.uuid4(),
            category="Tops",
            subcategory="T-Shirts & Tanks",
            primary_color="navy",
            primary_color_hex="#000080",
            embedding_path="mock_creator_embed.npy"
        )
        
        user_matching_item = ClothingItem(
            id=uuid.uuid4(),
            category="Tops",
            subcategory="T-Shirts & Tanks",
            primary_color="navy",
            primary_color_hex="#000080",
            embedding_path="mock_user_embed.npy"
        )
        
        tagged_item = PostTaggedItem(
            id=uuid.uuid4(),
            wardrobe_item=creator_item
        )

        # 2. Mock database execution session returning our matching wardrobe item candidate
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self_scalars):
                        return [user_matching_item]
                return MockScalars()

        class MockDB:
            async def execute(self, stmt):
                return MockResult()

        # 3. Mock file loader loading mock CLIP embedding float32 arrays
        mock_vec = np.ones(512, dtype=np.float32)
        monkeypatch.setattr(
            "app.services.recreation.FashionEmbeddingService.load_embedding_from_disk",
            lambda filepath: mock_vec
        )
        
        monkeypatch.setattr(
            "app.services.recreation.Path.exists",
            lambda filepath: True
        )

        # 4. Trigger recreation matching
        match, score, status = await OutfitRecreationService.match_tagged_item_to_wardrobe(
            tagged_item=tagged_item,
            user_id="default_user",
            db=MockDB()
        )

        # 5. Assertions
        assert match.id == user_matching_item.id
        assert score == 1.0  # Identical mock arrays
        assert status == "Perfect Match"

    asyncio.run(run_test())
