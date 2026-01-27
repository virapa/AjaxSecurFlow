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
    """Test login with unified identity (Ajax)."""
    with patch("backend.app.api.v1.auth.AjaxClient") as MockAjax, \
         patch("backend.app.api.v1.auth.crud_user.get_user_by_email") as mock_get_user, \
         patch("backend.app.api.v1.auth.security_service") as mock_sec:
        
        # 1. Mock Ajax success
        mock_ajax_instance = MockAjax.return_value
        mock_ajax_instance.login_with_credentials = AsyncMock(return_value={"userId": "123", "sessionToken": "t"})
        
        # 2. Mock Security Service
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.reset_login_failures = AsyncMock()
        
        # 3. Mock DB user
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "admin@example.com"
        mock_get_user.return_value = mock_user
        
        response = await client.post(
            "/api/v1/auth/token", 
            data={"username": "admin@example.com", "password": "secret"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        mock_sec.check_ip_lockout.assert_called_once()
        mock_sec.reset_login_failures.assert_called_once()

@pytest.mark.asyncio
async def test_auth_login_invalid(client, mock_db):
    """Test login failure with unified identity."""
    from backend.app.services.ajax_client import AjaxAuthError
    with patch("backend.app.api.v1.auth.AjaxClient") as MockAjax, \
         patch("backend.app.api.v1.auth.security_service") as mock_sec:
        
        mock_ajax_instance = MockAjax.return_value
        mock_ajax_instance.login_with_credentials = AsyncMock(side_effect=AjaxAuthError("Invalid"))
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.track_login_failure = AsyncMock()
        
        response = await client.post(
            "/api/v1/auth/token", 
            data={"username": "wrong", "password": "wrong"}
        )
        assert response.status_code == 401
        mock_sec.track_login_failure.assert_called_once()

@pytest.mark.asyncio
async def test_proxy_endpoint_protected(client, mock_rate_limiter):
    response = await client.get("/api/v1/ajax/some/resource")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_proxy_endpoint_success(client, mock_ajax_client, mock_rate_limiter, mock_db):
    """Test successful proxy request with unified auth."""
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.email = "admin@example.com"
    mock_user.subscription_status = "active"
    
    # Updated mocks to use unified identity logic
    with patch("backend.app.api.v1.auth.AjaxClient") as MockAjax, \
         patch("backend.app.api.v1.auth.crud_user.get_user_by_email") as mock_get_user, \
         patch("backend.app.api.v1.auth.security_service") as mock_sec, \
         patch("backend.app.api.v1.proxy.audit_service.log_action") as mock_log, \
         patch("backend.app.api.v1.proxy.billing_service.is_subscription_active") as mock_sub:
        
        # 1. Setup Auth Mocks
        mock_ajax_instance = MockAjax.return_value
        mock_ajax_instance.login_with_credentials = AsyncMock(return_value={"userId": "123", "sessionToken": "t"})
        mock_get_user.return_value = mock_user
        mock_sub.return_value = True
        mock_log.return_value = None
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.reset_login_failures = AsyncMock()
        
        # 2. Setup Proxy Mock (the actual request method)
        # Note: mock_ajax_client is a patch on backend.app.api.v1.proxy.AjaxClient
        mock_ajax_client.request = AsyncMock(return_value={"data": "mocked_response"})
        
        # 3. Get Token
        auth_resp = await client.post(
            "/api/v1/auth/token", 
            data={"username": "admin@example.com", "password": "secret"}
        )
        token = auth_resp.json()["access_token"]
        
        # 4. Access Proxy
        response = await client.get(
            "/api/v1/ajax/some/resource",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"data": "mocked_response"}
        
        # Verify call used user_email
        mock_ajax_client.request.assert_called_once()
        _, kwargs = mock_ajax_client.request.call_args
        assert kwargs["user_email"] == "admin@example.com"
