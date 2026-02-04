import os
import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from unittest.mock import AsyncMock

# Set environment variables for testing ONLY if not already defined (Docker-friendly)
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "ajax_proxy")
os.environ.setdefault("POSTGRES_HOST", "localhost")

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:5432/{os.environ['POSTGRES_DB']}"

os.environ.setdefault("REDIS_URL", f"redis://{os.environ['POSTGRES_HOST']}:6379/0")
os.environ["AJAX_API_KEY"] = "test_key"
os.environ["AJAX_LOGIN"] = "test_login"
os.environ["AJAX_PASSWORD"] = "test_password"
os.environ["SECRET_KEY"] = "supersecretkeyformocking12345"
os.environ["ENABLE_DEVELOPER_MODE"] = "False"

from backend.app.main import app

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    from backend.app.core.db import get_db
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides = {}

@pytest.fixture
def mock_user_subscription(mock_db):
    """Overrides get_current_user to return a subscribed user."""
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.email = "sub@example.com"
    mock_user.subscription_status = "active"
    mock_user.subscription_expires_at = None
    
    from backend.app.api.v1.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    app.dependency_overrides = {}

@pytest.fixture
def mock_user_no_subscription(mock_db):
    """Overrides get_current_user to return a user WITHOUT subscription."""
    mock_user = AsyncMock()
    mock_user.id = 2
    mock_user.email = "free@example.com"
    mock_user.subscription_status = "free"
    mock_user.subscription_expires_at = None
    
    from backend.app.api.v1.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    app.dependency_overrides = {}
