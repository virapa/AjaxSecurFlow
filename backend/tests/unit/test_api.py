import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch
from backend.app.core.config import settings
from backend.app.shared.infrastructure.database.session import get_db
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
from backend.app.shared.infrastructure.redis.deps import get_redis
from backend.app.modules.ajax.service import AjaxAuthError
from backend.app.modules.auth.models import User

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest.fixture
def mock_ajax_client():
    mock_instance = AsyncMock()
    mock_instance.request = AsyncMock(return_value={"data": "mocked_response"})
    mock_instance.login_with_credentials = AsyncMock(return_value={"userId": "123", "sessionToken": "t"})
    mock_instance.get_user_info = AsyncMock(return_value={"email": "admin@example.com", "name": "Admin"})
    
    app.dependency_overrides[get_ajax_client] = lambda: mock_instance
    yield mock_instance
    if get_ajax_client in app.dependency_overrides:
        del app.dependency_overrides[get_ajax_client]

@pytest.fixture
def mock_rate_limiter():
    async def mock_get_redis():
        mock = AsyncMock()
        mock.incr.return_value = 1
        mock.exists.return_value = False
        mock.set.return_value = True
        return mock
    
    app.dependency_overrides[get_redis] = mock_get_redis
    yield
    if get_redis in app.dependency_overrides:
        del app.dependency_overrides[get_redis]

@pytest.mark.asyncio
async def test_auth_login(client, mock_db):
    """Test login with unified identity (Ajax)."""
    with patch("backend.app.modules.security.service.log_action") as mock_log_req, \
         patch("backend.app.modules.auth.service.get_user_by_email") as mock_get_user, \
         patch("backend.app.modules.auth.service.security_service") as mock_sec:
        
        mock_log_req.return_value = AsyncMock()
        
        # 1. Mock Ajax success via dependency override
        mock_ajax_instance = AsyncMock()
        mock_ajax_instance.login_with_credentials = AsyncMock(return_value={"userId": "123", "sessionToken": "t"})
        app.dependency_overrides[get_ajax_client] = lambda: mock_ajax_instance
        
        # 2. Mock Security Service
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.reset_login_failures = AsyncMock()
        
        # 3. Mock DB user
        mock_user = AsyncMock(spec=User)
        mock_user.id = 1
        mock_user.email = "admin@example.com"
        mock_get_user.return_value = mock_user
        
        response = await client.post(
            "/api/v1/auth/token", 
            json={"username": "admin@example.com", "password": "secret"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        if get_ajax_client in app.dependency_overrides:
            del app.dependency_overrides[get_ajax_client]

@pytest.mark.asyncio
async def test_auth_login_new_user_provisioning(client, mock_db):
    """Test login with new user that needs auto-provisioning."""
    with patch("backend.app.modules.security.service.log_action") as mock_log_req, \
         patch("backend.app.modules.auth.service.get_user_by_email") as mock_get_user, \
         patch("backend.app.modules.auth.service.create_user") as mock_create_user, \
         patch("backend.app.modules.auth.service.security_service") as mock_sec:
        
        mock_log_req.return_value = AsyncMock()
        
        # 1. Mock Ajax success via dependency override
        mock_ajax_instance = AsyncMock()
        mock_ajax_instance.login_with_credentials = AsyncMock(return_value={"userId": "123", "sessionToken": "t"})
        app.dependency_overrides[get_ajax_client] = lambda: mock_ajax_instance
        
        # 2. Mock DB user NOT found initially
        mock_get_user.return_value = None
        
        # 3. Mock DB user creation success
        mock_new_user = AsyncMock(spec=User)
        mock_new_user.id = 99
        mock_new_user.email = "new@example.com"
        mock_create_user.return_value = mock_new_user
        
        # 4. Mock Security Service
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.reset_login_failures = AsyncMock()
        
        response = await client.post(
            "/api/v1/auth/token", 
            json={"username": "new@example.com", "password": "password123"}
        )
        
        assert response.status_code == 200
        mock_create_user.assert_called_once()
        
        if get_ajax_client in app.dependency_overrides:
            del app.dependency_overrides[get_ajax_client]

@pytest.mark.asyncio
async def test_auth_login_invalid(client, mock_db):
    """Test login failure with unified identity."""
    with patch("backend.app.modules.security.service.log_action") as mock_log_req, \
         patch("backend.app.modules.auth.service.security_service") as mock_sec:
        
        mock_log_req.return_value = AsyncMock()
        
        mock_ajax_instance = AsyncMock()
        mock_ajax_instance.login_with_credentials = AsyncMock(side_effect=AjaxAuthError("Invalid"))
        app.dependency_overrides[get_ajax_client] = lambda: mock_ajax_instance
        
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.track_login_failure = AsyncMock()
        
        response = await client.post(
            "/api/v1/auth/token", 
            json={"username": "wrong", "password": "wrong"}
        )
        assert response.status_code == 401
        
        if get_ajax_client in app.dependency_overrides:
            del app.dependency_overrides[get_ajax_client]

@pytest.mark.asyncio
async def test_proxy_endpoint_protected(client, mock_rate_limiter):
    response = await client.get("/api/v1/ajax/some/resource")
    # APIKeyHeader returns 401 by default if header is missing in newer FastAPI
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_proxy_endpoint_success(client, mock_ajax_client, mock_rate_limiter, mock_db):
    """Test successful proxy request with unified auth."""
    mock_user = AsyncMock(spec=User)
    mock_user.id = 1
    mock_user.email = "admin@example.com"
    mock_user.subscription_status = "active"
    
    with patch("backend.app.modules.auth.service.get_user_by_email") as mock_get_user, \
         patch("backend.app.modules.auth.service.security_service") as mock_sec, \
         patch("backend.app.modules.billing.service.is_subscription_active") as mock_sub, \
         patch("backend.app.modules.billing.service.can_access_feature") as mock_feature, \
         patch("backend.app.modules.security.service.log_action") as mock_log:
        
        # 1. Setup Auth Mocks
        mock_get_user.return_value = mock_user
        mock_sub.return_value = True
        mock_feature.return_value = True
        mock_log.return_value = AsyncMock()
        mock_sec.check_ip_lockout = AsyncMock(return_value=False)
        mock_sec.reset_login_failures = AsyncMock()
        
        # 2. Get Token
        # We need mock_ajax_client to handle the login inside auth or just use a pre-existing token
        # To simplify, we'll override get_current_user for this test or just use the token flow
        auth_resp = await client.post(
            "/api/v1/auth/token", 
            json={"username": "admin@example.com", "password": "secret"}
        )
        token = auth_resp.json()["access_token"]
        
        # 3. Access Proxy
        response = await client.get(
            "/api/v1/ajax/some/resource",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"data": "mocked_response"}
        mock_ajax_client.request.assert_called_once()
