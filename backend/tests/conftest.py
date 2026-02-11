import os
from datetime import datetime as dt_datetime, timezone, timedelta
import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

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

@pytest.fixture(autouse=True)
def mock_redis():
    """Global Redis mock for all tests."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.incr = AsyncMock(return_value=1)
    mock.delete = AsyncMock(return_value=True)
    mock.expire = AsyncMock(return_value=True)
    
    # Also handle Redis pipeline for atomic operations
    mock_pipeline = AsyncMock()
    mock_pipeline.execute = AsyncMock(return_value=[1, 1])
    # pipeline methods return the pipeline object for chaining
    mock_pipeline.incr = MagicMock(return_value=mock_pipeline)
    mock_pipeline.expire = MagicMock(return_value=mock_pipeline)
    mock_pipeline.set = MagicMock(return_value=mock_pipeline)
    
    mock.pipeline = MagicMock(return_value=mock_pipeline)
    
    # Also handle Redis dependency provider
    from backend.app.shared.infrastructure.redis.deps import get_redis
    app.dependency_overrides[get_redis] = lambda: mock
    yield mock
    # Clear Redis override after each test
    if get_redis in app.dependency_overrides:
        del app.dependency_overrides[get_redis]

@pytest.fixture(autouse=True)
def mock_db():
    added_objects = []
    mock_session = AsyncMock()
    
    # Standardize result behavior
    mock_result = MagicMock()
    def get_any_object():
        return added_objects[0] if added_objects else None
        
    mock_result.scalar_one_or_none.side_effect = get_any_object
    
    # scalars().first() behavior
    mock_scalars = MagicMock()
    mock_scalars.first.side_effect = get_any_object
    
    def filtered_all():
        # Heuristic: if we want logs, look for objects with 'action'
        # This is a bit hacky but works for the integration test's mocked DB
        return [obj for obj in added_objects if hasattr(obj, "action")] or added_objects
        
    mock_scalars.all.side_effect = filtered_all
    mock_scalars.one_or_none.side_effect = get_any_object
    mock_result.scalars.return_value = mock_scalars
    
    # mock_session already defined in previous chunk or here
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.get = AsyncMock(side_effect=lambda model, id: get_any_object())
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Non-coroutine methods in SQLAlchemy AsyncSession
    mock_session.add = MagicMock()
    def side_effect_add(obj):
        # Provide dummy values for Pydantic validation in tests
        if hasattr(obj, "id") and (obj.id is None or isinstance(obj.id, MagicMock)):
            obj.id = 1
        if hasattr(obj, "is_active") and (obj.is_active is None or isinstance(obj.is_active, MagicMock)):
            obj.is_active = True
        if hasattr(obj, "subscription_plan") and (obj.subscription_plan is None or isinstance(obj.subscription_plan, MagicMock)):
            obj.subscription_plan = "free"
        if hasattr(obj, "subscription_status") and (obj.subscription_status is None or isinstance(obj.subscription_status, MagicMock)):
            obj.subscription_status = "active"
        added_objects.append(obj)
    mock_session.add.side_effect = side_effect_add
    
    mock_session.refresh = AsyncMock() # refresh IS async in AsyncSession
    mock_session.delete = MagicMock() # delete is sync
    
    from backend.app.shared.infrastructure.database.session import get_db
    
    # Mock for Depends(get_db)
    app.dependency_overrides[get_db] = lambda: mock_session
    
    # Mock for async with async_session_factory()
    from unittest.mock import patch
    with patch("backend.app.shared.infrastructure.database.session.async_session_factory") as mock_factory:
        # async with async_session_factory() returns an async context manager that yields the session
        mock_factory.return_value.__aenter__.return_value = mock_session
        yield mock_session
    
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest.fixture
def mock_user_subscription(mock_db):
    """Overrides get_current_user to return a subscribed user."""
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.email = "sub@example.com"
    mock_user.subscription_status = "active"
    mock_user.subscription_plan = "premium"
    mock_user.subscription_expires_at = None
    
    from backend.app.modules.auth.service import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

@pytest.fixture
def mock_user_no_subscription(mock_db):
    """Overrides get_current_user to return a user WITHOUT subscription."""
    mock_user = AsyncMock()
    mock_user.id = 2
    mock_user.email = "free@example.com"
    mock_user.subscription_status = "free"
    mock_user.subscription_plan = "free"
    mock_user.subscription_expires_at = None
    
    from backend.app.modules.auth.service import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
