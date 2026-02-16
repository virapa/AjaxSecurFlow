import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.app.main import app
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client

@pytest.mark.asyncio
async def test_freemium_access_matrix(async_client: AsyncClient, mock_user_no_subscription):
    """
    INTEGRATION TEST: Verifies the full access matrix for a FREE user.
    A Free user should have access to:
    - /hubs (List)
    - /hubs/{id} (Detail)
    - /hubs/{id}/devices (List)
    - /hubs/{id}/rooms (List)
    - /hubs/{id}/groups (List)
    
    But NOT to:
    - /hubs/{id}/logs (403)
    - /hubs/{id}/arm-state (403)
    """
    mock_ajax = AsyncMock()
    app.dependency_overrides[get_ajax_client] = lambda: mock_ajax
    
    hub_id = "000000"
    
    # 1. ALLOWED: List Hubs
    mock_ajax.get_hubs.return_value = [{"id": hub_id, "name": "Free Hub"}]
    resp = await async_client.get("/api/v1/ajax/hubs")
    assert resp.status_code == 200, "Free user SHOULD access hub list"
    
    # 2. FORBIDDEN: Hub Devices
    mock_ajax.get_hub_devices.return_value = []
    resp = await async_client.get(f"/api/v1/ajax/hubs/{hub_id}/devices")
    assert resp.status_code == 403, "Free user should NOT access devices"
    assert "Device access not included in your plan" in resp.json()["detail"]
    
    # 3. FORBIDDEN: Hub Rooms
    mock_ajax.get_hub_rooms.return_value = []
    resp = await async_client.get(f"/api/v1/ajax/hubs/{hub_id}/rooms")
    assert resp.status_code == 403, "Free user should NOT access rooms"
    assert "Room access not included in your plan" in resp.json()["detail"]
    
    # 4. FORBIDDEN: Hub Groups
    mock_ajax.get_hub_groups.return_value = []
    resp = await async_client.get(f"/api/v1/ajax/hubs/{hub_id}/groups")
    assert resp.status_code == 403, "Free user should NOT access groups"
    assert "Group access not included in your plan" in resp.json()["detail"]
    
    # 4. FORBIDDEN: Hub Logs
    resp = await async_client.get(f"/api/v1/ajax/hubs/{hub_id}/logs")
    assert resp.status_code == 403, "Free user should NOT access logs"
    assert "Logs access not included in your plan" in resp.json()["detail"]
    
    # 5. FORBIDDEN: Arm State
    payload = {"arm_state": 1}
    resp = await async_client.post(f"/api/v1/ajax/hubs/{hub_id}/arm-state", json=payload)
    assert resp.status_code == 403, "Free user should NOT access arming"
    assert "Command execution not included in your plan" in resp.json()["detail"]

    # Cleanup
    del app.dependency_overrides[get_ajax_client]

@pytest.mark.asyncio
async def test_premium_proxy_access(async_client: AsyncClient, mock_user_subscription):
    """
    INTEGRATION TEST: Verifies that Premium users can access the catch-all proxy.
    """
    mock_ajax = AsyncMock()
    app.dependency_overrides[get_ajax_client] = lambda: mock_ajax
    
    # Premium user should be able to call random endpoints via proxy
    mock_ajax.request.return_value = {"proxied": True}
    resp = await async_client.get("/api/v1/ajax/some/random/endpoint")
    
    assert resp.status_code == 200
    assert resp.json() == {"proxied": True}
    
    # Cleanup
    del app.dependency_overrides[get_ajax_client]
