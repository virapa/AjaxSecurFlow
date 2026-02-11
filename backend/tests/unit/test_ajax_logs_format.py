import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.main import app
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
from backend.app.modules.auth.service import get_current_user
from backend.app.modules.ajax import schemas as schemas

@pytest.fixture
def mock_ajax_logs_overrides():
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.subscription_status = "active"
    mock_user.subscription_plan = "premium"
    mock_user.subscription_expires_at = None

    mock_ajax = AsyncMock()
    # Raw mock data from Ajax API (camelCase)
    mock_ajax.get_hub_logs.return_value = {
        "logs": [
            {
                "eventId": "event_123",
                "hubId": "hub_456",
                "timestamp": 1700000000000,
                "eventType": "SECURITY",
                "eventTag": "Motion",
                "sourceObjectType": "DEVICE",
                "sourceObjectName": "Living Room Cam"
            },
            {
                "eventId": "event_789",
                "hubId": "hub_456",
                "timestamp": 1700000060000,
                "eventType": "SECURITY",
                "eventTag": "Arm",
                "sourceObjectType": "USER",
                "sourceObjectName": "John Doe"
            }
        ],
        "total_count": 2
    }
    # Necessary for verify_hub_access
    mock_ajax.get_hubs.return_value = {"hubs": [{"id": "hub_456"}]}

    # Mock DB to prevent real DB access or leaky state
    from backend.app.shared.infrastructure.database.session import get_db
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_ajax_client] = lambda: mock_ajax
    app.dependency_overrides[get_db] = lambda: mock_db
    
    yield mock_ajax, mock_user, mock_db
    
    for dep in [get_current_user, get_ajax_client, get_db]:
        if dep in app.dependency_overrides:
            del app.dependency_overrides[dep]

def test_read_hub_logs_format(mock_ajax_logs_overrides):
    """Verify that hub logs return the correct wrapped format and aliases."""
    
    mock_ajax, mock_user, _ = mock_ajax_logs_overrides

    with TestClient(app) as client:
        response = client.get("/api/v1/ajax/hubs/hub_456/logs")
        
    assert response.status_code == 200
    data = response.json()
    
    # Check wrapper
    assert "logs" in data
    assert "total_count" in data
    assert data["total_count"] == 2
    
    # Check field aliases and mapping
    logs = data["logs"]
    assert logs[0]["id"] == "event_123"
    assert logs[0]["hub_id"] == "hub_456"
    assert logs[0]["event_desc"] == "Movimiento Detectado" # Mapped from 'Motion' or eventType
    assert logs[0]["device_name"] == "Living Room Cam"
    
    assert logs[1]["id"] == "event_789"
    assert logs[1]["event_desc"] == "Sistema Armado" # Mapped from 'Arm'
