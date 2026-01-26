import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch
from backend.app.core.config import settings

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_ajax_client():
    with patch("backend.app.api.v1.proxy.AjaxClient") as MockClient:
        instance = MockClient.return_value
        instance.request = AsyncMock(return_value={"data": "mocked_response"})
        yield instance

@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    # We override the dependency in FastAPI directly
    from backend.app.core.db import get_db
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides = {}

@pytest.fixture
def mock_rate_limiter():
    from backend.app.services.rate_limiter import RateLimiter, get_redis
    async def mock_get_redis():
        mock = AsyncMock()
        mock.incr.return_value = 1
        return mock
    app.dependency_overrides[get_redis] = mock_get_redis
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_auth_login(client, mock_db):
    with patch("backend.app.api.v1.auth.crud_user.authenticate_user") as mock_auth:
        mock_user = AsyncMock()
        mock_user.email = "admin@example.com"
        mock_auth.return_value = mock_user
        
        response = await client.post(
            "/api/v1/auth/token", 
            data={"username": "admin@example.com", "password": "secret"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_auth_login_invalid(client, mock_db):
    with patch("backend.app.api.v1.auth.crud_user.authenticate_user") as mock_auth:
        mock_auth.return_value = None
        response = await client.post(
            "/api/v1/auth/token", 
            data={"username": "wrong", "password": "wrong"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_proxy_endpoint_protected(client, mock_rate_limiter):
    response = await client.get("/api/v1/ajax/some/resource")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_proxy_endpoint_success(client, mock_ajax_client, mock_rate_limiter, mock_db):
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.email = "admin@example.com"
    mock_user.subscription_status = "active"
    
    with patch("backend.app.api.v1.auth.crud_user.authenticate_user") as mock_auth, \
         patch("backend.app.api.v1.auth.crud_user.get_user_by_email") as mock_get_user, \
         patch("backend.app.api.v1.proxy.audit_service.log_action") as mock_log:
        
        mock_auth.return_value = mock_user
        mock_get_user.return_value = mock_user
        mock_log.return_value = None
        
        # Get Token
        auth_resp = await client.post(
            "/api/v1/auth/token", 
            data={"username": "admin@example.com", "password": "secret"}
        )
        token = auth_resp.json()["access_token"]
        
        # 2. Access Proxy
        response = await client.get(
            "/api/v1/ajax/some/resource",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"data": "mocked_response"}
        
        # Verify Audit log was called
        mock_log.assert_called_once()
        _, kwargs = mock_log.call_args
        assert kwargs["user_id"] == 1
        assert kwargs["action"] == "PROXY_GET"
