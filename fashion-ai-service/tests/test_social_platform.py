import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timezone

from app.main import app
from app.routes.wardrobe import get_db

client = TestClient(app)

@pytest.fixture
def mock_db_session(monkeypatch):
    """Provides a mocked SQLAlchemy session for isolated API testing."""
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    target_user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")

    class MockUser:
        def __init__(self, id, username, vanity_username=""):
            self.id = id
            self.username = username
            self.vanity_username = vanity_username or username
            self.first_name = "Social"
            self.last_name = "Curator"
            self.bio = "Streetwear editor | Tokyo"
            self.avatar_url = None
            self.verified_badge = True
            self.favorite_brands = ["COS", "Zara"]
            self.wardrobe_visibility = "public"
            self.style_personas = ["streetwear"]

    class MockPost:
        def __init__(self, id, user_id, image_url, caption):
            self.id = id
            self.user_id = user_id
            self.image_url = image_url
            self.caption = caption
            self.weather_context = "rainy"
            self.occasion_tag = "casual"
            self.style_persona = "streetwear"
            self.created_at = datetime.now(timezone.utc)
            self.community_id = None
            self.tagged_items = []

    class MockResult:
        def __init__(self, data=None, raw_all=False):
            self.data = data or []
            self.raw_all = raw_all
        def scalar_one_or_none(self):
            return self.data[0] if self.data else None
        def scalar_one(self):
            return self.data[0]
        def scalars(self):
            class MockScalars:
                def all(self_scalars):
                    return self.data
            return MockScalars()
        def all(self):
            if self.raw_all:
                return self.data
            return [(d, None) for d in self.data]

    class MockDB:
        def __init__(self):
            self.added = []
            self.deleted = []

        async def execute(self, stmt):
            # Inspect SQL representation for testing routers mapping
            stmt_str = str(stmt).lower()
            if "style_persona" in stmt_str and "count" in stmt_str:
                return MockResult([("streetwear", 1, "http://image.png")], raw_all=True)
            elif "occasion_tag" in stmt_str and "count" in stmt_str:
                return MockResult([("casual", 1)], raw_all=True)
            elif "users" in stmt_str:
                if "ilike" in stmt_str:
                    # User profile fetch
                    return MockResult([MockUser(test_user_id, "social_curator")])
                return MockResult([MockUser(test_user_id, "social_curator")])
            elif "social_posts" in stmt_str:
                return MockResult([MockPost(uuid.uuid4(), test_user_id, "http://image.png", "test post")])
            return MockResult([])

        async def get(self, model, ident):
            if ident == test_user_id:
                return MockUser(test_user_id, "social_curator")
            return MockUser(target_user_id, "other_creator")

        async def scalar(self, stmt):
            stmt_str = str(stmt).lower()
            if "user_follows" in stmt_str:
                return 0
            if "users" in stmt_str or "count" in stmt_str:
                return 1
            if "social_posts" in stmt_str:
                return 1
            return 0

        def add(self, obj):
            self.added.append(obj)
        async def delete(self, obj):
            self.deleted.append(obj)
        async def commit(self): pass
        async def refresh(self, obj): pass

    mock_db = MockDB()

    # Isolated monkeypatch overrides for CLIP vector embedding generators
    import numpy as np
    from app.ai.embedding_service import FashionEmbeddingService
    monkeypatch.setattr(FashionEmbeddingService, "generate_image_embedding", lambda self, img: np.array([0.1] * 512, dtype=np.float32))
    monkeypatch.setattr(FashionEmbeddingService, "generate_text_embedding", lambda self, text: np.array([0.1] * 512, dtype=np.float32))
    
    async def mock_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = mock_get_db
    yield mock_db
    app.dependency_overrides.clear()


def test_get_social_profile(mock_db_session):
    """Verifies that GET /v1/social/profile/{username} fetches accurate profile metrics."""
    response = client.get("/v1/social/profile/social_curator")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "social_curator"
    assert data["bio"] == "Streetwear editor | Tokyo"
    assert data["followers_count"] == 0
    assert data["posts_count"] == 1


def test_toggle_follow_creator(mock_db_session):
    """Verifies follow graph actions."""
    target_id = uuid.uuid4()
    response = client.post(
        f"/v1/social/follow/{target_id}",
        json={"action": "follow"}
    )
    assert response.status_code == 200
    assert "Successfully followed" in response.json()["message"]


def test_create_outfit_post(mock_db_session):
    """Verifies posting outfits with captions and image coordinate tagging hotspots."""
    post_payload = {
        "image_url": "https://cdn.vouge.ai/outfit1.png",
        "caption": "Rainy afternoon outfit check.",
        "weather_context": "rainy",
        "occasion_tag": "work",
        "style_persona": "streetwear",
        "tagged_items": [
            {
                "wardrobe_item_id": str(uuid.uuid4()),
                "x_coord": 45.5,
                "y_coord": 30.0
            }
        ]
    }
    response = client.post("/v1/social/posts", json=post_payload)
    assert response.status_code == 201
    assert len(mock_db_session.added) > 0
    added_post = mock_db_session.added[0]
    assert added_post.caption == "Rainy afternoon outfit check."


def test_toggle_like_and_saves(mock_db_session):
    """Verifies post liking / saving toggles successfully."""
    post_id = uuid.uuid4()
    response = client.post(f"/v1/social/posts/{post_id}/like")
    assert response.status_code == 200
    assert "liked" in response.json()


def test_commenting_workflows(mock_db_session):
    """Verifies comments posting successfully."""
    post_id = uuid.uuid4()
    comment_payload = {
        "content": "Clean tailoring on those trousers!",
    }
    response = client.post(f"/v1/social/posts/{post_id}/comments", json=comment_payload)
    assert response.status_code == 201
    assert response.json()["content"] == "Clean tailoring on those trousers!"


def test_feed_listing_routers(mock_db_session):
    """Verifies that curated and trending feeds return list data successfully."""
    response = client.get("/v1/social/feed/curated")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_explore_showroom(mock_db_session):
    """Verifies that GET /v1/social/explore retrieves aggregates successfully."""
    response = client.get("/v1/social/explore")
    assert response.status_code == 200
    data = response.json()
    assert "trending_posts" in data
    assert "trending_personas" in data
    assert "popular_creators" in data
    assert "trending_occasions" in data

    assert len(data["trending_personas"]) > 0
    assert data["trending_personas"][0]["name"] == "streetwear"
    assert data["trending_personas"][0]["post_count"] == 1
    assert data["trending_personas"][0]["popular_image_url"] == "http://image.png"

    assert len(data["trending_occasions"]) > 0
    assert data["trending_occasions"][0]["name"] == "casual"
    assert data["trending_occasions"][0]["post_count"] == 1

    assert len(data["popular_creators"]) > 0
    assert data["popular_creators"][0]["username"] == "social_curator"


def test_social_semantic_search(mock_db_session):
    """Verifies that GET /v1/social/search query searches semantically using CLIP embeddings."""
    response = client.get("/v1/social/search?q=oversized+streetwear+autumn")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["caption"] == "test post"


