import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.app.main import app
from backend.app.modules.auth.service import get_current_user

@pytest.mark.asyncio
async def test_read_user_me_dynamic_plan():
    class MockUser:
        id = 1
        email = "test@example.com"
        subscription_plan = "premium"
        subscription_status = "expired"
        subscription_expires_at = None
        is_active = True
        is_superuser = False
    
    mock_user = MockUser()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock AjaxClient to avoid network calls
    mock_ajax = AsyncMock()
    mock_ajax.get_user_info.return_value = {"ajax_id": "123"}
    from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
    app.dependency_overrides[get_ajax_client] = lambda: mock_ajax

    from httpx import ASGITransport
    import traceback
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/users/me")
    except Exception:
        traceback.print_exc()
        raise
    
    assert response.status_code == 200
    data = response.json()
    print(f"\nDEBUG DATA: {data}")
    
    # New logic: subscription_plan is raw DB value, 
    # subscription_active is the calculated dynamic entitlement
    assert data["subscription_plan"] == "premium" 
    assert data["subscription_active"] is False
    assert data["billing_status"] == "expired"
    assert "effective_plan" not in data
    assert "is_active_premium" not in data
    
    app.dependency_overrides = {}
