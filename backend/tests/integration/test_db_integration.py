import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from unittest.mock import AsyncMock, patch
import uuid
from backend.app.main import app
from backend.app.modules.auth.models import User
from backend.app.modules.security.models import AuditLog
from backend.app.shared.infrastructure.database import session as db_session

@pytest.mark.asyncio
async def test_full_flow_integration(client):
    """
    Full integration flow:
    1. Register new user
    2. Login with new user
    3. Use Proxy
    4. Verify Audit Log entry in DB
    """
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "REDACTED_RANDOM_PWD_PLACEHOLDER"
    
    # Clean up previous runs if any
    async with db_session.async_session_factory() as session:
        stmt = select(User).where(User.email == email)
        res = await session.execute(stmt)
        # Handle both real SQLA and AsyncMock
        existing = res.scalar_one_or_none()
        if hasattr(existing, "__await__"):
            existing = await existing
        if existing:
            await session.execute(delete(AuditLog).where(AuditLog.user_id == existing.id))
            await session.delete(existing)
            await session.commit()

    # 1. Register
    response = await client.post(
        "/api/v1/users/",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Register failed: {response.text}"
    user_id = response.json()["id"]
    
    # 2. Login (Mocking Ajax and Security Service)
    # Using the correct path for AjaxClient and security_service
    with patch("backend.app.modules.ajax.service.AjaxClient.login_with_credentials", new_callable=AsyncMock) as mock_login, \
         patch("backend.app.modules.security.service.check_ip_lockout", new_callable=AsyncMock) as mock_lock, \
         patch("backend.app.modules.security.service.reset_login_failures", new_callable=AsyncMock) as mock_reset:
        
        mock_login.return_value = {"userId": "123", "sessionToken": "test_token"}
        mock_lock.return_value = False
        mock_reset.return_value = None
        
        login_response = await client.post(
            "/api/v1/auth/token",
            json={"username": email, "password": password}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]
    
    # ACTIVATE SUBSCRIPTION (Simulate Payment)
    async with db_session.async_session_factory() as session:
        user_to_activate = await session.get(User, user_id)
        user_to_activate.subscription_status = "active"
        user_to_activate.subscription_plan = "premium"
        await session.commit()
    
    # 3. Access Proxy (this will call AjaxClient, which we MOCK to avoid external hits)
    # We use a POST here so that it triggers auditing as a mutation
    with patch("backend.app.modules.ajax.service.AjaxClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "mocked"}
        
        proxy_resp = await client.post(
            "/api/v1/ajax/test-endpoint",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert proxy_resp.status_code == 200
    
    # 4. Verify Audit Log
    async with db_session.async_session_factory() as session:
        # User objects might be in a different session state, so we query fresh
        stmt = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.asc())
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        # We expect at least 3 logs from the sequence:
        # 1. Mutation (Register /api/v1/users/) - from middleware
        # 2. LOGIN_SUCCESS - from auth router manual log
        # 3. Mutation (/api/v1/auth/token) - from middleware
        # 4. Mutation (/api/v1/ajax/test-endpoint) - from middleware (intercepted by proxy)
        assert len(logs) >= 3
        
        actions = [l.action for l in logs]
        # Verify essential events occurred
        assert any("/users/" in a for a in actions)
        assert "LOGIN_SUCCESS" in actions
        assert any("/ajax/test-endpoint" in a for a in actions)
        
        # Verify the most recent log (Proxy Mutation)
        proxy_log = logs[-1]
        assert "/ajax/test-endpoint" in proxy_log.action
        assert proxy_log.ip_address is not None
        assert proxy_log.user_agent is not None
        assert proxy_log.severity == "INFO"
