import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from pydantic import SecretStr
from backend.app.modules.ajax.service import AjaxClient, AjaxAuthError

# Mock settings
@pytest.fixture(autouse=True)
def mock_settings():
    with patch("backend.app.modules.ajax.service.settings") as mock_settings:
        mock_settings.AJAX_API_BASE_URL = "https://mock.api"
        mock_settings.AJAX_LOGIN = "test_user"
        mock_settings.AJAX_PASSWORD = SecretStr("secret_pass")
        mock_settings.AJAX_API_KEY = SecretStr("secret_key")
        mock_settings.REDIS_URL = "redis://mock:6379/0"
        mock_settings.CACHE_TTL_HUBS = 300
        mock_settings.CACHE_TTL_HUB_DETAIL = 300
        mock_settings.CACHE_TTL_DEVICES = 300
        yield mock_settings

@pytest.fixture
def ajax_client():
    client = AjaxClient()
    # Mock redis inside the client to avoid real connection attempt
    client.redis = AsyncMock()
    
    # Mock cache to always "miss" so existing tests logic remains valid
    # and doesn't consume redis mock side_effects unexpectedly
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.invalidate = AsyncMock(return_value=True)
    
    # Mock get_or_fetch to bypass cache and call the fetch function directly
    async def mock_get_or_fetch(key, ttl, fetch_func):
        return await fetch_func()
    mock_cache.get_or_fetch = AsyncMock(side_effect=mock_get_or_fetch)
    
    # Helper methods for keys
    mock_cache.key_hubs = MagicMock(return_value="cache:hubs")
    mock_cache.key_hub = MagicMock(return_value="cache:hub")
    mock_cache.key_devices = MagicMock(return_value="cache:devices")
    mock_cache.key_device = MagicMock(return_value="cache:device")
    mock_cache.key_rooms = MagicMock(return_value="cache:rooms")
    mock_cache.key_groups = MagicMock(return_value="cache:groups")
    
    # Patch _get_cache to return our mock_cache
    with patch.object(client, '_get_cache', return_value=mock_cache):
        yield client

@pytest.mark.asyncio
async def test_get_hubs_enriched_parallel(ajax_client):
    """Test that get_hubs calls _fetch_hub_details_uncached for each hub."""
    mock_redis = ajax_client.redis
    mock_redis.get.return_value = "ajax_user_123" # For _get_ajax_user_id
    
    # Mock the request for get_hubs (the list)
    hubs_list = [{"hubId": "hub1"}, {"hubId": "hub2"}]
    
    with patch.object(ajax_client, 'request', new_callable=AsyncMock) as mock_request, \
         patch.object(ajax_client, '_fetch_hub_details_uncached', new_callable=AsyncMock) as mock_details:
        
        mock_request.return_value = hubs_list
        mock_details.side_effect = [
            {"hubId": "hub1", "state": "ARMED"},
            {"hubId": "hub2", "state": "DISARMED"}
        ]
        
        enriched = await ajax_client.get_hubs("user@example.com")
        
        assert len(enriched) == 2
        assert enriched[0]["hubId"] == "hub1"
        assert enriched[1]["hubId"] == "hub2"
        assert mock_details.call_count == 2

@pytest.mark.asyncio
async def test_get_hub_devices_flattening(ajax_client):
    """Test that properties are correctly flattened in get_hub_devices."""
    mock_redis = ajax_client.redis
    mock_redis.get.return_value = "ajax_user_123"
    
    ajax_response = [
        {
            "deviceId": "dev1",
            "properties": {
                "deviceName": "Front Door",
                "online": True
            }
        },
        {
            "id": "dev2",
            "properties": {
                "deviceName": "Motion"
            }
        }
    ]
    
    with patch.object(ajax_client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = ajax_response
        
        devices = await ajax_client.get_hub_devices("user@example.com", "hub123")
        
        assert len(devices) == 2
        assert devices[0]["deviceId"] == "dev1"
        assert devices[0]["deviceName"] == "Front Door"
        assert devices[1]["deviceId"] == "dev2"
        assert devices[1]["deviceName"] == "Motion"

@pytest.mark.asyncio
async def test_get_session_token_from_redis(ajax_client):
    mock_local_redis = AsyncMock()
    ajax_client.redis = mock_local_redis
    mock_local_redis.get.return_value = "cached_token"
    
    token = await ajax_client._get_session_token("user@example.com")
    assert token == "cached_token"
    mock_local_redis.get.assert_called_with("ajax_user:user@example.com:token")

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
    
    with patch.object(ajax_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        data = await ajax_client.login_with_credentials("user@example.com", "pass123")
        
        assert data["sessionToken"] == "new_token"
        assert mock_redis.set.call_count >= 2

@pytest.mark.asyncio
async def test_request_uses_userId_in_path(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token", "0"] 
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"hubs": []}
    
    with patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_success
        
        await ajax_client.get_hubs("user@example.com")
        
        args, kwargs = mock_request.call_args
        assert "user/ajax_user_123/hubs" in args[1]
        assert kwargs["headers"]["X-Session-Token"] == "cached_token"

@pytest.mark.asyncio
async def test_set_arm_state_command(ajax_client):
    mock_redis = ajax_client.redis
    mock_redis.get.side_effect = ["ajax_user_123", "cached_token"]
    
    mock_success = MagicMock()
    mock_success.status_code = 204
    
    with patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_success
        
        await ajax_client.set_arm_state("user@example.com", "hub_007", arm_state=1)
        
        args, kwargs = mock_request.call_args
        assert args[0] == "PUT"
        assert "user/ajax_user_123/hubs/hub_007/commands/arming" in args[1]
        assert kwargs["json"] == {"command": "ARM", "ignoreProblems": True}

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
    
    with patch.object(ajax_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        new_token = await ajax_client.refresh_session("user@example.com")
        
        assert new_token == "refreshed_access"
        assert mock_redis.set.call_count >= 2

@pytest.mark.asyncio
async def test_request_auto_refresh_on_401(ajax_client):
    # Setup mocks
    mock_401 = MagicMock()
    mock_401.status_code = 401
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"data": "ok"}
    
    with patch.object(ajax_client.client, 'request', new_callable=AsyncMock) as mock_request, \
         patch.object(ajax_client, 'refresh_session', new_callable=AsyncMock) as mock_refresh:
        
        mock_request.side_effect = [mock_401, mock_200]
        mock_refresh.return_value = "new_token"
        
        # We need to mock _get_session_token to return something initially
        with patch.object(ajax_client, '_get_session_token', new_callable=AsyncMock) as mock_token:
            mock_token.side_effect = ["expired_token", "new_token"]
            
            resp = await ajax_client.request("user@example.com", "GET", "/some-data")
            
            assert resp == {"data": "ok"}
            assert mock_request.call_count == 2
            assert mock_refresh.called
