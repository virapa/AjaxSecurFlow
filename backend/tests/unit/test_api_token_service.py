import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from backend.app.modules.auth import api_token_service as svc
from backend.app.modules.auth.models import ApiToken, User


def _db_returning(scalar=None, scalar_one_or_none=None, scalars_all=None):
    db = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = scalar
    result.scalar_one_or_none.return_value = scalar_one_or_none
    result.scalars.return_value.all.return_value = scalars_all or []
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def test_generate_raw_token_has_prefix_and_length():
    raw = svc.generate_raw_token()
    assert raw.startswith("asf_")
    assert len(raw) >= 40


def test_hash_token_is_sha256_hex():
    assert len(svc.hash_token("asf_x")) == 64
    assert svc.hash_token("asf_x") == svc.hash_token("asf_x")
    assert svc.hash_token("asf_x") != svc.hash_token("asf_y")


@pytest.mark.asyncio
async def test_create_api_token_returns_model_and_raw_once():
    db = _db_returning(scalar=0)
    token, raw = await svc.create_api_token(db, user_id=1, name="HA", expires_in_days=None)
    assert raw.startswith("asf_")
    assert token.prefix == raw[:12]
    assert token.token_hash == svc.hash_token(raw)
    assert token.expires_at is None
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_api_token_sets_expiry():
    db = _db_returning(scalar=0)
    token, _ = await svc.create_api_token(db, user_id=1, name="HA", expires_in_days=30)
    assert token.expires_at is not None
    assert token.expires_at > datetime.now(timezone.utc) + timedelta(days=29)


@pytest.mark.asyncio
async def test_create_api_token_enforces_limit():
    db = _db_returning(scalar=svc.MAX_ACTIVE_TOKENS)
    with pytest.raises(svc.TokenLimitExceeded):
        await svc.create_api_token(db, user_id=1, name="HA", expires_in_days=None)


@pytest.mark.asyncio
async def test_revoke_api_token_marks_revoked():
    token = ApiToken(id=5, user_id=1, name="HA", token_hash="h", prefix="asf_12345678")
    db = _db_returning(scalar_one_or_none=token)
    assert await svc.revoke_api_token(db, user_id=1, token_id=5) is True
    assert token.revoked_at is not None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_api_token_unknown_returns_false():
    db = _db_returning(scalar_one_or_none=None)
    assert await svc.revoke_api_token(db, user_id=1, token_id=99) is False


@pytest.mark.asyncio
async def test_authenticate_rejects_non_prefixed():
    db = _db_returning()
    assert await svc.authenticate_api_token(db, "eyJhbGci") is None
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_returns_user_and_touches_last_used():
    user = User(id=1, email="u@x.com", hashed_password="x", is_active=True)
    token = ApiToken(id=5, user_id=1, name="HA", token_hash="h", prefix="asf_12345678")
    db = _db_returning(scalar_one_or_none=token)
    db.get = AsyncMock(return_value=user)
    assert await svc.authenticate_api_token(db, "asf_whatever") is user
    assert token.last_used_at is not None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_authenticate_does_not_rewrite_last_used_within_throttle():
    user = User(id=1, email="u@x.com", hashed_password="x", is_active=True)
    recent = datetime.now(timezone.utc) - timedelta(seconds=10)
    token = ApiToken(id=5, user_id=1, name="HA", token_hash="h", prefix="asf_12345678", last_used_at=recent)
    db = _db_returning(scalar_one_or_none=token)
    db.get = AsyncMock(return_value=user)
    assert await svc.authenticate_api_token(db, "asf_whatever") is user
    assert token.last_used_at == recent
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_rejects_expired():
    user = User(id=1, email="u@x.com", hashed_password="x", is_active=True)
    token = ApiToken(id=5, user_id=1, name="HA", token_hash="h", prefix="asf_12345678",
                     expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    db = _db_returning(scalar_one_or_none=token)
    db.get = AsyncMock(return_value=user)
    assert await svc.authenticate_api_token(db, "asf_whatever") is None


@pytest.mark.asyncio
async def test_authenticate_rejects_inactive_user():
    user = User(id=1, email="u@x.com", hashed_password="x", is_active=False)
    token = ApiToken(id=5, user_id=1, name="HA", token_hash="h", prefix="asf_12345678")
    db = _db_returning(scalar_one_or_none=token)
    db.get = AsyncMock(return_value=user)
    assert await svc.authenticate_api_token(db, "asf_whatever") is None
