import pytest
from fastapi.testclient import TestClient
import uuid
import numpy as np

from app.main import app
from app.routes.processing import get_db
from app.recommendation.engines.body_engine import BodyTypeEngine
from app.recommendation.engines.persona_engine import StylePersonaEngine
from app.recommendation.engines.feedback_engine import FeedbackEngine
from app.recommendation.engines.embedding_similarity_engine import EmbeddingSimilarityEngine
from app.recommendation.engines.silhouette_engine import SilhouetteEngine

client = TestClient(app)

# Helper fixtures for mock clothing items
@pytest.fixture
def mock_outfit_items():
    return [
        {
            "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
            "category": "TOPS",
            "subcategory": "Shirts & Blouses",
            "primary_color": "white",
            "primary_color_hex": "#ffffff",
            "fit": "oversized",
            "style": "classic",
            "formality": 6,
            "pattern": "solid",
            "embedding_path": "mock.npy"
        },
        {
            "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
            "category": "BOTTOMS",
            "subcategory": "Jeans",
            "primary_color": "blue",
            "primary_color_hex": "#1e3a8a",
            "fit": "slim",
            "style": "classic",
            "formality": 4,
            "pattern": "solid",
            "embedding_path": "mock.npy"
        },
        {
            "id": uuid.UUID("77777777-7777-7777-7777-777777777777"),
            "category": "FOOTWEAR",
            "subcategory": "Loafers & Slip-ons",
            "primary_color": "brown",
            "primary_color_hex": "#a52a2a",
            "fit": "standard",
            "style": "classic",
            "formality": 6,
            "pattern": "solid",
            "embedding_path": "mock.npy"
        }
    ]

# 1. Body Type Engine Tests
def test_body_engine_multipliers(mock_outfit_items):
    # Test 1: Tall lean profile should receive a boost for oversized top
    tall_profile = {
        "height_cm": 185,
        "body_archetype": "lean_tall",
        "fit_preference": "oversized"
    }
    res_tall = BodyTypeEngine.calculate_body_compatibility(mock_outfit_items, tall_profile)
    assert res_tall["score"] == 1.0  # Clipped at maximum 1.0

    # Test 2: Athletic profile with slim bottom gets a slight constraint penalty
    athletic_profile = {
        "height_cm": 175,
        "body_archetype": "athletic",
        "fit_preference": "standard"
    }
    res_ath = BodyTypeEngine.calculate_body_compatibility(mock_outfit_items, athletic_profile)
    assert res_ath["score"] < 1.0  # Penalty applied for slim fit pants
    assert "Slim-fit pants may feel restrictive" in res_ath["reason"]

# 2. Style Persona Engine Tests
def test_style_persona_matching(mock_outfit_items):
    # Test 1: Minimalist alignment
    res_min = StylePersonaEngine.calculate_persona_compatibility(mock_outfit_items, "minimalist")
    assert res_min["score"] == 1.0  # Items are minimalists/neutral
    assert "Perfect match for your preferred minimalist aesthetic." in res_min["why_selected"]

    # Test 2: Streetwear clash with formal oxford element
    clashing_items = list(mock_outfit_items)
    clashing_items[2] = dict(clashing_items[2], subcategory="oxfords & derby shoes")
    res_street = StylePersonaEngine.calculate_persona_compatibility(clashing_items, "streetwear")
    assert "Formal drape" in res_street["reason"]


# 3. Feedback / Preference Engine Tests
def test_feedback_penalization(mock_outfit_items):
    profile = {
        "avoided_colors": ["blue"],
        "favorite_styles": ["classic"]
    }
    
    # Avoided color (blue) is present in jeans; direct penalty
    res_fb = FeedbackEngine.calculate_feedback_adjustments(mock_outfit_items, profile, [])
    assert res_fb["adjustment_factor"] < 1.0
    assert "Contains blue, which is on your avoided colors list." in res_fb["reason"]

    # Mock historical feedback saving these items -> boosts score
    feedbacks = [
        {"feedback_type": "like", "outfit_item_ids": ["11111111-1111-1111-1111-111111111111"]}
    ]
    res_fb_history = FeedbackEngine.calculate_feedback_adjustments(mock_outfit_items, profile, feedbacks)
    # Adjustment factor reflects likes vs avoided color
    assert res_fb_history["adjustment_factor"] > 0.60

# 4. Embedding Similarity Engine Tests
def test_embedding_similarity_math(mock_outfit_items):
    res_harmony = EmbeddingSimilarityEngine.calculate_visual_harmony(mock_outfit_items)
    
    assert 0.0 <= res_harmony["score"] <= 1.0
    assert len(res_harmony["outfit_embedding"]) == 512
    # Unified embedding vector should be L2 normalized (length approx 1.0)
    norm = np.linalg.norm(res_harmony["outfit_embedding"])
    assert pytest.approx(norm, 0.01) == 1.0

# 5. Silhouette Proportions Balance Engine Tests
def test_silhouette_fit_proportions(mock_outfit_items):
    # Oversized top + slim bottom = Elegant contrast proportion
    res_sil = SilhouetteEngine.calculate_silhouette_balance(mock_outfit_items, "office", "minimalist")
    assert res_sil["score"] == 1.0
    assert "Elegant contrast proportion: oversized top balanced with slim bottoms." in res_sil["why_selected"]

    # Baggy-baggy fits (oversized + oversized) penalty
    baggy_items = list(mock_outfit_items)
    baggy_items[1] = dict(baggy_items[1], fit="oversized")
    res_baggy = SilhouetteEngine.calculate_silhouette_balance(baggy_items, "office", "minimalist")
    assert res_baggy["score"] < 1.0
    assert "swallow your silhouette proportions" in res_baggy["reason"]

