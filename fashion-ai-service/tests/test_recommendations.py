import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timezone

from app.main import app
from app.routes.processing import get_db
from app.schemas.recommendation import GenerateOutfitsRequest, SaveOutfitRequest
from app.recommendation.utils.wardrobe_normalizer import WardrobeNormalizer
from app.recommendation.generators.outfit_templates import TEMPLATES, get_templates_for_occasion
from app.recommendation.scorers.outfit_scorer import OutfitScorer
from app.recommendation.scorers.ranker import RecommendationRanker

client = TestClient(app)

# Helper fixture representing mock wardrobe items in the database
@pytest.fixture
def mock_closet_items():
    class MockGarment:
        def __init__(self, id_val, cat, sub, col, hex_val, fit, style, formality, seasons, pattern, is_dup=False, conf=1.0):
            self.id = id_val
            self.category = cat
            self.subcategory = sub
            self.primary_color = col
            self.primary_color_hex = hex_val
            self.secondary_colors = []
            self.secondary_colors_hex = []
            self.fit = fit
            self.style = style
            self.formality = formality
            self.seasons = seasons
            self.pattern = pattern
            self.is_duplicate = is_dup
            self.confidence_category = conf
            self.embedding_path = "mock.npy"
            self.created_at = datetime.now(timezone.utc)

    return [
        # Tops
        MockGarment(uuid.UUID("11111111-1111-1111-1111-111111111111"), "Tops", "Shirts & Blouses", "white", "#ffffff", "standard", "classic", 6, ["spring", "summer", "autumn", "winter"], "solid"),
        MockGarment(uuid.UUID("22222222-2222-2222-2222-222222222222"), "Tops", "T-Shirts & Tanks", "black", "#000000", "oversized", "streetwear", 3, ["spring", "summer"], "graphic"),
        MockGarment(uuid.UUID("33333333-3333-3333-3333-333333333333"), "Tops", "T-Shirts & Tanks", "red", "#ff0000", "standard", "athleisure", 2, ["summer"], "solid", conf=0.20),  # Filtered due to low confidence
        
        # Bottoms
        MockGarment(uuid.UUID("44444444-4444-4444-4444-444444444444"), "Bottoms", "Jeans", "blue", "#1e3a8a", "standard", "classic", 4, ["spring", "summer", "autumn", "winter"], "solid"),
        MockGarment(uuid.UUID("55555555-5555-5555-5555-555555555555"), "Bottoms", "Chinos & Trousers", "grey", "#808080", "standard", "classic", 6, ["spring", "autumn", "winter"], "solid"),
        MockGarment(uuid.UUID("66666666-6666-6666-6666-666666666666"), "Bottoms", "Sweatpants & Joggers", "black", "#000000", "relaxed", "athleisure", 2, ["spring", "winter"], "solid", is_dup=True),  # Filtered due to duplicate
        
        # Shoes
        MockGarment(uuid.UUID("77777777-7777-7777-7777-777777777777"), "Shoes", "Loafers & Slip-ons", "brown", "#a52a2a", "standard", "classic", 6, ["spring", "summer", "autumn"], "solid"),
        MockGarment(uuid.UUID("88888888-8888-8888-8888-888888888888"), "Shoes", "Sneakers", "white", "#ffffff", "standard", "streetwear", 3, ["spring", "summer", "autumn", "winter"], "solid")
    ]

def test_wardrobe_normalizer(mock_closet_items):
    """Verifies that the normalizer removes duplicates, rejects low-confidence items, and groups correctly."""
    grouped = WardrobeNormalizer.normalize_and_group(mock_closet_items, min_confidence=0.45)
    
    # We started with 8 items.
    # 1 item has confidence 0.20 < 0.45 (filtered).
    # 1 item is marked as duplicate (filtered).
    # Remaining high-quality items = 6.
    
    total_grouped = sum(len(items) for items in grouped.values())
    assert total_grouped == 6
    
    # Verify groupings
    assert len(grouped["TOPS"]) == 2  # White shirt and Black t-shirt (Red t-shirt filtered)
    assert len(grouped["BOTTOMS"]) == 2  # Blue jeans and Grey chinos (Sweatpants duplicate filtered)
    assert len(grouped["FOOTWEAR"]) == 2  # Brown loafers and White sneakers
    
    # Check normalization mappings
    white_top = next(it for it in grouped["TOPS"] if it["id"] == uuid.UUID("11111111-1111-1111-1111-111111111111"))
    assert white_top["category"] == "TOPS"
    assert white_top["style"] == "classic"
    assert white_top["fit"] == "regular"  # 'standard' fit maps to 'regular' in taxonomy

