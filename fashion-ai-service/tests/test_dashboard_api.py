"""
Phase 3B — Feature 3: Dashboard REST API Specification Tests.
Verifies Geolocation weather, Spotlight Looks, Runway Trends, Color Overreliance, and Chat.
"""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.security import create_access_token
from app.database.session import get_db
from app.database.models import User, UserStyleProfile, ClothingItem, GeneratedOutfit, GeneratedOutfitItem
from app.services.personalization_engine import PersonalizationEngine

client = TestClient(app)

# ── Shared In-Memory Stores for Test State ─────────────────────────────────────
_USERS: dict = {}
_STYLE_PROFILES: dict = {}
_CLOTHING_ITEMS: list = []
_GENERATED_OUTFITS: list = []

class MockUser:
    def __init__(self, email="test@vouge.ai", username="test_user"):
        self.id = uuid.uuid4()
        self.email = email
        self.username = username
        self.hashed_password = "hashed_password"
        self.is_active = True
        self.onboarding_completed = True
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

class MockClothingItem:
    def __init__(self, name, category, subcategory, primary_color, style, formality, fit):
        self.id = uuid.uuid4()
        self.name = name
        self.category = category
        self.subcategory = subcategory
        self.primary_color = primary_color
        self.style = style
        self.formality = formality
        self.fit = fit
        self.processed_image_path = "/assets/item.png"
        self.processed_image_url = "http://cdn/item.png"
        self.original_image_path = "/assets/item_raw.png"
        self.original_image_url = "http://cdn/item_raw.png"
        self.embedding_path = "/assets/item.npy"

class MockGeneratedOutfit:
    def __init__(self, user_id, occasion, season, score, template_name, reasoning, items):
        self.id = uuid.uuid4()
        self.user_id = str(user_id)
        self.occasion = occasion
        self.season = season
        self.score = score
        self.template_name = template_name
        self.reasoning = reasoning
        self.preview_url = "http://cdn/preview.png"
        self.breakdown = {"harmony": 90, "body": 95}
        self.created_at = datetime.now(timezone.utc)
        self.why_selected = ["Monochrome boost"]
        self.items = [MockGeneratedOutfitItem(self, it) for it in items]

class MockGeneratedOutfitItem:
    def __init__(self, outfit, clothing_item):
        self.id = uuid.uuid4()
        self.outfit_id = outfit.id
        self.clothing_item_id = clothing_item.id
        self.clothing_item = clothing_item

class _MockResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value

    def scalars(self):
        return self

    def first(self):
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value

    def all(self):
        if isinstance(self._value, list):
            return self._value
        return [self._value] if self._value is not None else []

def _smart_override_for_dashboard(current_user: MockUser):
    async def mock_get_db():
        class DashboardMockDB:
            def __init__(self):
                self._added = []

            def add(self, obj):
                self._added.append(obj)

            async def delete(self, obj):
                if obj in self._added:
                    self._added.remove(obj)
                global _GENERATED_OUTFITS
                if obj in _GENERATED_OUTFITS:
                    _GENERATED_OUTFITS.remove(obj)

            async def execute(self, stmt):
                stmt_str = str(stmt).lower()

                if "from users" in stmt_str:
                    return _MockResult(current_user)

                elif "from user_style_profiles" in stmt_str:
                    profile = _STYLE_PROFILES.get(current_user.id)
                    return _MockResult(profile)

                elif "from clothing_items" in stmt_str:
                    return _MockResult(_CLOTHING_ITEMS)

                elif "from generated_outfits" in stmt_str:
                    user_outfits = [o for o in _GENERATED_OUTFITS if o.user_id == str(current_user.id)]
                    return _MockResult(user_outfits)

                return _MockResult(None)

            async def commit(self):
                for obj in self._added:
                    if isinstance(obj, UserStyleProfile):
                        obj.id = uuid.uuid4()
                        _STYLE_PROFILES[obj.user_id] = obj
                    elif isinstance(obj, GeneratedOutfit):
                        obj.id = uuid.uuid4()
                        _GENERATED_OUTFITS.append(obj)

            async def refresh(self, obj):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid.uuid4()
                if getattr(obj, "updated_at", None) is None:
                    obj.updated_at = datetime.now(timezone.utc)
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = datetime.now(timezone.utc)

        yield DashboardMockDB()

    return mock_get_db

# ── 1. Test Weather API ───────────────────────────────────────────────────────
def test_dashboard_weather_api():
    """Tests Geolocation weather resolution for nearest capitals."""
    # 1. Test default London weather
    response = client.get("/api/dashboard/weather")
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "London"
    assert data["temperature_celsius"] == 12.0
    assert "weather-cloudy" in data["icon"]

    # 2. Test Paris Coordinates
    response_paris = client.get("/api/dashboard/weather?latitude=48.85&longitude=2.35")
    assert response_paris.status_code == 200
    data_paris = response_paris.json()
    assert data_paris["location"] == "Paris"
    assert data_paris["temperature_celsius"] == 15.0
    assert "weather-sunny" in data_paris["icon"]

    # 3. Test Tokyo Coordinates
    response_tokyo = client.get("/api/dashboard/weather?latitude=35.67&longitude=139.65")
    assert response_tokyo.status_code == 200
    data_tokyo = response_tokyo.json()
    assert data_tokyo["location"] == "Tokyo"
    assert data_tokyo["temperature_celsius"] == 20.0
    assert "weather-rainy" in data_tokyo["icon"]

