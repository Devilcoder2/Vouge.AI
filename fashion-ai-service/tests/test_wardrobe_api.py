import io
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_db
from app.database.models import User, ClothingItem, SavedOutfit, WardrobeCategory, WardrobeHistory
from app.auth.security import create_access_token
from app.routes.wardrobe import get_optional_current_user

# Setup client
client = TestClient(app)

# ── Test Stores ──────────────────────────────────────────────────────────────
_USERS = {}
_CATEGORIES = {}
_ITEMS = {}
_HISTORY = []
_SAVED_OUTFITS = []


# ── Mock Classes for Models ──────────────────────────────────────────────────
class MockUser:
    def __init__(self, email="test@vouge.ai", username="test_user"):
        self.id = uuid.uuid4()
        self.email = email
        self.username = username
        self.is_active = True
        self.onboarding_completed = True
        self.created_at = datetime.now(timezone.utc)


class MockCategory:
    def __init__(self, id, name, subtitle=None, status="active", image=None):
        self.id = id
        self.name = name
        self.subtitle = subtitle
        self.status = status
        self.image = image
        self.created_at = datetime.now(timezone.utc)


class MockClothingItem:
    def __init__(self, id, name, textile, primary_color, primary_color_hex, categories, verified=False, has_ai_service=False, occasion=None, formality=5, long=False):
        self.id = id or uuid.uuid4()
        self.name = name
        self.textile = textile
        self.primary_color = primary_color
        self.primary_color_hex = primary_color_hex
        self.categories = categories
        self.verified = verified
        self.has_ai_service = has_ai_service
        self.occasion = occasion
        self.formality = formality
        self.long = long
        self.secondary_colors = []
        self.secondary_colors_hex = []
        self.more_details = "Mock item details"
        self.original_image_path = f"raw/{self.id}.png"
        self.processed_image_path = f"processed/{self.id}.png"
        self.original_image_url = None
        self.processed_image_url = None
        self.category = "tops"
        self.subcategory = "tops"
        self.fit = "standard"
        self.style = "minimalist"
        self.seasons = ["spring", "summer"]
        self.pattern = "solid"
        self.created_at = datetime.now(timezone.utc)


class MockWardrobeHistory:
    def __init__(self, user_id, item_id, viewed_at=None):
        self.id = uuid.uuid4()
        self.user_id = str(user_id)
        self.item_id = item_id
        self.viewed_at = viewed_at or datetime.now(timezone.utc)


class MockSavedOutfit:
    def __init__(self, user_id, score=90):
        self.id = uuid.uuid4()
        self.user_id = str(user_id)
        self.score = score


# ── Mock DB Session ─────────────────────────────────────────────────────────
class MockDBResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return self

    def all(self):
        return self._data

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None


