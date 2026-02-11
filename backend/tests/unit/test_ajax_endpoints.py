import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from backend.app.main import app
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
from backend.app.modules.ajax.schemas import ArmState

# Mock data
MOCK_HUBS = [{"id": "000000", "name": "Success Hub", "role": "MASTER"}]
MOCK_LOGS = {"logs": [{"eventId": "ev1", "hubId": "000000", "eventCode": "M_12", "eventTag": "Arm", "timestamp": 1672574400}], "total_count": 1}

@pytest.fixture
def mock_ajax_client_override():
    mock_instance = AsyncMock()
    # Default mock for hub verification (Phase 3)
    mock_instance.get_hubs = AsyncMock(return_value=MOCK_HUBS)
    app.dependency_overrides[get_ajax_client] = lambda: mock_instance
    yield mock_instance
    if get_ajax_client in app.dependency_overrides:
        del app.dependency_overrides[get_ajax_client]

@pytest.mark.asyncio
async def test_get_hubs_success(async_client: AsyncClient, mock_user_subscription, mock_ajax_client_override):
    """
    Test getting hubs with valid subscription and successful upstream response.
    """
    mock_ajax_client_override.get_hubs = AsyncMock(return_value=MOCK_HUBS)
    
    response = await async_client.get("/api/v1/ajax/hubs")
    
    assert response.status_code == 200
    mock_ajax_client_override.get_hubs.assert_called_with(user_email=mock_user_subscription.email)

@pytest.mark.asyncio
async def test_get_hubs_no_subscription(async_client: AsyncClient, mock_user_no_subscription, mock_ajax_client_override):
    """
    Test access denied when subscription is not active.
    """
    response = await async_client.get("/api/v1/ajax/hubs")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_hub_devices_success(async_client: AsyncClient, mock_user_subscription, mock_ajax_client_override):
    """
    Test getting devices for a hub.
    """
    mock_devices = [{"id": "dev1", "hubId": "000000", "deviceName": "Motion Sensor", "deviceType": "MotionProtect", "online": True}]
    mock_ajax_client_override.get_hub_devices = AsyncMock(return_value=mock_devices)
    
    response = await async_client.get("/api/v1/ajax/hubs/000000/devices")
    
    assert response.status_code == 200
    mock_ajax_client_override.get_hub_devices.assert_called_with(user_email=mock_user_subscription.email, hub_id="000000")

@pytest.mark.asyncio
async def test_get_hub_logs_success(async_client: AsyncClient, mock_user_subscription, mock_ajax_client_override):
    """
    Test getting logs for a hub.
    """
    mock_ajax_client_override.get_hub_logs = AsyncMock(return_value=MOCK_LOGS)
    
    response = await async_client.get("/api/v1/ajax/hubs/000000/logs")
    
    assert response.status_code == 200
    mock_ajax_client_override.get_hub_logs.assert_called_with(
        user_email=mock_user_subscription.email, 
        hub_id="000000", 
        limit=20, 
        offset=0
    )

@pytest.mark.asyncio
async def test_set_arm_state_success(async_client: AsyncClient, mock_user_subscription, mock_ajax_client_override):
    """
    Test setting arm state successfully.
    """
    with patch("backend.app.modules.security.service.create_audit_log") as mock_log:
        mock_ajax_client_override.set_arm_state = AsyncMock(return_value={"success": True, "message": "Command sent"})
        mock_log.return_value = AsyncMock()
        
        payload = {"armState": 1}
        response = await async_client.post("/api/v1/ajax/hubs/000000/arm", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # The actual call uses positional for all arguments
        mock_ajax_client_override.set_arm_state.assert_called_with(
            mock_user_subscription.email,
            "000000", 
            ArmState.ARMED, 
            None
        )