def test_templates_for_occasions():
    """Verifies template category routing."""
    office_templates = get_templates_for_occasion("office")
    assert len(office_templates) > 0
    # Must support smart casual or office professional
    template_names = [t.name for t in office_templates]
    assert "office_professional" in template_names or "smart_casual" in template_names

def test_outfit_scorer():
    """Verifies ensemble scoring math and weight distribution."""
    # Define a clean smart casual outfit
    outfit_items = [
        {"category": "TOPS", "subcategory": "Shirts & Blouses", "primary_color": "white", "primary_color_hex": "#ffffff", "style": "classic", "fit": "regular", "formality": 6, "seasons": ["spring", "summer", "autumn", "winter"], "pattern": "solid"},
        {"category": "BOTTOMS", "subcategory": "Chinos & Trousers", "primary_color": "grey", "primary_color_hex": "#808080", "style": "classic", "fit": "regular", "formality": 6, "seasons": ["spring", "autumn", "winter"], "pattern": "solid"},
        {"category": "FOOTWEAR", "subcategory": "Loafers & Slip-ons", "primary_color": "brown", "primary_color_hex": "#a52a2a", "style": "classic", "fit": "regular", "formality": 6, "seasons": ["spring", "summer", "autumn"], "pattern": "solid"}
    ]
    
    score_res = OutfitScorer.score_outfit(outfit_items, "office", "autumn")
    
    # Ensure total score is between 0 and 100
    assert 0 <= score_res["total_score"] <= 100
    # Since these are highly compatible classic pieces, score should be quite high
    assert score_res["total_score"] >= 85
    assert "breakdown" in score_res
    assert len(score_res["reasons"]) == 5

def test_recommendation_ranker():
    """Verifies ranker filters visual redundancies and duplicate outfits."""
    top_a = {"id": uuid.UUID("11111111-1111-1111-1111-111111111111"), "category": "TOPS"}
    bottom_a = {"id": uuid.UUID("44444444-4444-4444-4444-444444444444"), "category": "BOTTOMS"}
    shoe_a = {"id": uuid.UUID("77777777-7777-7777-7777-777777777777"), "category": "FOOTWEAR"}
    shoe_b = {"id": uuid.UUID("88888888-8888-8888-8888-888888888888"), "category": "FOOTWEAR"}
    
    candidates = [
        # Outfit 1 (Top A + Bottom A + Shoe A) - Score 92
        {"items": [top_a, bottom_a, shoe_a], "total_score": 92, "template_name": "casual", "breakdown": {}},
        # Outfit 2 (Top A + Bottom A + Shoe B) - Score 88 (redundant top/bottom combo, shoe swap)
        {"items": [top_a, bottom_a, shoe_b], "total_score": 88, "template_name": "casual", "breakdown": {}}
    ]
    
    diversified = RecommendationRanker.diversify_and_rank(candidates, max_outputs=5)
    # The redundant candidate (Outfit 2) must be filtered out!
    assert len(diversified) == 1
    assert diversified[0]["total_score"] == 92

def test_api_generate_outfits_endpoint(mock_closet_items, monkeypatch):
    """
    Tests the POST /recommendations/generate-outfits endpoint end-to-end.
    """
    # Mock the database select call to return our mock closet items
    async def mock_get_db():
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return mock_closet_items
                return MockScalars()
        class MockDB:
            async def execute(self, stmt):
                return MockResult()
        yield MockDB()

    app.dependency_overrides[get_db] = mock_get_db

    request_payload = {
        "occasion": "office",
        "season": "autumn",
        "user_id": "test_user_id"
    }

    response = client.post("/recommendations/generate-outfits", json=request_payload)
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "outfits" in data
    assert "diversity_eval" in data
    
    # We should have generated outfits successfully
    assert len(data["outfits"]) > 0
    top_outfit = data["outfits"][0]
    assert top_outfit["score"] >= 55
    assert "reasoning" in top_outfit
    assert "breakdown" in top_outfit
    assert len(top_outfit["items"]) >= 3