class MockDBSession:
    def __init__(self):
        self._added = []

    def add(self, obj):
        self._added.append(obj)

    async def delete(self, obj):
        if isinstance(obj, WardrobeCategory) or isinstance(obj, MockCategory):
            _CATEGORIES.pop(obj.id, None)
        elif isinstance(obj, ClothingItem) or isinstance(obj, MockClothingItem):
            _ITEMS.pop(obj.id, None)

    async def commit(self):
        for obj in self._added:
            if isinstance(obj, WardrobeCategory):
                _CATEGORIES[obj.id] = MockCategory(
                    id=obj.id,
                    name=obj.name,
                    subtitle=obj.subtitle,
                    status=obj.status,
                    image=obj.image
                )
            elif isinstance(obj, ClothingItem):
                _ITEMS[obj.id] = MockClothingItem(
                    id=obj.id,
                    name=obj.name,
                    textile=obj.textile,
                    primary_color=obj.primary_color,
                    primary_color_hex=obj.primary_color_hex,
                    categories=obj.categories,
                    verified=obj.verified,
                    has_ai_service=obj.has_ai_service,
                    occasion=obj.occasion,
                    formality=obj.formality,
                    long=obj.long
                )
            elif isinstance(obj, WardrobeHistory):
                _HISTORY.append(MockWardrobeHistory(
                    user_id=obj.user_id,
                    item_id=obj.item_id,
                    viewed_at=obj.viewed_at
                ))
        self._added = []

    async def refresh(self, obj):
        pass

    async def scalar(self, statement):
        sql_str = str(statement).lower()
        if "count" in sql_str:
            if "clothing_items" in sql_str:
                if "verified = true" in sql_str or "verified = :verified_1" in sql_str:
                    return sum(1 for it in _ITEMS.values() if it.verified)
                # Count matching category
                match = re.search(r"clothing_items\.categories.*contains.*", sql_str)
                if match or "clothing_items.categories" in sql_str:
                    # Parse category ID being checked from params
                    # Let's count matching category in simulation
                    # For simplicity, count total matching items
                    cat_id = None
                    # Attempt to find category ID in params or statement
                    for c_id in _CATEGORIES:
                        if c_id in sql_str or any(c_id in str(val) for val in getattr(statement, "compile", lambda: None)().params.values() if hasattr(statement, "compile")):
                            cat_id = c_id
                            break
                    if not cat_id:
                        # Fallback: find it in compilation params
                        try:
                            compiled = statement.compile()
                            for val in compiled.params.values():
                                if isinstance(val, list) and len(val) > 0:
                                    cat_id = val[0]
                                elif isinstance(val, str):
                                    cat_id = val
                        except Exception:
                            pass
                    if cat_id:
                        return sum(1 for it in _ITEMS.values() if it.categories and cat_id in it.categories)
                return len(_ITEMS)
            elif "saved_outfits" in sql_str:
                return len(_SAVED_OUTFITS)
        return 0

    async def execute(self, statement, params=None):
        sql_str = str(statement).lower()
        
        # 1. Update/Delete queries run via text execution
        if "update clothing_items" in sql_str:
            # Simulated array_remove or legacy cleanup
            if params and "cat_id" in params:
                cat_id = params["cat_id"]
                for item in _ITEMS.values():
                    if item.categories and cat_id in item.categories:
                        item.categories = [c for c in item.categories if c != cat_id]
            return MockDBResult([])
            
        # 2. Select queries
        if "wardrobe_categories" in sql_str:
            # Fetch single category
            if "where wardrobe_categories.id = :id_1" in sql_str or "id =" in sql_str:
                cat_id = None
                try:
                    compiled = statement.compile()
                    cat_id = compiled.params.get("id_1") or compiled.params.get("id")
                except Exception:
                    pass
                if not cat_id:
                    # Regex match
                    m = re.search(r"where wardrobe_categories\.id = '([^']+)'", sql_str)
                    if m:
                        cat_id = m.group(1)
                
                cat = _CATEGORIES.get(cat_id)
                return MockDBResult([cat] if cat else [])
                
            # List categories with search filter
            cats = list(_CATEGORIES.values())
            try:
                compiled = statement.compile()
                search_term = next((val for val in compiled.params.values() if isinstance(val, str) and val.startswith("%") and val.endswith("%")), None)
                if search_term:
                    search = search_term.strip("%").lower()
                    cats = [c for c in cats if (c.name and search in c.name.lower()) or (c.subtitle and search in c.subtitle.lower())]
            except Exception:
                pass
            return MockDBResult(cats)
            
        elif "clothing_items" in sql_str:
            if "wardrobe_history" in sql_str:
                # History logs join
                rows = []
                for hist in _HISTORY:
                    item = _ITEMS.get(hist.item_id)
                    if item:
                        rows.append((hist, item))
                return MockDBResult(rows)
                
            # Fetch single item
            if "where clothing_items.id = :id_1" in sql_str or "id =" in sql_str:
                item_id = None
                try:
                    compiled = statement.compile()
                    item_id = compiled.params.get("id_1") or compiled.params.get("id")
                except Exception:
                    pass
                if not item_id and hasattr(statement, "compile"):
                    # Find UUID in params
                    for val in statement.compile().params.values():
                        if isinstance(val, uuid.UUID) or isinstance(val, str):
                            item_id = val
                            break
                if isinstance(item_id, str):
                    try:
                        item_id = uuid.UUID(item_id)
                    except ValueError:
                        pass
                item = _ITEMS.get(item_id)
                return MockDBResult([item] if item else [])
                
            # List items with filters
            items_list = list(_ITEMS.values())
            
            # Filter by categoryId
            cat_id = None
            try:
                compiled = statement.compile()
                for val in compiled.params.values():
                    if isinstance(val, list) and len(val) == 1 and isinstance(val[0], str):
                        cat_id = val[0]
                        break
                    elif isinstance(val, str) and val in _CATEGORIES:
                        cat_id = val
                        break
            except Exception:
                pass
                
            if not cat_id:
                for c_id in _CATEGORIES:
                    if f"contains(['{c_id}'])" in sql_str or f"'{c_id}'" in sql_str:
                        cat_id = c_id
                        break
                        
            if cat_id:
                items_list = [it for it in items_list if it.categories and cat_id in it.categories]
                
            # Filter by search
            search_term = None
            try:
                compiled = statement.compile()
                search_term = next((val for val in compiled.params.values() if isinstance(val, str) and val.startswith("%") and val.endswith("%")), None)
            except Exception:
                pass
            if search_term:
                search = search_term.strip("%").lower()
                items_list = [it for it in items_list if (it.name and search in it.name.lower()) or (it.textile and search in it.textile.lower())]
                
            return MockDBResult(items_list)
            
        elif "wardrobe_history" in sql_str:
            # Check single history entry
            user_id = None
            item_id = None
            try:
                compiled = statement.compile()
                user_id = compiled.params.get("user_id_1")
                item_id = compiled.params.get("item_id_1")
            except Exception:
                pass
            if user_id and item_id:
                hist = [h for h in _HISTORY if h.user_id == str(user_id) and h.item_id == item_id]
                return MockDBResult(hist)
            return MockDBResult(_HISTORY)
            
        return MockDBResult([])


