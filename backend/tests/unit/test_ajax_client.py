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
    mock_redis = ajax_client.redis # This is our AsyncMock
    mock_redis.get.return_value = "cached_token"
    
    # Explicitly use AsyncMock for _get_redis
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis:
        mock_get_redis.return_value = mock_redis
        
        token = await ajax_client._get_session_token()
        assert token == "cached_token"
        mock_redis.get.assert_called_with("ajax_session_token")

@pytest.mark.asyncio
async def test_login_success(ajax_client):
    mock_redis = ajax_client.redis
    
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"session_token": "new_token", "expires_in": 3600}
    
    # For client.post, we need an AsyncMock because it is awaited
    with patch.object(ajax_client, '_get_redis', new_callable=AsyncMock) as mock_get_redis, \
         patch.object(ajax_client.client, 'post', new_callable=AsyncMock) as mock_post:
        
        mock_get_redis.return_value = mock_redis
        mock_post.return_value = mock_response
        
        token = await ajax_client.login()
        
        assert token == "new_token"
        mock_redis.set.assert_called()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "ajax_session_token"
        assert call_args[0][1] == "new_token"

@pytest.mark.asyncio
async def test_request_auto_reauth(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.return_value = "expired_token"
    
    mock_401 = MagicMock()
    mock_401.status_code = 401
    
    mock_login_resp = MagicMock()
    mock_login_resp.status_code = 200
    mock_login_resp.json.return_value = {"session_token": "refreshed_token", "expires_in": 3600}
    
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
