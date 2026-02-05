import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.deps import get_ajax_client
from backend.app.api.v1.auth import get_current_user
from backend.app.schemas import ajax as schemas

def test_read_hub_logs_format():
    """Verify that hub logs return the correct wrapped format and aliases."""
    
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.subscription_status = "active"
    mock_user.subscription_plan = "premium"
    mock_user.subscription_expires_at = None

    mock_ajax = AsyncMock()
    # Raw mock data from Ajax API (camelCase)
    mock_ajax.get_hub_logs.return_value = [
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
    ]
    # Necessary for verify_hub_access
    mock_ajax.get_hubs.return_value = {"hubs": [{"id": "hub_456"}]}

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_ajax_client] = lambda: mock_ajax

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
    assert logs[1]["event_desc"] == "Sistema Armado" # Mapped from 'Arm' (not implemented yet in mock, let's fix mock)

    app.dependency_overrides = {}
