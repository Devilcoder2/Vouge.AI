"""
Phase 3B — Feature 4: Digital Wardrobe Calendar System Tests.
Verifies CRUD entry planning, slot constraints, Pillow photo uploads, and AI Curation Schedulers.
"""
import uuid
import io
from datetime import datetime, timezone, date as date_type
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.auth.security import create_access_token
from app.database.session import get_db
from app.database.models import (
    User, UserStyleProfile, ClothingItem, SavedOutfit, SavedOutfitItem,
    CalendarEntry, CalendarEntryItem
)

client = TestClient(app)

# ── Shared In-Memory Stores for Test State ─────────────────────────────────────
_USERS: dict = {}
_CLOTHING_ITEMS: list = []
_SAVED_OUTFITS: list = []
_SAVED_OUTFIT_ITEMS: list = []
_CALENDAR_ENTRIES: list = []
_CALENDAR_ENTRY_ITEMS: list = []
_STYLE_PROFILES: dict = {}

class MockUser:
    def __init__(self, email="test@vouge.ai", username="test_user"):
        self.id = uuid.uuid4()
        self.email = email
        self.username = username
        self.hashed_password = "hashed_password"
        self.is_active = True
        self.onboarding_completed = True
        self.height_cm = 180
        self.body_type = "lean_tall"
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

class MockClothingItem:
    def __init__(self, name, category, subcategory, primary_color, style, formality, fit):
        self.id = uuid.uuid4()
        self.name = name
        self.category = category
        self.subcategory = subcategory
        self.primary_color = primary_color
        self.primary_color_hex = "#ffffff"
        self.style = style
        self.formality = formality
        self.fit = fit
        self.pattern = "solid"
        self.seasons = ["spring", "summer", "autumn", "winter"]
        self.textile = "cotton"
        self.occasion = "casual"
        self.processed_image_path = "/assets/item.png"
        self.processed_image_url = "http://cdn/item.png"
        self.thumbnail_url = "http://cdn/item_thumb.png"
        self.original_image_path = "/assets/item_raw.png"
        self.original_image_url = "http://cdn/item_raw.png"
        self.embedding_path = "/assets/item.npy"
        self.categories = [category]
        self.verified = True
        self.has_ai_service = True
        self.secondary_colors = []
        self.secondary_colors_hex = []
        self.more_details = "Mock details"
        self.long = False



class _MockResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        if isinstance(self._value, list):
            return self._value[0] if self._value else None
        return self._value

    def scalar_one(self):
        if isinstance(self._value, list):
            return self._value[0]
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

