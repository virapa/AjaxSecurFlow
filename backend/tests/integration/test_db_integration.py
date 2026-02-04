import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from unittest.mock import AsyncMock, patch
import uuid
from backend.app.main import app
from backend.app.domain.models import User, AuditLog
from backend.app.core.db import async_session_factory

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
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == email)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
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
    with patch("backend.app.api.v1.auth.AjaxClient.login_with_credentials") as mock_login, \
         patch("backend.app.api.v1.auth.security_service.check_ip_lockout") as mock_lock, \
         patch("backend.app.api.v1.auth.security_service.reset_login_failures") as mock_reset:
        
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
    async with async_session_factory() as session:
        user_to_activate = await session.get(User, user_id)
        user_to_activate.subscription_status = "active"
        user_to_activate.subscription_plan = "premium"
        await session.commit()
    
    # 3. Access Proxy (this will call AjaxClient, which we MOCK to avoid external hits)
    # We patch AjaxClient.request to avoid hitting the real API in integration test
    with patch("backend.app.api.v1.proxy.AjaxClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "mocked"}
        
        proxy_resp = await client.get(
            "/api/v1/ajax/test-endpoint",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert proxy_resp.status_code == 200
    
    # 4. Verify Audit Log
    async with async_session_factory() as session:
        # User objects might be in a different session state, so we query fresh
        stmt = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.asc())
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        # We expect at least 2 logs: LOGIN_SUCCESS and PROXY_GET
        assert len(logs) >= 2
        
        # 1st: Login
        assert logs[0].action == "LOGIN_SUCCESS"
        
        # 2nd: Proxy
        assert logs[1].action == "PROXY_GET"
        assert logs[1].endpoint == "/api/v1/ajax/test-endpoint"
        # Verify enriched fields (IP and UA)
        assert logs[1].ip_address is not None
        assert logs[1].user_agent is not None
        assert logs[1].severity == "INFO"
