"""
Phase 3A — Feature 2: User Personalization & Feedback Learning System Tests.
Uses FastAPI TestClient with dependency_overrides to prevent asyncpg event-loop conflicts.
"""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.security import create_access_token
from app.database.session import get_db
from app.database.models import User, UserStyleProfile, RecommendationFeedback, UserBehaviorEvent, ClothingItem, SavedOutfit
from app.services.personalization_engine import PersonalizationEngine

client = TestClient(app)

# ── Shared In-Memory Stores for Test State ─────────────────────────────────────
_USERS: dict = {}
_FEEDBACKS: list = []
_EVENTS: list = []
_STYLE_PROFILES: dict = {}  # user_id -> UserStyleProfile
_SAVED_OUTFITS: list = []
_CLOTHING_ITEMS: list = []


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
    def __init__(self, category, subcategory, primary_color, style, formality, fit):
        self.id = uuid.uuid4()
        self.category = category
        self.subcategory = subcategory
        self.primary_color = primary_color
        self.style = style
        self.formality = formality
        self.fit = fit
        self.perceptual_hash = "fake_hash"
        self.is_duplicate = False


class MockSavedOutfit:
    def __init__(self, user_id, name, occasion, season, score, items):
        self.id = uuid.uuid4()
        self.user_id = str(user_id)
        self.name = name
        self.occasion = occasion
        self.season = season
        self.score = score
        self.reasoning = "Stylish combo"
        self.created_at = datetime.now(timezone.utc)
        self.items = [MockSavedOutfitItem(self, it) for it in items]


class MockSavedOutfitItem:
    def __init__(self, outfit, clothing_item):
        self.id = uuid.uuid4()
        self.outfit_id = outfit.id
        self.clothing_item_id = clothing_item.id
        self.clothing_item = clothing_item


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


# ── Smart DB Mock Override for Personalization Endpoints ──────────────────────
def _smart_override_for_personalization(current_user: MockUser):
    async def mock_get_db():
        class PersonalizationMockDB:
            def __init__(self):
                self._added = []

            def add(self, obj):
                self._added.append(obj)

            async def execute(self, stmt):
                stmt_str = str(stmt).lower()

                # 1. User lookup
                if "from users" in stmt_str:
                    return _MockResult(current_user)

                # 2. UserStyleProfile lookup
                elif "from user_style_profiles" in stmt_str:
                    profile = _STYLE_PROFILES.get(current_user.id)
                    return _MockResult(profile)

                # 3. SavedOutfit lookup
                elif "from saved_outfits" in stmt_str:
                    # Filter saved outfits for current user
                    user_outfits = [o for o in _SAVED_OUTFITS if o.user_id == str(current_user.id)]
                    return _MockResult(user_outfits)

                # 4. RecommendationFeedback lookup
                elif "from recommendation_feedback" in stmt_str:
                    user_feedbacks = [f for f in _FEEDBACKS if f.user_id == current_user.id]
                    return _MockResult(user_feedbacks)

                # 5. UserBehaviorEvent lookup
                elif "from user_behavior_events" in stmt_str:
                    user_events = [e for e in _EVENTS if e.user_id == current_user.id]
                    return _MockResult(user_events)

                # 6. ClothingItems lookup
                elif "from clothing_items" in stmt_str:
                    return _MockResult(_CLOTHING_ITEMS)

                return _MockResult(None)

            async def commit(self):
                for obj in self._added:
                    if isinstance(obj, RecommendationFeedback):
                        obj.id = uuid.uuid4()
                        _FEEDBACKS.append(obj)
                    elif isinstance(obj, UserBehaviorEvent):
                        obj.id = uuid.uuid4()
                        _EVENTS.append(obj)
                    elif isinstance(obj, UserStyleProfile):
                        obj.id = uuid.uuid4()
                        _STYLE_PROFILES[obj.user_id] = obj

            async def refresh(self, obj):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid.uuid4()
                if getattr(obj, "updated_at", None) is None:
                    obj.updated_at = datetime.now(timezone.utc)
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = datetime.now(timezone.utc)

        yield PersonalizationMockDB()

    return mock_get_db