# ── Pytest Fixture setup ─────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def setup_mock_db():
    """Initializes in-memory stores with test fixtures and mocks FastAPI dependencies."""
    global _USERS, _CATEGORIES, _ITEMS, _HISTORY, _SAVED_OUTFITS
    
    # 1. Setup mock users
    user = MockUser()
    _USERS = {str(user.id): user}
    
    # 2. Setup standard categories
    _CATEGORIES = {
        "tops": MockCategory("tops", "Tops", "Shirts and knits"),
        "bottoms": MockCategory("bottoms", "Bottoms", "Pants and jeans"),
        "footwear": MockCategory("footwear", "Footwear", "Shoes and sneakers"),
    }
    
    # 3. Setup items
    item1 = MockClothingItem(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        name="Stone Cashmere Knit",
        textile="Cashmere",
        primary_color="Stone",
        primary_color_hex="#D2B48C",
        categories=["tops"],
        verified=True,
        has_ai_service=True,
        occasion="casual",
        formality=5
    )
    item2 = MockClothingItem(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        name="Selvedge Denim Jeans",
        textile="Denim",
        primary_color="Indigo",
        primary_color_hex="#4B0082",
        categories=["bottoms"],
        verified=False,
        has_ai_service=False,
        occasion="work",
        formality=3
    )
    # Add multi-category item (Many-to-Many Categories)
    item3 = MockClothingItem(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        name="Versatile Shirt Jacket",
        textile="Wool Blend",
        primary_color="Charcoal",
        primary_color_hex="#36454F",
        categories=["tops", "bottoms"], # belongs to multiple
        verified=True,
        has_ai_service=False,
        occasion="casual",
        formality=4
    )
    _ITEMS = {
        item1.id: item1,
        item2.id: item2,
        item3.id: item3
    }
    
    # 4. Setup mock history and saved outfits
    _HISTORY = [
        MockWardrobeHistory(user.id, item1.id, datetime.now(timezone.utc) - timedelta(hours=2)),
        MockWardrobeHistory(user.id, item2.id, datetime.now(timezone.utc) - timedelta(days=1))
    ]
    _SAVED_OUTFITS = [
        MockSavedOutfit(user.id),
        MockSavedOutfit(user.id)
    ]
    
    # 5. Apply dependency overrides
    async def mock_get_db_override():
        yield MockDBSession()
        
    async def mock_optional_user_override():
        return user

    app.dependency_overrides[get_db] = mock_get_db_override
    app.dependency_overrides[get_optional_current_user] = mock_optional_user_override
    
    yield
    
    # Teardown
    app.dependency_overrides.clear()


# ── Test Suite ───────────────────────────────────────────────────────────────

