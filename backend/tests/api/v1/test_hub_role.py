import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.app.services.ajax_client import AjaxClient

# Pure Unit Test - No app/db imports to avoid Side Effects

@pytest.mark.asyncio
async def test_get_user_hub_binding_success():
    """
    Test AjaxClient.get_user_hub_binding logic in isolation.
    """
    # Mock Redis
    mock_redis = MagicMock()
    
    # Instantiate Client
    client = AjaxClient(redis_client=mock_redis)
    
    # Mock internal request method 
    client.request = AsyncMock(return_value={
        "hubId": "0004C602",
        "hubBindingRole": "PRO"
    })
    
    result = await client.get_user_hub_binding("test@email.com", "user123", "0004C602")
    
    assert result is not None
    assert result["hubId"] == "0004C602"
    assert result["hubBindingRole"] == "PRO"
    
    # Verify arguments passed to request
    client.request.assert_called_with(
        "test@email.com",
        "GET",
        "/user/user123/hubs/0004C602/users/user123"
    )

@pytest.mark.asyncio
async def test_get_user_hub_binding_not_found():
    """
    Test AjaxClient.get_user_hub_binding when hub is not found (404).
    """
    import httpx
    
    mock_redis = MagicMock()
    client = AjaxClient(redis_client=mock_redis)
    
    # Mock request to raise 404
    error_response = httpx.Response(404)
    client.request = AsyncMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=error_response))
    
    result = await client.get_user_hub_binding("test@email.com", "user123", "0004C602")
    
    assert result is None