def test_saved_outfits_crud_flow(mock_closet_items):
    """
    Tests the CRUD operations for Saved Outfits: save, retrieve, and delete.
    """
    test_outfit_id = uuid.uuid4()
    
    # Mock models representing saved outfits
    class MockSavedOutfitItemLink:
        def __init__(self, gi):
            self.clothing_item = gi
            
    class MockSavedOutfitModel:
        def __init__(self):
            self.id = test_outfit_id
            self.user_id = "test_user_id"
            self.name = "My Office Classic Outfit"
            self.occasion = "office"
            self.season = "autumn"
            self.score = 92
            self.reasoning = "Elegant professional composition."
            self.created_at = datetime.now(timezone.utc)
            self.items = [MockSavedOutfitItemLink(mock_closet_items[0]), MockSavedOutfitItemLink(mock_closet_items[3]), MockSavedOutfitItemLink(mock_closet_items[6])]

    mock_saved_outfit = MockSavedOutfitModel()
    saved_outfits_db = [mock_saved_outfit]

    async def mock_get_db():
        class MockResult:
            def __init__(self, stmt):
                self.stmt_str = str(stmt)
                
            def scalar_one_or_none(self):
                # If checking for a clothing item, return the matching MockGarment
                if "clothing_items" in self.stmt_str:
                    for garment in mock_closet_items:
                        if str(garment.id) in self.stmt_str:
                            return garment
                    return mock_closet_items[0]
                    
                # If checking for a saved outfit
                if "saved_outfits" in self.stmt_str:
                    if len(saved_outfits_db) > 0:
                        return mock_saved_outfit
                return None
                
            def scalars(self):
                class MockScalars:
                    def __init__(self, stmt_str):
                        self.stmt_str = stmt_str
                    def all(self):
                        # Handles returning mock closet items or list of saved outfits
                        if "saved_outfits" in self.stmt_str:
                            return saved_outfits_db
                        return mock_closet_items
                return MockScalars(self.stmt_str)
                
        class MockDB:
            async def execute(self, stmt):
                return MockResult(stmt)
            def add(self, obj): pass
            async def commit(self): pass
            async def refresh(self, obj): pass
            async def delete(self, obj):
                saved_outfits_db.clear()
        yield MockDB()

    app.dependency_overrides[get_db] = mock_get_db

    # 1. Save Outfit
    save_payload = {
        "user_id": "test_user_id",
        "name": "My Office Classic Outfit",
        "occasion": "office",
        "season": "autumn",
        "score": 92,
        "reasoning": "Elegant professional composition.",
        "clothing_item_ids": [
            "11111111-1111-1111-1111-111111111111",
            "44444444-4444-4444-4444-444444444444",
            "77777777-7777-7777-7777-777777777777"
        ]
    }
    
    save_resp = client.post("/recommendations/save-outfit", json=save_payload)
    assert save_resp.status_code == 201
    
    # 2. Get Saved Outfits
    get_resp = client.get("/recommendations/saved-outfits?user_id=test_user_id")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 1
    assert get_resp.json()[0]["name"] == "My Office Classic Outfit"
    
    # 3. Delete Saved Outfit
    del_resp = client.delete(f"/recommendations/saved-outfits/{test_outfit_id}")
    assert del_resp.status_code == 200
    assert "Successfully deleted" in del_resp.json()["message"]
    
    app.dependency_overrides.clear()

def test_moat_analysis_endpoints(mock_closet_items):
    """
    Tests GET /recommendations/gap-analysis and GET /recommendations/versatility.
    """
    async def mock_get_db():
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return mock_closet_items
                return MockScalars()
        class MockDB:
            async def execute(self, stmt):
                return MockResult()
        yield MockDB()

    app.dependency_overrides[get_db] = mock_get_db

    # 1. Gap Analysis
    gap_resp = client.get("/recommendations/gap-analysis")
    assert gap_resp.status_code == 200
    gap_data = gap_resp.json()
    assert len(gap_data) > 0
    assert "unlocked_outfits_count" in gap_data[0]
    
    # 2. Versatility Analysis
    vers_resp = client.get("/recommendations/versatility")
    assert vers_resp.status_code == 200
    vers_data = vers_resp.json()
    assert len(vers_data) > 0
    assert "versatility_score" in vers_data[0]
    
    app.dependency_overrides.clear()