# 6. End-to-End API Routes Integration Tests
def test_endpoints_profile_and_feedback(mock_outfit_items, monkeypatch):
    test_user_id = "test_engines_user"

    # Mock DB select returns representing items, profiles, and feedbacks
    class MockUserProfileModel:
        def __init__(self):
            self.id = uuid.uuid4()
            self.user_id = test_user_id
            self.height_cm = 185
            self.body_archetype = "lean_tall"
            self.fit_preference = "oversized"
            self.style_persona = "old_money"
            self.avoided_colors = ["red"]
            self.favorite_styles = ["classic"]
            self.created_at = None

    mock_profile = MockUserProfileModel()

    class MockClothingItem:
        def __init__(self):
            self.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
            self.category = "Tops"
            self.subcategory = "Shirts & Blouses"
            self.primary_color = "white"
            self.primary_color_hex = "#ffffff"
            self.secondary_colors = []
            self.fit = "oversized"
            self.style = "classic"
            self.formality = 6
            self.seasons = ["spring", "summer"]
            self.pattern = "solid"
            self.embedding_path = "mock.npy"

    mock_garment = MockClothingItem()

    async def mock_get_db():
        class MockResult:
            def __init__(self, query_str):
                self.query_str = query_str
            def scalars(self):
                class MockScalars:
                    def __init__(self, q): self.q = q
                    def all(self):
                        if "user_profiles" in self.q: return [mock_profile]
                        if "clothing_items" in self.q: return [mock_garment]
                        return []
                return MockScalars(self.query_str)
            def scalar_one_or_none(self):
                if "user_profiles" in self.query_str: return mock_profile
                return None
        class MockDB:
            async def execute(self, stmt): return MockResult(str(stmt))
            def add(self, obj): pass
            async def commit(self): pass
            async def refresh(self, obj): pass
        yield MockDB()

    app.dependency_overrides[get_db] = mock_get_db

    # A. Test POST /recommendations/profile
    profile_payload = {
        "user_id": test_user_id,
        "height_cm": 185,
        "body_archetype": "lean_tall",
        "fit_preference": "oversized",
        "style_persona": "old_money",
        "avoided_colors": ["red"],
        "favorite_styles": ["classic"]
    }
    resp_prof = client.post("/recommendations/profile", json=profile_payload)
    assert resp_prof.status_code == 200
    data_prof = resp_prof.json()
    assert data_prof["user_id"] == test_user_id
    assert data_prof["body_archetype"] == "lean_tall"

    # B. Test POST /recommendations/feedback
    feedback_payload = {
        "user_id": test_user_id,
        "outfit_item_ids": ["11111111-1111-1111-1111-111111111111"],
        "feedback_type": "like"
    }
    resp_fb = client.post("/recommendations/feedback", json=feedback_payload)
    assert resp_fb.status_code == 201
    assert "submitted successfully" in resp_fb.json()["message"]

    # C. Test POST /recommendations/generate-outfits returns personalized metadata
    outfits_payload = {
        "user_id": test_user_id,
        "occasion": "office",
        "season": "spring"
    }
    
    # We must patch CandidateGenerator to return a valid candidate outfit to bypass early pruning
    monkeypatch.setattr(
        "app.recommendation.generators.candidate_generator.CandidateGenerator.generate_candidates",
        lambda db_items, occ, season: [{
            "items": [
                {"id": uuid.UUID("11111111-1111-1111-1111-111111111111"), "category": "TOPS", "subcategory": "Shirts & Blouses", "primary_color": "white", "primary_color_hex": "#ffffff", "fit": "oversized", "style": "classic", "formality": 6, "pattern": "solid", "embedding_path": "mock.npy"},
                {"id": uuid.UUID("44444444-4444-4444-4444-444444444444"), "category": "BOTTOMS", "subcategory": "Chinos & Trousers", "primary_color": "beige", "primary_color_hex": "#f5f5dc", "fit": "slim", "style": "classic", "formality": 6, "pattern": "solid", "embedding_path": "mock.npy"},
                {"id": uuid.UUID("77777777-7777-7777-7777-777777777777"), "category": "FOOTWEAR", "subcategory": "Loafers & Slip-ons", "primary_color": "brown", "primary_color_hex": "#a52a2a", "fit": "standard", "style": "classic", "formality": 6, "pattern": "solid", "embedding_path": "mock.npy"}
            ],
            "template_name": "smart_casual"
        }]
    )

    resp_outfits = client.post("/recommendations/generate-outfits", json=outfits_payload)
    app.dependency_overrides.clear()

    assert resp_outfits.status_code == 200
    data_outfits = resp_outfits.json()
    assert "outfits" in data_outfits
    assert len(data_outfits["outfits"]) > 0
    
    first_outfit = data_outfits["outfits"][0]
    # Check that personalized why_selected metadata and outfit_embedding are returned!
    assert "why_selected" in first_outfit
    assert len(first_outfit["why_selected"]) > 0
    assert "outfit_embedding" in first_outfit
    assert len(first_outfit["outfit_embedding"]) == 512
