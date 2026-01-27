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