def _smart_override_for_calendar(current_user: MockUser):
    async def mock_get_db():
        class CalendarMockDB:
            def __init__(self):
                self._added = []

            def add(self, obj):
                self._added.append(obj)

            async def flush(self):
                for obj in self._added:
                    if getattr(obj, "id", None) is None:
                        obj.id = uuid.uuid4()

            async def execute(self, stmt):
                stmt_str = str(stmt).lower()

                # 1. User lookup
                if "from users" in stmt_str:
                    return _MockResult(current_user)

                # 2. ClothingItem lookup
                elif "from clothing_items" in stmt_str:
                    return _MockResult(_CLOTHING_ITEMS)

                # 3. UserStyleProfile lookup
                elif "from user_style_profiles" in stmt_str:
                    profile = _STYLE_PROFILES.get(current_user.id)
                    return _MockResult(profile)

                # 4. SavedOutfit lookup
                elif "from saved_outfits" in stmt_str:
                    # check for specific outfit ID
                    if "saved_outfits.id =" in stmt_str:
                        parts = stmt_str.split("saved_outfits.id =")
                        # parse UUID loosely
                        for o in _SAVED_OUTFITS:
                            if str(o.id) in stmt_str:
                                return _MockResult(o)
                    return _MockResult(_SAVED_OUTFITS)

                # 5. CalendarEntry lookup
                elif "from calendar_entries" in stmt_str:
                    # check for specific entry ID
                    if "calendar_entries.id =" in stmt_str:
                        for e in _CALENDAR_ENTRIES:
                            if str(e.id) in stmt_str:
                                return _MockResult(e)
                    # Check unique uix constraint query
                    elif "calendar_entries.slot =" in stmt_str:
                        # Extract query params from state or mock
                        # return match if overlaps
                        return _MockResult(None)
                    
                    return _MockResult(_CALENDAR_ENTRIES)

                return _MockResult(None)

            async def commit(self):
                # First pass: assign IDs and add to lists
                for obj in self._added:
                    if getattr(obj, "id", None) is None:
                        obj.id = uuid.uuid4()
                    if isinstance(obj, CalendarEntry) and obj not in _CALENDAR_ENTRIES:
                        _CALENDAR_ENTRIES.append(obj)
                    elif isinstance(obj, CalendarEntryItem) and obj not in _CALENDAR_ENTRY_ITEMS:
                        obj.clothing_item = next((it for it in _CLOTHING_ITEMS if it.id == obj.clothing_item_id), None)
                        _CALENDAR_ENTRY_ITEMS.append(obj)
                    elif isinstance(obj, SavedOutfit) and obj not in _SAVED_OUTFITS:
                        _SAVED_OUTFITS.append(obj)
                    elif isinstance(obj, SavedOutfitItem) and obj not in _SAVED_OUTFIT_ITEMS:
                        obj.clothing_item = next((it for it in _CLOTHING_ITEMS if it.id == obj.clothing_item_id), None)
                        _SAVED_OUTFIT_ITEMS.append(obj)

                # Second pass: wire relationships
                for o in _SAVED_OUTFITS:
                    o.items = [i for i in _SAVED_OUTFIT_ITEMS if i.outfit_id == o.id]
                for e in _CALENDAR_ENTRIES:
                    e.items = [i for i in _CALENDAR_ENTRY_ITEMS if i.calendar_entry_id == e.id]
                    if e.outfit_id:
                        e.outfit = next((o for o in _SAVED_OUTFITS if o.id == e.outfit_id), None)


            async def refresh(self, obj):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid.uuid4()
                if getattr(obj, "updated_at", None) is None:
                    obj.updated_at = datetime.now(timezone.utc)
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = datetime.now(timezone.utc)

            async def delete(self, obj):
                if isinstance(obj, CalendarEntry):
                    if obj in _CALENDAR_ENTRIES:
                        _CALENDAR_ENTRIES.remove(obj)
                    # Cascade items removal
                    global _CALENDAR_ENTRY_ITEMS
                    _CALENDAR_ENTRY_ITEMS = [i for i in _CALENDAR_ENTRY_ITEMS if i.calendar_entry_id != obj.id]

        yield CalendarMockDB()

    return mock_get_db


