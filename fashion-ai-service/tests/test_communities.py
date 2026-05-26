import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timezone

from app.main import app
from app.routes.wardrobe import get_db
from app.database.models import User

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    """Provides a mocked SQLAlchemy session for community endpoints testing."""
    test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    target_community_id = uuid.UUID("00000000-0000-0000-0000-000000000003")

    class MockUser:
        def __init__(self):
            self.id = test_user_id
            self.username = "social_curator"
            self.vanity_username = "Aesthetic_Curator"
            self.avatar_url = None
            self.verified_badge = True
            self.favorite_brands = ["COS"]
            self.style_personas = ["minimalist"]

    class MockCommunity:
        def __init__(self):
            self.id = target_community_id
            self.name = "Streetwear Tokyo"
            self.slug = "streetwear-tokyo"
            self.description = "Tokyo style layering"
            self.cover_image_url = "http://image.png"
            self.rules = "Be friendly"
            self.creator_id = test_user_id
            self.created_at = datetime.now(timezone.utc)

    class MockMember:
        def __init__(self):
            self.community_id = target_community_id
            self.user_id = test_user_id
            self.role = "member"  # member role so leave_community is permitted
            self.joined_at = datetime.now(timezone.utc)
            self.user = MockUser()

    class MockPost:
        def __init__(self):
            self.id = uuid.uuid4()
            self.user_id = test_user_id
            self.image_url = "http://image.png"
            self.caption = "Tokyo flat lay check"
            self.weather_context = "rainy"
            self.occasion_tag = "casual"
            self.style_persona = "streetwear"
            self.community_id = target_community_id
            self.created_at = datetime.now(timezone.utc)
            self.tagged_items = []

    class MockResult:
        def __init__(self, data=None):
            self.data = data or []
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
            return self.data

    class MockDB:
        def __init__(self):
            self.added = []
            self.deleted = []

        async def execute(self, stmt):
            stmt_str = str(stmt).lower()
            if "users" in stmt_str:
                return MockResult([MockUser()])
            elif "fashion_communities" in stmt_str:
                if "lower" in stmt_str or "like" in stmt_str:
                    # Uniqueness check in create_community (or matching query)
                    return MockResult([])
                return MockResult([MockCommunity()])
            elif "community_members" in stmt_str:
                return MockResult([MockMember()])
            elif "social_posts" in stmt_str:
                return MockResult([MockPost()])
            return MockResult([])

        async def get(self, model, ident):
            return MockUser()

        async def scalar(self, stmt):
            stmt_str = str(stmt).lower()
            if "community_members" in stmt_str or "count" in stmt_str:
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

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db
    yield mock_db
    app.dependency_overrides.clear()


def test_create_fashion_community(mock_db_session):
    """Verifies POST /v1/social/communities endpoint."""
    payload = {
        "name": "Streetwear Tokyo",
        "description": "Tokyo style layering",
        "cover_image_url": "http://image.png",
        "rules": "Be friendly"
    }
    response = client.post("/v1/social/communities", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Streetwear Tokyo"
    assert data["slug"] == "streetwear-tokyo"
    assert data["is_joined"] is True
    assert len(mock_db_session.added) > 0


def test_list_communities(mock_db_session):
    """Verifies GET /v1/social/communities list endpoint."""
    response = client.get("/v1/social/communities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["slug"] == "streetwear-tokyo"


def test_get_my_communities(mock_db_session):
    """Verifies GET /v1/social/communities/my returns user's joined communities."""
    response = client.get("/v1/social/communities/my")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_community_details(mock_db_session):
    """Verifies GET /v1/social/communities/{slug} returns detailed community info."""
    response = client.get("/v1/social/communities/streetwear-tokyo")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Streetwear Tokyo"
    assert data["slug"] == "streetwear-tokyo"


def test_join_and_leave_community(mock_db_session):
    """Verifies join/leave community routes."""
    comm_id = uuid.uuid4()
    
    # Mock join
    response = client.post(f"/v1/social/communities/{comm_id}/join")
    assert response.status_code == 200
    
    # Mock leave
    response = client.post(f"/v1/social/communities/{comm_id}/leave")
    assert response.status_code == 200


def test_list_community_posts(mock_db_session):
    """Verifies listing posts posted inside a community."""
    comm_id = uuid.uuid4()
    response = client.get(f"/v1/social/communities/{comm_id}/posts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_community_members(mock_db_session):
    """Verifies listing members of a community."""
    comm_id = uuid.uuid4()
    response = client.get(f"/v1/social/communities/{comm_id}/members")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["username"] == "social_curator"
