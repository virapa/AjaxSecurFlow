import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from backend.app.modules.auth.models import User

PROBE = "/api/v1/security/audit-logs"


def _user():
    return User(id=1, email="ha@example.com", hashed_password="x", is_active=True,
                subscription_plan="pro", subscription_status="active")


@pytest.mark.asyncio
async def test_valid_api_token_authenticates(async_client: AsyncClient):
    with patch("backend.app.modules.auth.service.api_token_service.authenticate_api_token",
               AsyncMock(return_value=_user())):
        response = await async_client.get(PROBE, headers={"Authorization": "Bearer asf_valid"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_token_ignores_user_agent_binding(async_client: AsyncClient):
    with patch("backend.app.modules.auth.service.api_token_service.authenticate_api_token",
               AsyncMock(return_value=_user())):
        r1 = await async_client.get(PROBE, headers={"Authorization": "Bearer asf_valid", "User-Agent": "ha/1"})
        r2 = await async_client.get(PROBE, headers={"Authorization": "Bearer asf_valid", "User-Agent": "ha/2"})
    assert r1.status_code == 200
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_invalid_api_token_401_and_audited(async_client: AsyncClient, mock_db):
    with patch("backend.app.modules.auth.service.api_token_service.authenticate_api_token",
               AsyncMock(return_value=None)), \
         patch("backend.app.modules.auth.service.security_service.log_request_action", AsyncMock()) as audit:
        response = await async_client.get(PROBE, headers={"Authorization": "Bearer asf_revoked"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    assert audit.await_args.kwargs["action"] == "API_TOKEN_INVALID"


@pytest.mark.asyncio
async def test_jwt_path_untouched_for_non_prefixed_tokens(async_client: AsyncClient):
    with patch("backend.app.modules.auth.service.api_token_service.authenticate_api_token", AsyncMock()) as m:
        response = await async_client.get(PROBE, headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
    m.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_api_token_audit_is_throttled(async_client: AsyncClient, mock_db, mock_redis):
    # Redis NX key already exists for this IP -> audit write must be skipped
    mock_redis.set.return_value = None
    with patch("backend.app.modules.auth.service.api_token_service.authenticate_api_token",
               AsyncMock(return_value=None)), \
         patch("backend.app.modules.auth.service.security_service.log_request_action", AsyncMock()) as audit:
        response = await async_client.get(PROBE, headers={"Authorization": "Bearer asf_revoked"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    audit.assert_not_awaited()
