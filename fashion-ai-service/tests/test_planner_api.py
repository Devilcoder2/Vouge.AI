"""
Dynamic Calendar Planner System Tests.
Verifies GET, POST, PUT, DELETE schedule entries, AI auto-planning, and Wear snapshot logs.
"""
import uuid
import io
from datetime import datetime, timezone, date as date_type
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.auth.dependencies import get_current_active_user
from app.database.session import get_db
from app.database.models import (
    User, UserStyleProfile, ClothingItem, SavedOutfit, SavedOutfitItem,
    CalendarEntry, CalendarEntryItem, WearLog
)

client = TestClient(app)

# ── Shared In-Memory Stores for Test State ─────────────────────────────────────
_CLOTHING_ITEMS: list = []
_SAVED_OUTFITS: list = []
_SAVED_OUTFIT_ITEMS: list = []
_CALENDAR_ENTRIES: list = []
_CALENDAR_ENTRY_ITEMS: list = []
_WEAR_LOGS: list = []
_STYLE_PROFILES: dict = {}

class MockUser:
    def __init__(self, email="planner_test@vouge.ai", username="planner_user"):
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

def _smart_override_for_planner(current_user: MockUser):
    async def mock_get_db():
        class PlannerMockDB:
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
                    if "saved_outfits.id =" in stmt_str:
                        for o in _SAVED_OUTFITS:
                            if str(o.id) in stmt_str:
                                return _MockResult(o)
                    return _MockResult(_SAVED_OUTFITS)

                # 5. CalendarEntry lookup
                elif "from calendar_entries" in stmt_str:
                    if "calendar_entries.id =" in stmt_str:
                        for e in _CALENDAR_ENTRIES:
                            if str(e.id) in stmt_str:
                                return _MockResult(e)
                    elif "calendar_entries.slot =" in stmt_str:
                        return _MockResult(None)
                    
                    return _MockResult(_CALENDAR_ENTRIES)

                # 6. WearLog lookup
                elif "from wear_logs" in stmt_str:
                    if "wear_logs.id =" in stmt_str:
                        for wl in _WEAR_LOGS:
                            if str(wl.id) in stmt_str:
                                return _MockResult(wl)
                    return _MockResult(_WEAR_LOGS)

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
                    elif isinstance(obj, WearLog) and obj not in _WEAR_LOGS:
                        _WEAR_LOGS.append(obj)

                # Second pass: wire relationships
                for o in _SAVED_OUTFITS:
                    o.items = [i for i in _SAVED_OUTFIT_ITEMS if i.outfit_id == o.id]
                for e in _CALENDAR_ENTRIES:
                    e.items = [i for i in _CALENDAR_ENTRY_ITEMS if i.calendar_entry_id == e.id]
                    e.wear_log_rel = next((w for w in _WEAR_LOGS if w.planned_outfit_id == e.id), None)
                    if e.outfit_id:
                        e.outfit = next((o for o in _SAVED_OUTFITS if o.id == e.outfit_id), None)

            async def refresh(self, obj):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid.uuid4()
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = datetime.now(timezone.utc)

            async def delete(self, obj):
                if isinstance(obj, CalendarEntry):
                    if obj in _CALENDAR_ENTRIES:
                        _CALENDAR_ENTRIES.remove(obj)
                    global _CALENDAR_ENTRY_ITEMS
                    _CALENDAR_ENTRY_ITEMS = [i for i in _CALENDAR_ENTRY_ITEMS if i.calendar_entry_id != obj.id]
                elif isinstance(obj, WearLog):
                    if obj in _WEAR_LOGS:
                        _WEAR_LOGS.remove(obj)

        yield PlannerMockDB()

    return mock_get_db