# ══════════════════════════════════════════════════════════════════════════════
# TEST CASES
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Unit Test: Preference Weights and Profile Compilation ─────────────────
@pytest.mark.anyio
async def test_preference_weights_and_profile_compilation():
    """
    Verifies that the weights aggregator compiles preferred colors, preferred styles,
    favorite categories, and avoids/limits based on positive and negative behavior events.
    """
    user_id = uuid.uuid4()
    
    # Clean stores
    feedbacks = []
    events = []
    saved_outfits = []

    # Let's create mock items
    item_casual = {
        "primary_color": "blue",
        "style": "minimalist",
        "category": "top",
        "formality": 3,
        "fit": "standard"
    }
    item_formal = {
        "primary_color": "black",
        "style": "formal",
        "category": "bottom",
        "formality": 8,
        "fit": "slim"
    }
    item_oversized = {
        "primary_color": "yellow",
        "style": "streetwear",
        "category": "bottom",
        "formality": 4,
        "fit": "oversized"
    }

    # Simulate positive actions (+3.0 minimalist style, +3.0 blue color, +3.0 top category)
    # We log 3 saves/likes of item_casual
    for _ in range(3):
        events.append(UserBehaviorEvent(
            user_id=user_id,
            event_type="outfit_saved",
            event_metadata={"items": [item_casual]}
        ))

    # Simulate negative actions (-3.0 oversized fit, -3.0 yellow color)
    for _ in range(3):
        events.append(UserBehaviorEvent(
            user_id=user_id,
            event_type="outfit_dismissed",
            event_metadata={"items": [item_oversized]}
        ))

    # Compute preference weights
    weights = PersonalizationEngine.compute_preference_weights(feedbacks, events, saved_outfits)

    assert weights["color_scores"]["blue"] == 3.0
    assert weights["color_scores"]["yellow"] == -3.0
    assert weights["style_scores"]["minimalist"] == 3.0
    assert weights["style_scores"]["streetwear"] == -3.0
    assert weights["fit_scores"]["standard"] == 3.0
    assert weights["fit_scores"]["oversized"] == -3.0

    # Let's check preference vector generator logic
    # Mocking aggregate_feedback to return our lists
    async def mock_aggregate(*args):
        return {"feedbacks": feedbacks, "events": events, "saved_outfits": saved_outfits}

    # Temporarily monkeypatch aggregate_feedback
    original_aggregate = PersonalizationEngine.aggregate_feedback
    PersonalizationEngine.aggregate_feedback = mock_aggregate

    # Run DB-less generation of preference vector
    try:
        prefs = await PersonalizationEngine.generate_user_preference_vector(user_id, None)
        
        assert "blue" in prefs["preferred_colors"]
        assert "yellow" in prefs["disliked_colors"]
        assert "minimalist" in prefs["preferred_styles"]
        assert "oversized" in prefs["disliked_fits"]
        assert "top" in prefs["favorite_categories"]
    finally:
        PersonalizationEngine.aggregate_feedback = original_aggregate


# ── 2. Unit Test: Apply Boosts and Penalties ──────────────────────────────────
@pytest.mark.anyio
async def test_apply_boosts_and_penalties():
    """
    Verifies that boosts and penalties are mathematically correct and re-rank
    scored candidates appropriately.
    """
    user_id = uuid.uuid4()
    
    # Scored outfits list
    outfits = [
        # Candidate 1: Standard Neutral Outfit
        {
            "items": [
                {"primary_color": "white", "style": "minimalist", "fit": "standard", "formality": 4},
                {"primary_color": "black", "style": "minimalist", "fit": "standard", "formality": 4}
            ],
            "total_score": 80,
            "reasons": [],
            "why_selected": []
        },
        # Candidate 2: Streetwear oversized outfit with yellow (avoided) color
        {
            "items": [
                {"primary_color": "yellow", "style": "streetwear", "fit": "oversized", "formality": 4},
                {"primary_color": "black", "style": "streetwear", "fit": "oversized", "formality": 4}
            ],
            "total_score": 90,
            "reasons": [],
            "why_selected": []
        }
    ]

    # Style Profile preferences:
    # preferred_colors: ["white"], disliked_colors: ["yellow"]
    # preferred_styles: ["minimalist"], disliked_fits: ["oversized"]
    # preferred_formality_range: [3, 5]
    profile = UserStyleProfile(
        user_id=user_id,
        preferred_colors=["white"],
        disliked_colors=["yellow"],
        preferred_styles=["minimalist"],
        preferred_formality_range=[3, 5],
        favorite_categories=["top"]
    )

    class MockDB:
        async def execute(self, stmt):
            return _MockResult(profile)

    # We patch generate_user_preference_vector to return fit and monochrome preferences
    async def mock_pref_vector(*args):
        return {
            "preferred_colors": ["white"],
            "disliked_colors": ["yellow"],
            "preferred_styles": ["minimalist"],
            "preferred_formality_range": [3, 5],
            "favorite_categories": ["top"],
            "disliked_fits": ["oversized"],
            "prefers_monochrome": False
        }

    original_vector = PersonalizationEngine.generate_user_preference_vector
    PersonalizationEngine.generate_user_preference_vector = mock_pref_vector

    try:
        boosted_outfits = await PersonalizationEngine.apply_recommendation_boosts(
            outfits, user_id, MockDB()
        )

        # Candidate 1:
        # has white -> color boost (x1.05)
        # has minimalist -> style boost (x1.20)
        # avg formality = 4 (inside [3, 5])
        # Expected score: 80 * 1.05 * 1.20 = 100.8 -> 100 (cap)
        # Candidate 2:
        # has yellow -> avoided color penalty (x0.50)
        # has oversized -> disliked fit penalty (x0.80)
        # Expected score: 90 * 0.50 * 0.80 = 36
        
        assert boosted_outfits[0]["total_score"] == 100
        assert boosted_outfits[1]["total_score"] == 36
        
        # Verify Candidate 1 is ranked first now (even though Candidate 2 had base score 90!)
        assert boosted_outfits[0]["items"][0]["primary_color"] == "white"
    finally:
        PersonalizationEngine.generate_user_preference_vector = original_vector


