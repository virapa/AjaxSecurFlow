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
    # Health check is not under /api/v1, so it shouldn't have the header based on current implementation
    assert "X-Correlation-ID" not in response.headers

    response = await async_client.get("/api/v1/auth/token") # Even if it fails auth/method, middleware should run
    assert "X-Correlation-ID" in response.headers

@pytest.mark.asyncio
async def test_audit_middleware_logs_to_db(async_client: AsyncClient):
    """
    Test that the middleware actually calls the audit service.
    """
    with patch("backend.app.crud.audit.create_audit_log", new_callable=AsyncMock) as mock_log:
        response = await async_client.get("/api/v1/users/me") # Protected route, will 401 but middleware logs it
        
        assert response.status_code == 401
        assert "X-Correlation-ID" in response.headers
        
        # Verify call
        mock_log.assert_called_once()
        _, kwargs = mock_log.call_args
        assert kwargs["action"].startswith("AUTO_AUDIT_")
        assert "latency_ms" in kwargs
        assert "correlation_id" in kwargs
        assert kwargs["correlation_id"] == response.headers["X-Correlation-ID"]
