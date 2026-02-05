import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.services.audit_service import log_request_action, log_action

@pytest.mark.asyncio
async def test_log_action_basic():
    mock_db = AsyncMock()
    with patch("backend.app.services.audit_service.crud_audit.create_audit_log", new_callable=AsyncMock) as mock_create:
        await log_action(
            db=mock_db,
            user_id=1,
            action="TEST_ACTION",
            endpoint="/test",
            status_code=200,
            severity="DEBUG"
        )
        
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        assert kwargs["action"] == "TEST_ACTION"
        assert kwargs["severity"] == "DEBUG"

@pytest.mark.asyncio
async def test_log_request_action_with_x_forwarded_for():
    mock_db = AsyncMock()
    mock_request = MagicMock()
    mock_request.headers = {
        "x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178",
        "user-agent": "Mozilla/5.0"
    }
    mock_request.url.path = "/api/v1/resource"
    mock_request.method = "POST"
    
    with patch("backend.app.services.audit_service.log_action", new_callable=AsyncMock) as mock_log:
        await log_request_action(
            db=mock_db,
            request=mock_request,
            user_id=42,
            action="CREATE_RESOURCE",
            status_code=201
        )
        
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        # Should pick the FIRST IP in the list
        assert kwargs["ip_address"] == "203.0.113.195"
        assert kwargs["user_agent"] == "Mozilla/5.0"
        assert kwargs["endpoint"] == "/api/v1/resource"

@pytest.mark.asyncio
async def test_log_request_action_with_x_real_ip():
    mock_db = AsyncMock()
    mock_request = MagicMock()
    mock_request.headers = {
        "x-real-ip": "1.2.3.4"
    }
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.url.path = "/test"
    mock_request.method = "GET"
    
    with patch("backend.app.services.audit_service.log_action", new_callable=AsyncMock) as mock_log:
        await log_request_action(
            db=mock_db,
            request=mock_request,
            user_id=None,
            action="VIEW",
            status_code=200
        )
        
        assert mock_log.call_args[1]["ip_address"] == "1.2.3.4"