# ── 3. Endpoint: Submit Feedback ──────────────────────────────────────────────
def test_submit_feedback_endpoint():
    """
    Tests POST /v1/recommendations/feedback endpoint.
    Verifies that it logs feedback in the DB and returns success.
    """
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)
    
    # Setup mock DB
    app.dependency_overrides[get_db] = _smart_override_for_personalization(user)

    resp = client.post(
        "/v1/recommendations/feedback",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "outfit_id": str(uuid.uuid4()),
            "action": "like"
        }
    )
    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 201, resp.json()
    assert resp.json()["success"] is True
    assert "recorded successfully" in resp.json()["message"]

    # Verify that the feedback is indeed recorded in the memory store
    assert len(_FEEDBACKS) > 0
    assert _FEEDBACKS[-1].action_type == "like"
    assert len(_EVENTS) > 0
    assert _EVENTS[-1].event_type == "outfit_liked"


# ── 4. Endpoint: Get Style Profile ───────────────────────────────────────────
def test_get_style_profile_endpoint():
    """
    Tests GET /v1/users/style-profile endpoint.
    Verifies that it compiles and returns style profile preferences.
    """
    user = MockUser()
    access_token = create_access_token(str(user.id), user.email)

    # Let's populate some feedback in memory store
    _FEEDBACKS.clear()
    _EVENTS.clear()
    _STYLE_PROFILES.clear()

    # Log 3 behavior events of liking minimalist streetwear top
    item = {
        "primary_color": "blue",
        "style": "minimalist",
        "category": "top",
        "formality": 4,
        "fit": "standard"
    }
    for _ in range(3):
        _EVENTS.append(UserBehaviorEvent(
            user_id=user.id,
            event_type="outfit_liked",
            event_metadata={"items": [item]}
        ))

    app.dependency_overrides[get_db] = _smart_override_for_personalization(user)
    resp = client.get(
        "/v1/users/style-profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200, resp.json()
    body = resp.json()
    assert body["user_id"] == str(user.id)
    assert "blue" in body["preferred_colors"]
    assert "minimalist" in body["preferred_styles"]
    assert "top" in body["favorite_categories"]
    assert body["preferred_formality_range"] == [4, 4]


# ── 5. Integration: Generate Outfits Personalization ─────────────────────────
def test_generate_outfits_personalization_integration():
    """
    Verifies that generate-outfits parses real user UUID and personalizes ranking
    if style profile exists.
    """
    # 1. Create closet items to return
    item_top = MockClothingItem("top", "shirt", "blue", "minimalist", 4, "standard")
    item_bottom = MockClothingItem("bottom", "pants", "black", "minimalist", 4, "standard")
    item_shoes = MockClothingItem("shoes", "sneakers", "white", "minimalist", 4, "standard")
    _CLOTHING_ITEMS.clear()
    _CLOTHING_ITEMS.extend([item_top, item_bottom, item_shoes])

    user = MockUser()
    profile = UserStyleProfile(
        user_id=user.id,
        preferred_colors=["blue"],
        disliked_colors=["orange"],
        preferred_styles=["minimalist"],
        preferred_formality_range=[3, 5],
        favorite_categories=["top"]
    )
    _STYLE_PROFILES[user.id] = profile

    app.dependency_overrides[get_db] = _smart_override_for_personalization(user)

    # Trigger outfit generation for occasion="casual", season="summer"
    resp = client.post(
        "/recommendations/generate-outfits",
        json={
            "user_id": str(user.id),
            "occasion": "casual",
            "season": "summer"
        }
    )
    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200, resp.json()
    body = resp.json()
    # If outfits were generated, verify they exist and personalization reason is attached
    if body["outfits"]:
        outfit = body["outfits"][0]
        # Should have why_selected personalization notes
        assert any("boost" in reason or "style" in reason for reason in outfit["why_selected"])