# ── 2. Test Runway Trends API ────────────────────────────────────────────────
def test_runway_trends_api():
    """Tests runway trends retrieval and style persona filters."""
    # Test minimalist filter limit 2
    response = client.get("/recommendations/trends?style_persona=minimalist&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2
    for trend in data:
        assert "monochrome" in trend["description"].lower() or "minimalism" in trend["description"].lower()

    # Test tactical/gorpcore filter
    response_street = client.get("/recommendations/trends?style_persona=streetwear&limit=1")
    assert response_street.status_code == 200
    data_street = response_street.json()
    assert len(data_street) == 1
    assert "tactical" in data_street[0]["description"].lower()

# ── 3. Test Editorial Spotlight Look API ──────────────────────────────────────
@pytest.mark.anyio
async def test_editorial_look_fallback_and_cached():
    """Tests Spotlight Curation response matching DB and fallback Noir schemas."""
    mock_user = MockUser()
    from app.auth.dependencies import get_current_active_user
    
    app.dependency_overrides[get_db] = _smart_override_for_dashboard(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        # Clear stores
        global _GENERATED_OUTFITS
        _GENERATED_OUTFITS = []

        # 1. Verify standard Noir fallback when empty
        response_fallback = client.get("/recommendations/editorial-look")
        assert response_fallback.status_code == 200
        data_fb = response_fallback.json()
        assert data_fb["outfit_id"] == "modern-minimalist"
        assert "charcoal" in data_fb["description"].lower()
        assert data_fb["weather_context"]["location"] == "London"


        # 2. Add cached GeneratedOutfit
        items = [
            MockClothingItem("Charcoal Trench", "outerwear", "trench", "charcoal", "minimalist", 8, "standard"),
            MockClothingItem("Ivory Knit", "tops", "knit", "ivory", "minimalist", 4, "standard")
        ]
        cached_outfit = MockGeneratedOutfit(
            user_id=mock_user.id,
            occasion="evening",
            season="winter",
            score=98,
            template_name="Winter Elegance",
            reasoning="A cozy yet extremely high-contrast monochromatic pairing.",
            items=items
        )
        _GENERATED_OUTFITS.append(cached_outfit)

        # 3. Verify it picks up cache
        response_cached = client.get(f"/recommendations/editorial-look?user_id={mock_user.id}")
        assert response_cached.status_code == 200
        data_cached = response_cached.json()
        assert data_cached["outfit_id"] == str(cached_outfit.id)
        assert "Winter Elegance" in data_cached["editorial_title"]
        assert data_cached["vogue_score"] == 98
        assert len(data_cached["clothing_item_ids"]) == 2

        # 4. Add a cached GeneratedOutfit with a missing preview file and verify it gets evicted
        stale_cached_outfit = MockGeneratedOutfit(
            user_id=mock_user.id,
            occasion="evening",
            season="winter",
            score=95,
            template_name="Stale Cache Outfit",
            reasoning="A stale cache entry whose preview image is physically missing.",
            items=items
        )
        stale_cached_outfit.preview_url = "/recommendations/preview-image/nonexistent_file_xyz_preview.png"
        _GENERATED_OUTFITS.insert(0, stale_cached_outfit)

        # Verify it falls back to the previous valid cached outfit and evicts the stale one!
        response_cache_after_stale = client.get(f"/recommendations/editorial-look?user_id={mock_user.id}")
        assert response_cache_after_stale.status_code == 200
        data_after_stale = response_cache_after_stale.json()
        
        assert data_after_stale["outfit_id"] == str(cached_outfit.id)
        assert "Winter Elegance" in data_after_stale["editorial_title"]
        assert stale_cached_outfit not in _GENERATED_OUTFITS

    finally:
        app.dependency_overrides.clear()

# ── 4. Test Chat Assistant API ────────────────────────────────────────────────
@pytest.mark.anyio
async def test_stylist_chat_assistant():
    """Verifies chatbot responses, user styling profile context, and cached suggestions."""
    mock_user = MockUser()
    from app.auth.dependencies import get_current_active_user
    
    app.dependency_overrides[get_db] = _smart_override_for_dashboard(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        # Create some items and cached outfit
        global _CLOTHING_ITEMS, _GENERATED_OUTFITS
        _CLOTHING_ITEMS = [
            MockClothingItem("Blue Dress Shirt", "tops", "shirt", "blue", "workwear", 7, "standard"),
            MockClothingItem("Navy Chinos", "bottoms", "pants", "navy", "workwear", 6, "slim")
        ]
        
        cached_outfit = MockGeneratedOutfit(
            user_id=mock_user.id,
            occasion="work",
            season="spring",
            score=92,
            template_name="Workday Classic",
            reasoning="A sharp, coordinated workwear silhouette.",
            items=_CLOTHING_ITEMS
        )
        _GENERATED_OUTFITS = [cached_outfit]

        # 1. Ask about rain
        payload_rain = {
            "user_id": str(mock_user.id),
            "message": "It is raining today, what should I wear?",
            "chat_history": []
        }
        res_rain = client.post("/v1/chat/message", json=payload_rain)
        assert res_rain.status_code == 200
        data_rain = res_rain.json()
        assert "trench" in data_rain["reply"].lower() or "knit" in data_rain["reply"].lower()
        # Should attach suggested cached outfit ID
        assert data_rain["suggested_outfit_id"] == str(cached_outfit.id)

        # 2. Ask about colors
        payload_color = {
            "user_id": str(mock_user.id),
            "message": "I feel like I wear too much navy blue",
            "chat_history": []
        }
        res_color = client.post("/v1/chat/message", json=payload_color)
        assert res_color.status_code == 200
        data_color = res_color.json()
        assert "navy" in data_color["reply"].lower()
        assert "earth" in data_color["reply"].lower()

    finally:
        app.dependency_overrides.clear()
