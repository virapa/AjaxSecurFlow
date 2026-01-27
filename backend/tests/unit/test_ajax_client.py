import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from pydantic import SecretStr
from backend.app.services.ajax_client import AjaxClient, AjaxAuthError

# Mock settings
@pytest.fixture(autouse=True)
def mock_settings():
    with patch("backend.app.services.ajax_client.settings") as mock_settings:
        mock_settings.AJAX_API_BASE_URL = "https://mock.api"
        mock_settings.AJAX_LOGIN = "test_user"
        mock_settings.AJAX_PASSWORD = SecretStr("secret_pass")
        mock_settings.AJAX_API_KEY = SecretStr("secret_key")
        mock_settings.REDIS_URL = "redis://mock:6379/0"
        yield mock_settings

@pytest.fixture
def ajax_client():
    # Reset singleton for testing
    AjaxClient._instance = None
    client = AjaxClient()
    # Mock redis inside the client to avoid real connection attempt
    client.redis = AsyncMock() 
    return client

@pytest.mark.asyncio
async def test_get_session_token_from_redis(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.return_value = "cached_token"
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis:
        mock_get_redis.return_value = mock_redis
        # Now requires user_email
        token = await ajax_client._get_session_token("user@example.com")
        assert token == "cached_token"
        mock_redis.get.assert_called_with("ajax_user:user@example.com:token")

@pytest.mark.asyncio
async def test_login_success(ajax_client):
    mock_redis = ajax_client.redis
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sessionToken": "new_token", 
        "userId": "ajax_user_123",
        "expires_in": 3600
    }
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'post', new_callable=AsyncMock) as mock_post:
        
        mock_get_redis.return_value = mock_redis
        mock_post.return_value = mock_response
        
        # New login method
        data = await ajax_client.login_with_credentials("user@example.com", "pass123")
        
        assert data["sessionToken"] == "new_token"
        # Verify redis keys are namespaced
        assert mock_redis.set.call_count >= 2
        calls = [call[0][0] for call in mock_redis.set.call_args_list]
        assert "ajax_user:user@example.com:token" in calls
        assert "ajax_user:user@example.com:id" in calls

@pytest.mark.asyncio
async def test_request_uses_userId_in_path(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token"]
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"hubs": []}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
             
             mock_get_redis.return_value = mock_redis
             mock_request.return_value = mock_success
             
             await ajax_client.get_hubs("user@example.com")
             
             args, kwargs = mock_request.call_args
             assert "/user/ajax_user_123/hubs" in args[1]
             assert kwargs["headers"]["X-Session-Token"] == "cached_token"

@pytest.mark.asyncio
async def test_set_arm_state_command(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token"]
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"success": True}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
             
             mock_get_redis.return_value = mock_redis
             mock_request.return_value = mock_success
             
             await ajax_client.set_arm_state("user@example.com", "hub_007", arm_state=1)
             
             args, kwargs = mock_request.call_args
             assert args[0] == "POST"
             assert "/user/ajax_user_123/hubs/hub_007/commands/set-arm-state" in args[1]
             assert kwargs["json"] == {"armState": 1}

@pytest.mark.asyncio
async def test_refresh_session_success(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["old_refresh", "ajax_user_123"]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sessionToken": "refreshed_access", 
        "refreshToken": "refreshed_refresh",
        "expires_in": 900
    }
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'post', new_callable=AsyncMock) as mock_post:
        
        mock_get_redis.return_value = mock_redis
        mock_post.return_value = mock_response
        
        new_token = await ajax_client.refresh_session("user@example.com")
        
        assert new_token == "refreshed_access"
        # Check params sent to /refresh
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["userId"] == "ajax_user_123"
        assert kwargs["json"]["refreshToken"] == "old_refresh"
        
        # Verify redis update
        assert mock_redis.set.call_count >= 2

@pytest.mark.asyncio
async def test_request_auto_refresh_on_401(ajax_client):
    mock_redis = ajax_client.redis
    # _get_session_token (initial), _get_ajax_user_id (ensuring userId), then refresh_session (get refresh, get user id)
    # The current request() code:
    # 1. token = _get_session_token -> "expired_token"
    # 2. _do_req("expired_token") -> 401
    # 3. refresh_session("user@example.com") 
    #    - _get_refresh_token -> "refresh_val"
    #    - _get_ajax_user_id -> "user_val"
    # 4. _do_req("new_token") -> 200
    
    mock_redis.get.side_effect = ["expired_token", "refresh_val", "user_val"]
    
    mock_401 = MagicMock()
    mock_401.status_code = 401
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"data": "ok"}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request, \
         patch.object(ajax_client, 'refresh_session', new_callable=AsyncMock) as mock_refresh:
        
        mock_get_redis.return_value = mock_redis
        mock_request.side_effect = [mock_401, mock_200]
        mock_refresh.return_value = "new_token"
        
        resp = await ajax_client.request("user@example.com", "GET", "/some-data")
        
        assert resp == {"data": "ok"}
        assert mock_request.call_count == 2
        assert mock_refresh.called
