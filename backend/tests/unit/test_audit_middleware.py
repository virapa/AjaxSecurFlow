import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.app.main import app

@pytest.mark.asyncio
async def test_audit_middleware_adds_header(async_client: AsyncClient):
    """
    Test that the audit middleware adds the X-Correlation-ID header to responses.
    """
    response = await async_client.get("/health")
    # Health check should now have headers as they are added by default
    assert "X-Correlation-ID" in response.headers
    assert "X-Request-Latency-ms" in response.headers

    response = await async_client.get("/api/v1/auth/token")
    assert "X-Correlation-ID" in response.headers

@pytest.mark.asyncio
async def test_audit_middleware_logs_to_db(async_client: AsyncClient):
    """
    Test that the middleware calls the audit service for mutations.
    """
    # Patch the function where it is IMPORTED in main.py
    with patch("backend.app.modules.security.service.log_request_action", new_callable=AsyncMock) as mock_log:
        # Use POST to trigger mutation auditing
        response = await async_client.post("/api/v1/auth/token", json={"username": "test", "password": "pwd"})
        
        # Note: /auth/token POST is audited by middleware
        assert "X-Correlation-ID" in response.headers
        
        # Note: /auth/token POST is audited by BOTH the handler and the middleware
        assert response.status_code == 401
        assert "X-Correlation-ID" in response.headers
        
        assert mock_log.call_count == 2
        # Verify first call (handler) or second call (middleware)
        # We just need to know it captured the action
        calls = [call[1]["action"] for call in mock_log.call_args_list]
        assert any("LOGIN_FAILED" in a for a in calls)
        assert any("Mutation: /api/v1/auth/token" in a for a in calls)
