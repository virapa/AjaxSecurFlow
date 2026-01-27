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
        token = await ajax_client._get_session_token()
        assert token == "cached_token"

@pytest.mark.asyncio
async def test_login_success(ajax_client):
    mock_redis = ajax_client.redis
    
    # Mock HTTP response with correct camelCase keys
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
        
        token = await ajax_client.login()
        
        assert token == "new_token"
        # Verify redis calls for both token and userId
        assert mock_redis.set.call_count >= 2
        calls = [call[0][0] for call in mock_redis.set.call_args_list]
        assert "ajax_session_token" in calls
        assert "ajax_user_id" in calls

@pytest.mark.asyncio
async def test_request_uses_userId_in_path(ajax_client):
    """
    Verify that requests use the userId from redis in their paths.
    """
    mock_redis = ajax_client.redis
    # Order of calls:
    # 1. get_hubs calls _get_ajax_user_id -> redis.get("ajax_user_id")
    # 2. request calls _get_session_token -> redis.get("ajax_session_token")
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token"]
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"hubs": []}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
             
             mock_get_redis.return_value = mock_redis
             mock_request.return_value = mock_success
             
             # Call get_hubs which uses the path logic
             await ajax_client.get_hubs()
             
             # Check that the path includes the userId
             args, kwargs = mock_request.call_args
             assert "/user/ajax_user_123/hubs" in args[1]
             assert kwargs["headers"]["X-Session-Token"] == "cached_token"

@pytest.mark.asyncio
async def test_request_auto_reauth(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.return_value = "expired_token"
    
    mock_401 = MagicMock()
    mock_401.status_code = 401
    
    mock_login_resp = MagicMock()
    mock_login_resp.status_code = 200
    mock_login_resp.json.return_value = {
        "sessionToken": "refreshed_token", 
        "userId": "ajax_user_123",
        "expires_in": 3600
    }
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"data": "success"}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request, \
         patch.object(ajax_client.client, 'post', new_callable=AsyncMock) as mock_post:
             
             mock_get_redis.return_value = mock_redis
             mock_request.side_effect = [mock_401, mock_success]
             mock_post.return_value = mock_login_resp
             
             result = await ajax_client.request("GET", "/some-endpoint")
             
             assert result == {"data": "success"}
             assert mock_request.call_count == 2
             mock_post.assert_called()

@pytest.mark.asyncio
async def test_set_arm_state_command(ajax_client):
    """
    Test that set_arm_state sends the correct payload and path.
    """
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token"]
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"success": True}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
             
             mock_get_redis.return_value = mock_redis
             mock_request.return_value = mock_success
             
             # ARM the whole system (armState=1)
             await ajax_client.set_arm_state("hub_007", arm_state=1)
             
             args, kwargs = mock_request.call_args
             assert args[0] == "POST"
             assert "/user/ajax_user_123/hubs/hub_007/commands/set-arm-state" in args[1]
             assert kwargs["json"] == {"armState": 1}

@pytest.mark.asyncio
async def test_set_arm_state_with_group(ajax_client):
    """
    Test set_arm_state with a specific group ID.
    """
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token"]
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"success": True}
    
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
             
             mock_get_redis.return_value = mock_redis
             mock_request.return_value = mock_success
             
             # DISARM specific group (armState=0, group_id="g1")
             await ajax_client.set_arm_state("hub_007", arm_state=0, group_id="g1")
             
             _, kwargs = mock_request.call_args
             assert kwargs["json"] == {"armState": 0, "groupId": "g1"}