# ── 1. Test Planner schedule CRUD ─────────────────────────────────────────────
@pytest.mark.anyio
async def test_planner_schedule_crud():
    mock_user = MockUser()
    app.dependency_overrides[get_db] = _smart_override_for_planner(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        global _CALENDAR_ENTRIES, _CALENDAR_ENTRY_ITEMS, _CLOTHING_ITEMS
        _CALENDAR_ENTRIES = []
        _CALENDAR_ENTRY_ITEMS = []
        
        garment = MockClothingItem("Trench Coat", "Outerwear", "trench", "beige", "classic", 7, "standard")
        _CLOTHING_ITEMS = [garment]

        # A. Schedule Custom Outfit
        payload = {
            "date": "2026-05-30",
            "time_slot": "Office Dinner",
            "occasion": "FORMAL",
            "clothing_item_ids": [str(garment.id)],
            "notes": "Premium monochrome look."
        }
        res = client.post("/api/planner/schedule", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["time_slot"] == "Office Dinner"
        
        planned_id = data["planned_outfit_id"]

        # B. Get Planner Grid Range
        res_grid = client.get("/api/planner?start_date=2026-05-30&end_date=2026-05-30")
        assert res_grid.status_code == 200
        grid_data = res_grid.json()
        assert len(grid_data["calendar"]) == 1
        assert grid_data["calendar"][0]["day_of_week"] == "SATURDAY"
        assert len(grid_data["calendar"][0]["planned_slots"]) == 1
        assert grid_data["calendar"][0]["planned_slots"][0]["planned_outfit_id"] == planned_id

        # C. Update planned Schedule
        payload_update = {
            "time_slot": "Gala Ceremony",
            "notes": "Updated outfit notes."
        }
        res_up = client.put(f"/api/planner/schedule/{planned_id}", json=payload_update)
        assert res_up.status_code == 200
        assert "time_slot" in res_up.json()["updated_fields"]

        # D. Delete schedule
        res_del = client.delete(f"/api/planner/schedule/{planned_id}")
        assert res_del.status_code == 200
        assert res_del.json()["planned_outfit_id"] == planned_id

    finally:
        app.dependency_overrides.clear()


# ── 2. Test AI Auto-Planner Suggestions ───────────────────────────────────────
@pytest.mark.anyio
async def test_planner_ai_auto_generator():
    mock_user = MockUser()
    app.dependency_overrides[get_db] = _smart_override_for_planner(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        global _CLOTHING_ITEMS, _CALENDAR_ENTRIES, _SAVED_OUTFITS, _SAVED_OUTFIT_ITEMS
        _CLOTHING_ITEMS = [
            MockClothingItem("Casual Tee", "Tops", "Shirts & Blouses", "white", "minimal", 3, "regular"),
            MockClothingItem("Raw Jeans", "Bottoms", "Chinos & Trousers", "indigo", "minimal", 4, "regular"),
            MockClothingItem("Retro Sneaker", "Shoes", "Sneakers", "white", "minimal", 2, "regular")
        ]
        _CALENDAR_ENTRIES = []
        _SAVED_OUTFITS = []
        _SAVED_OUTFIT_ITEMS = []

        payload_auto = {
            "start_date": "2026-06-01",
            "days_count": 1,
            "agendas": [
                {
                    "date": "2026-06-01",
                    "slots": [
                        { "time_slot": "Brunch Look", "occasion": "casual" }
                    ]
                }
            ]
        }

        res = client.post("/api/planner/auto-generate", json=payload_auto)
        assert res.status_code == 200
        assert res.json()["auto_scheduled_count"] == 1

    finally:
        app.dependency_overrides.clear()


# ── 3. Test Wear Log Snap Photo Uploads & Deletions ──────────────────────────
@pytest.mark.anyio
async def test_planner_wear_logs_snaps():
    mock_user = MockUser()
    app.dependency_overrides[get_db] = _smart_override_for_planner(mock_user)
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        global _WEAR_LOGS, _CALENDAR_ENTRIES
        _WEAR_LOGS = []
        _CALENDAR_ENTRIES = []

        # Create large mock file to upload
        large_img = Image.new("RGB", (1000, 750), color="green")
        buffer = io.BytesIO()
        large_img.save(buffer, format="JPEG")
        buffer.seek(0)

        # Upload fit log snap photo
        res_upload = client.post(
            "/api/planner/log-photo",
            data={
                "date": "2026-05-29",
                "notes": "Loved the aesthetic reaction today!"
            },
            files={"file": ("my_log_snap.jpg", buffer, "image/jpeg")}
        )
        assert res_upload.status_code == 201
        data = res_upload.json()
        assert data["notes"] == "Loved the aesthetic reaction today!"
        
        log_id = data["log_id"]

        # Delete photo wear log snap
        res_del = client.delete(f"/api/planner/log-photo/{log_id}")
        assert res_del.status_code == 200
        assert res_del.json()["log_id"] == log_id

    finally:
        app.dependency_overrides.clear()
