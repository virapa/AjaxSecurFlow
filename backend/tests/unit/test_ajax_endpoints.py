import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

# Mock data
MOCK_HUBS = [{"id": "000000", "name": "Success Hub", "role": "MASTER"}]
MOCK_LOGS = {"logs": [{"id": "ev1", "hub_id": "000000", "event_code": "M_12", "timestamp": "2023-01-01T12:00:00Z"}], "total_count": 1}

@pytest.mark.asyncio
async def test_get_hubs_success(async_client: AsyncClient, mock_user_subscription):
    """
    Test getting hubs with valid subscription and successful upstream response.
    """
    with patch("backend.app.api.v1.endpoints.ajax.AjaxClient") as MockClient:
        # Configure Mock
        instance = MockClient.return_value
        instance.get_hubs = AsyncMock(return_value=MOCK_HUBS)
        
        response = await async_client.get("/api/v1/ajax/hubs")
        
        assert response.status_code == 200
        instance.get_hubs.assert_called_with(user_email=mock_user_subscription.email)

@pytest.mark.asyncio
async def test_get_hubs_no_subscription(async_client: AsyncClient, mock_user_no_subscription):
    """
    Test access denied when subscription is not active.
    """
    response = await async_client.get("/api/v1/ajax/hubs")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_hub_devices_success(async_client: AsyncClient, mock_user_subscription):
    """
    Test getting devices for a hub.
    """
    mock_devices = [{"id": "dev1", "hubId": "000000", "deviceName": "Motion Sensor", "deviceType": "MotionProtect", "online": True}]
    with patch("backend.app.api.v1.endpoints.ajax.AjaxClient") as MockClient:
        instance = MockClient.return_value
        instance.get_hub_devices = AsyncMock(return_value=mock_devices)
        
        response = await async_client.get("/api/v1/ajax/hubs/000000/devices")
        
        assert response.status_code == 200
        instance.get_hub_devices.assert_called_with(user_email=mock_user_subscription.email, hub_id="000000")

@pytest.mark.asyncio
async def test_get_hub_logs_success(async_client: AsyncClient, mock_user_subscription):
    """
    Test getting logs for a hub.
    """
    with patch("backend.app.api.v1.endpoints.ajax.AjaxClient") as MockClient:
        instance = MockClient.return_value
        instance.get_hub_logs = AsyncMock(return_value=MOCK_LOGS)
        
        response = await async_client.get("/api/v1/ajax/hubs/000000/logs")
        
        assert response.status_code == 200
        instance.get_hub_logs.assert_called_with(
            user_email=mock_user_subscription.email, 
            hub_id="000000", 
            limit=100, 
            offset=0
        )

@pytest.mark.asyncio
async def test_set_arm_state_success(async_client: AsyncClient, mock_user_subscription):
    """
    Test setting arm state successfully.
    """
    with patch("backend.app.api.v1.endpoints.ajax.AjaxClient") as MockClient:
        instance = MockClient.return_value
        instance.set_arm_state = AsyncMock(return_value={"success": True, "message": "Command sent"})
        
        payload = {"armState": 1}
        response = await async_client.post("/api/v1/ajax/hubs/000000/arm-state", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Updated assertion to expect user_email
        instance.set_arm_state.assert_called_with(
            user_email=mock_user_subscription.email,
            hub_id="000000", 
            arm_state=1, 
            group_id=None
        )
