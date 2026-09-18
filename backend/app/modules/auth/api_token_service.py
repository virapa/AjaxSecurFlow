"""
Long-lived integration tokens (Home Assistant and other external clients).
Tokens are opaque strings 'asf_<random>' validated by SHA-256 hash in the database.
"""
import hashlib
import secrets
from datetime import datetime as dt_datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.auth.models import ApiToken, User

TOKEN_PREFIX = "asf_"
PREFIX_LENGTH = 12
MAX_ACTIVE_TOKENS = 10
LAST_USED_THROTTLE_SECONDS = 60


class TokenLimitExceeded(Exception):
    pass


def generate_raw_token() -> str:
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(30)}"


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def count_active_tokens(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count(ApiToken.id)).where(
            ApiToken.user_id == user_id,
            ApiToken.revoked_at.is_(None)
        )
    )
    return int(result.scalar() or 0)


async def create_api_token(
    db: AsyncSession, user_id: int, name: str, expires_in_days: Optional[int]
) -> Tuple[ApiToken, str]:
    if await count_active_tokens(db, user_id) >= MAX_ACTIVE_TOKENS:
        raise TokenLimitExceeded()

    raw = generate_raw_token()
    expires_at = None
    if expires_in_days:
        expires_at = dt_datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    token = ApiToken(
        user_id=user_id,
        name=name.strip(),
        token_hash=hash_token(raw),
        prefix=raw[:PREFIX_LENGTH],
        expires_at=expires_at,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token, raw


async def list_api_tokens(db: AsyncSession, user_id: int) -> List[ApiToken]:
    result = await db.execute(
        select(ApiToken)
        .where(ApiToken.user_id == user_id, ApiToken.revoked_at.is_(None))
        .order_by(ApiToken.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_api_token(db: AsyncSession, user_id: int, token_id: int) -> bool:
    result = await db.execute(
        select(ApiToken).where(
            ApiToken.id == token_id,
            ApiToken.user_id == user_id,
            ApiToken.revoked_at.is_(None)
        )
    )
    token = result.scalar_one_or_none()
    if token is None:
        return False
    token.revoked_at = dt_datetime.now(timezone.utc)
    await db.commit()
    return True


async def authenticate_api_token(db: AsyncSession, raw_token: str) -> Optional[User]:
    """Returns the owning User for a valid, active token; None otherwise."""
    if not raw_token.startswith(TOKEN_PREFIX):
        return None

    result = await db.execute(
        select(ApiToken).where(
            ApiToken.token_hash == hash_token(raw_token),
            ApiToken.revoked_at.is_(None)
        )
    )
    token = result.scalar_one_or_none()
    if token is None:
        return None

    now = dt_datetime.now(timezone.utc)
    if not token.is_active(now):
        return None

    user = await db.get(User, token.user_id)
    if user is None or not user.is_active:
        return None

    if token.last_used_at is None or (now - token.last_used_at).total_seconds() > LAST_USED_THROTTLE_SECONDS:
        token.last_used_at = now
        await db.commit()

    return user