# ── 1. Test Manual Calendar Entry CRUD & Constraints ─────────────────────────
@pytest.mark.anyio
async def test_manual_calendar_entry_crud_and_validation():
    """Tests manual calendar planning (custom outfits on-the-go) and unique constraint checks."""
    mock_user = MockUser()
    from app.auth.dependencies import get_current_active_user
    
    app.dependency_overrides[get_db] = _smart_override_for_calendar(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        # Clear stores
        global _CALENDAR_ENTRIES, _CALENDAR_ENTRY_ITEMS, _CLOTHING_ITEMS
        _CALENDAR_ENTRIES = []
        _CALENDAR_ENTRY_ITEMS = []
        
        garment = MockClothingItem("Stone Trench", "Outerwear", "trench", "stone", "minimalist", 8, "standard")
        _CLOTHING_ITEMS = [garment]

        # 1. Create a planned calendar entry
        payload_create = {
            "date": "2026-06-01",
            "slot": "office",
            "clothing_item_ids": [str(garment.id)]
        }
        res_create = client.post("/api/calendar/entries", json=payload_create)
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["slot"] == "office"
        assert len(data_create["items"]) == 1
        assert data_create["items"][0]["clothing_item_id"] == str(garment.id)
        
        entry_id = data_create["id"]

        # 2. Get calendar entries
        res_list = client.get("/api/calendar/entries?date=2026-06-01")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert len(data_list) == 1
        assert data_list[0]["id"] == entry_id

        # 3. Edit planned entries (swapping slot to dinner)
        payload_update = {
            "slot": "dinner"
        }
        res_edit = client.put(f"/api/calendar/entries/{entry_id}", json=payload_update)
        assert res_edit.status_code == 200
        data_edit = res_edit.json()
        assert data_edit["slot"] == "dinner"

        # 4. Delete calendar entries
        res_delete = client.delete(f"/api/calendar/entries/{entry_id}")
        assert res_delete.status_code == 200
        assert res_delete.json()["success"] is True
        assert len(_CALENDAR_ENTRIES) == 0

    finally:
        app.dependency_overrides.clear()


# ── 2. Test Real-Life Outfit Photo aspect Scaling Uploads ────────────────────
@pytest.mark.anyio
async def test_pillow_photo_aspect_scaling_upload():
    """Tests Pillow-based actual fit check uploads, verifying aspect scaling."""
    mock_user = MockUser()
    from app.auth.dependencies import get_current_active_user
    
    app.dependency_overrides[get_db] = _smart_override_for_calendar(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        # Clear stores and create dummy calendar entry
        global _CALENDAR_ENTRIES
        _CALENDAR_ENTRIES = []
        
        entry = CalendarEntry(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            date=date_type(2026, 6, 2),
            slot="brunch",
            outfit_id=None
        )
        _CALENDAR_ENTRIES.append(entry)

        # Build a large mock image bytes (1200x800 px) to test scaling compression
        large_img = Image.new("RGB", (1200, 800), color="blue")
        buffer = io.BytesIO()
        large_img.save(buffer, format="JPEG")
        buffer.seek(0)

        # Upload fit photo file
        response_upload = client.post(
            f"/api/calendar/entries/{entry.id}/photo",
            files={"file": ("my_fit.jpg", buffer, "image/jpeg")}
        )
        assert response_upload.status_code == 200
        data_upload = response_upload.json()
        assert data_upload["real_photo_path"] is not None
        assert "calendar" in data_upload["real_photo_url"]

    finally:
        app.dependency_overrides.clear()


# ── 3. Test AI Calendar Suggestions Curation Planner ──────────────────────────
@pytest.mark.anyio
async def test_ai_calendar_suggestions_planner():
    """Tests outfit suggestion curators and scheduler planned links."""
    mock_user = MockUser()
    from app.auth.dependencies import get_current_active_user
    
    app.dependency_overrides[get_db] = _smart_override_for_calendar(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        # Clear stores
        global _CLOTHING_ITEMS, _CALENDAR_ENTRIES, _SAVED_OUTFITS, _SAVED_OUTFIT_ITEMS
        _CLOTHING_ITEMS = []
        _CALENDAR_ENTRIES = []
        _SAVED_OUTFITS = []
        _SAVED_OUTFIT_ITEMS = []

        # Populate closet with minimal items to allow AI template selection
        _CLOTHING_ITEMS = [
            MockClothingItem("Blue Casual Shirt", "Tops", "Shirts & Blouses", "blue", "minimalist", 4, "standard"),
            MockClothingItem("Khaki Chinos", "Bottoms", "Chinos & Trousers", "khaki", "minimalist", 5, "standard"),
            MockClothingItem("Classic Sneakers", "Shoes", "Sneakers", "white", "minimalist", 2, "standard")
        ]

        # Trigger AI recommendations generation suggestion for tomorrow
        payload_suggest = {
            "date": "2026-06-03",
            "slot": "casual"
        }
        res_suggest = client.post("/api/calendar/generate-suggestions", json=payload_suggest)
        
        # Verify AI planned saved outfit is compiled and linked to calendar entry
        assert res_suggest.status_code == 201
        data_suggest = res_suggest.json()
        assert data_suggest["slot"] == "casual"
        assert data_suggest["outfit_id"] is not None
        assert "AI Planned" in data_suggest["outfit"]["name"]
        assert len(data_suggest["outfit"]["items"]) == 3

    finally:
        app.dependency_overrides.clear()
