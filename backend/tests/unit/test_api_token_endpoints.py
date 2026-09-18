import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from backend.app.modules.auth.models import ApiToken, User
from backend.app.modules.auth.api_token_service import TokenLimitExceeded


def _token(id=1, user_id=1):
    return ApiToken(
        id=id, user_id=user_id, name="Home Assistant", token_hash="h",
        prefix="asf_abcdefgh", created_at=datetime(2026, 9, 18, tzinfo=timezone.utc)
    )


@pytest.mark.asyncio
async def test_create_token_returns_raw_once(async_client: AsyncClient, mock_user_subscription):
    with patch("backend.app.modules.auth.api_token_service.create_api_token",
               AsyncMock(return_value=(_token(), "asf_abcdefghRAWRAW"))):
        response = await async_client.post("/api/v1/auth/api-tokens", json={"name": "Home Assistant"})
    assert response.status_code == 201
    body = response.json()
    assert body["token"] == "asf_abcdefghRAWRAW"
    assert body["prefix"] == "asf_abcdefgh"
    assert body["name"] == "Home Assistant"


@pytest.mark.asyncio
async def test_create_token_forbidden_for_free_plan(async_client: AsyncClient, mock_user_no_subscription):
    response = await async_client.post("/api/v1/auth/api-tokens", json={"name": "HA"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_token_limit_returns_400(async_client: AsyncClient, mock_user_subscription):
    with patch("backend.app.modules.auth.api_token_service.create_api_token",
               AsyncMock(side_effect=TokenLimitExceeded())):
        response = await async_client.post("/api/v1/auth/api-tokens", json={"name": "HA"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_token_validates_name(async_client: AsyncClient, mock_user_subscription):
    response = await async_client.post("/api/v1/auth/api-tokens", json={"name": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tokens_never_exposes_raw(async_client: AsyncClient, mock_user_subscription):
    with patch("backend.app.modules.auth.api_token_service.list_api_tokens",
               AsyncMock(return_value=[_token(1), _token(2)])):
        response = await async_client.get("/api/v1/auth/api-tokens")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert "token" not in body[0]
    assert body[0]["prefix"] == "asf_abcdefgh"


@pytest.mark.asyncio
async def test_revoke_token_204(async_client: AsyncClient, mock_user_subscription):
    with patch("backend.app.modules.auth.api_token_service.revoke_api_token", AsyncMock(return_value=True)) as m:
        response = await async_client.delete("/api/v1/auth/api-tokens/7")
    assert response.status_code == 204
    m.assert_awaited_once()
    assert m.await_args.kwargs["token_id"] == 7
    assert m.await_args.kwargs["user_id"] == mock_user_subscription.id


@pytest.mark.asyncio
async def test_revoke_unknown_token_404(async_client: AsyncClient, mock_user_subscription):
    with patch("backend.app.modules.auth.api_token_service.revoke_api_token", AsyncMock(return_value=False)):
        response = await async_client.delete("/api/v1/auth/api-tokens/99")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_token_rejects_whitespace_name(async_client: AsyncClient, mock_user_subscription):
    response = await async_client.post("/api/v1/auth/api-tokens", json={"name": "   "})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tokens_forbidden_for_free_plan(async_client: AsyncClient, mock_user_no_subscription):
    response = await async_client.get("/api/v1/auth/api-tokens")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_revoke_forbidden_for_free_plan(async_client: AsyncClient, mock_user_no_subscription):
    response = await async_client.delete("/api/v1/auth/api-tokens/7")
    assert response.status_code == 403


# --- Integration tokens must not manage tokens (real get_current_user, no user fixture) ---

def _api_token_user():
    return User(id=1, email="ha@example.com", hashed_password="x", is_active=True,
                subscription_plan="pro", subscription_status="active")


_AUTH_API_TOKEN = "backend.app.modules.auth.service.api_token_service.authenticate_api_token"


@pytest.mark.asyncio
async def test_api_token_cannot_create_tokens(async_client: AsyncClient):
    with patch(_AUTH_API_TOKEN, AsyncMock(return_value=_api_token_user())):
        response = await async_client.post(
            "/api/v1/auth/api-tokens", json={"name": "HA"},
            headers={"Authorization": "Bearer asf_valid"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_api_token_cannot_list_tokens(async_client: AsyncClient):
    with patch(_AUTH_API_TOKEN, AsyncMock(return_value=_api_token_user())):
        response = await async_client.get(
            "/api/v1/auth/api-tokens", headers={"Authorization": "Bearer asf_valid"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_api_token_cannot_revoke_tokens(async_client: AsyncClient):
    with patch(_AUTH_API_TOKEN, AsyncMock(return_value=_api_token_user())):
        response = await async_client.delete(
            "/api/v1/auth/api-tokens/7", headers={"Authorization": "Bearer asf_valid"},
        )
    assert response.status_code == 403
