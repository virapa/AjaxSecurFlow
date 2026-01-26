import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch
from backend.app.core.config import settings

@pytest_asyncio.fixture
async def client():
    # Use httpx.ASGITransport for the transport
    # base_url should point to what the tests use.
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_ajax_client():
    with patch("backend.app.api.v1.proxy.AjaxClient") as MockClient:
        instance = MockClient.return_value
        instance.request = AsyncMock(return_value={"data": "mocked_response"})
        yield instance

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
async def test_auth_login(client):
    # Use the credentials from Settings (mocked or default)
    username = settings.FIRST_SUPERUSER
    password = settings.FIRST_SUPERUSER_PASSWORD
    
    response = await client.post(
        "/api/v1/auth/token", 
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_auth_login_invalid(client):
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
async def test_proxy_endpoint_success(client, mock_ajax_client, mock_rate_limiter):
    # 1. Get Token using correct credentials
    username = settings.FIRST_SUPERUSER
    password = settings.FIRST_SUPERUSER_PASSWORD
    
    auth_resp = await client.post(
        "/api/v1/auth/token", 
        data={"username": username, "password": password}
    )
    assert auth_resp.status_code == 200, f"Auth failed: {auth_resp.text}"
    token = auth_resp.json()["access_token"]
    
    # 2. Access Proxy
    response = await client.get(
        "/api/v1/ajax/some/resource",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"data": "mocked_response"}
    
    mock_ajax_client.request.assert_called_with(
        method="GET",
        endpoint="/some/resource",
        json=None
    )