def test_get_categories_list():
    """1. Tests listing categories with item counts and search filter."""
    # List categories
    response = client.get("/api/wardrobe/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    # Verify counts: tops has item1 and item3 (count = 2)
    tops = next(c for c in data if c["id"] == "tops")
    assert tops["count"] == 2
    
    # Verify search
    response = client.get("/api/wardrobe/categories?search=tops")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "tops"


def test_categories_crud():
    """2. Tests creation, retrieval, update and cascading orphan updates on Category DELETE."""
    # Create category
    payload = {
        "name": "Evening Attire",
        "subtitle": "Gowns, suits, tuxedos",
        "image": "http://cdn.com/evening.jpg"
    }
    response = client.post("/api/wardrobe/categories", json=payload)
    assert response.status_code == 201
    new_cat = response.json()
    assert new_cat["id"] == "evening-attire"
    assert new_cat["name"] == "Evening Attire"
    
    # Get created category
    response = client.get("/api/wardrobe/categories/evening-attire")
    assert response.status_code == 200
    assert response.json()["name"] == "Evening Attire"
    
    # Update category
    update_payload = {"subtitle": "Formal evening wear"}
    response = client.put("/api/wardrobe/categories/evening-attire", json=update_payload)
    assert response.status_code == 200
    assert response.json()["subtitle"] == "Formal evening wear"
    
    # Delete category with keep_orphans cleanup
    response = client.delete("/api/wardrobe/categories/evening-attire?cleanup=keep_orphans")
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Ensure it's deleted
    response = client.get("/api/wardrobe/categories/evening-attire")
    assert response.status_code == 404


def test_list_items_with_many_to_many():
    """3. Tests item search and many-to-many category tagging queries."""
    # Query tops
    response = client.get("/api/wardrobe/items?categoryId=tops")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2 # item1 and item3
    assert data["meta"]["totalCount"] == 2
    
    # Query multi-category (belongs to tops AND bottoms)
    response = client.get("/api/wardrobe/items?categoryId=bottoms")
    assert response.status_code == 200
    data = response.json()
    # bottoms contains item2 and item3
    assert len(data["data"]) == 2
    
    # Search filter
    response = client.get("/api/wardrobe/items?search=Stone")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Stone Cashmere Knit"


def test_items_crud():
    """4. Tests manual creation, get detail, and deletion of wardrobe garments."""
    # Create item
    payload = {
        "name": "White Linen Shirt",
        "textile": "Linen",
        "colorName": "White",
        "colorHex": "#FFFFFF",
        "secondaryColors": [{"name": "Ivory", "hex": "#FFFFF0"}],
        "moreDetails": "Perfect linen shirt for summer",
        "occasion": "casual",
        "image": "http://cdn.com/shirt.jpg",
        "verified": True,
        "long": False,
        "hasAIService": True,
        "categories": ["tops"]
    }
    response = client.post("/api/wardrobe/items", json=payload)
    assert response.status_code == 201
    new_item = response.json()
    assert new_item["name"] == "White Linen Shirt"
    assert new_item["verified"] is True
    
    item_id = new_item["id"]
    
    # Get details
    response = client.get(f"/api/wardrobe/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["textile"] == "Linen"
    
    # Update item
    update_payload = {"name": "Premium White Linen Shirt"}
    response = client.put(f"/api/wardrobe/items/{item_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Premium White Linen Shirt"
    
    # Delete item
    response = client.delete(f"/api/wardrobe/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_wardrobe_stats():
    """5. Tests closet statistics calculations."""
    response = client.get("/api/wardrobe/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["totalPieces"] == 3
    # item1 and item3 are verified (2 out of 3 -> 66.7%)
    assert data["syncPercentage"] == 66.7
    assert data["outfitsCount"] == 2


def test_sidebar_history_logging():
    """6. Verifies that GET item details triggers sidebar history logging with relative timestamps."""
    # Retrieve item1 details
    item_id = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/api/wardrobe/items/{item_id}")
    assert response.status_code == 200
    
    # Verify it exists in recently viewed sidebar
    response = client.get("/api/wardrobe/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    
    # Ensure correct pagination meta envelope
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["currentPage"] == 1
    
    # Verify relative time-label formatting (should be '2 hours ago' or similar)
    hist_entry = next(h for h in data["data"] if h["item"]["id"] == item_id)
    assert "hour" in hist_entry["relativeTimeLabel"] or "minute" in hist_entry["relativeTimeLabel"] or "Just now" in hist_entry["relativeTimeLabel"]


def test_ai_scanner_image_suggestion():
    """7. Tests AI Scanner Suggestion classifying dominant color, fabrics, and confidence scores."""
    # Mock image upload file payload
    mock_file = io.BytesIO(b"transparent mock png bytes")
    mock_file.name = "grey_pants.png"
    
    response = client.post(
        "/api/wardrobe/scan",
        files={"image": ("grey_pants.png", mock_file, "image/png")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify deterministic keyword checks for "pants" keyword
    assert data["colorName"] == "Slate Grey"
    assert data["colorHex"] == "#708090"
    assert data["textile"] == "Wool Blend"
    assert data["category"] == "bottoms"
    assert data["subcategory"] == "trousers"
    assert data["confidence"] == 0.89
    assert "tempFileKey" in data
