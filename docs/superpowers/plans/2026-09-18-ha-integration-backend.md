# Home Assistant Integration: Backend + Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add revocable integration tokens (`asf_…`), expose sensor state fields in the device/hub schemas, and give users a dashboard section to manage tokens, so the Home Assistant integration (separate repo, second plan) can authenticate and read device state.

**Architecture:** New `api_tokens` table and service in the `auth` module; `get_current_user` accepts `asf_` bearer tokens validated by SHA-256 hash in Postgres (no JWT, no IP/User-Agent binding). `DeviceListItem`/`DeviceDetail` gain a shared `DeviceTelemetry` mixin so the device list already carries reed/motion/leak/smoke flags coming from Ajax `enrich=true`. Frontend adds a `features/integrations` section mounted in the profile page.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, pytest + pytest-asyncio; Next.js 15, React 19, TailwindCSS 4, Vitest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-09-18-home-assistant-integration-design.md`

**Conventions:**
- Run backend tests from the repo root: `python -m pytest backend/tests/unit/<file> -v` (venv at `./venv`; on Windows `venv/Scripts/python`).
- Run frontend tests from `frontend/`: `pnpm test:run <file>`.
- Branch: `feat/ha-integration` created from `dev`. First step of Task 1 creates it.
- Known baseline failures exist in the test suite (see memory `preexisting-test-failures`); only the tests named in this plan must pass.
- Code, comments and identifiers in English. UI strings in Spanish via `es.ts`.

---

## File map

| Path | Responsibility |
|---|---|
| `backend/app/modules/auth/models.py` | add `ApiToken` ORM model |
| `backend/alembic/versions/a3f7c9d1e2b4_add_api_tokens.py` | migration for `api_tokens` |
| `backend/alembic/env.py` | import `ApiToken` so autogenerate sees it |
| `backend/app/modules/auth/schemas.py` | `ApiTokenCreate`, `ApiTokenRead`, `ApiTokenCreated` |
| `backend/app/modules/auth/api_token_service.py` | generate/hash/create/list/revoke/authenticate |
| `backend/app/modules/auth/api_token_router.py` | `POST/GET/DELETE /auth/api-tokens` |
| `backend/app/modules/router.py` | include the new router |
| `backend/app/modules/auth/service.py` | `get_current_user` accepts `asf_` tokens |
| `backend/app/modules/ajax/schemas.py` | `DeviceTelemetry` mixin, `HubDetail.groups_enabled` |
| `backend/docs/API_PERMISSIONS.md`, `backend/docs/INTEGRATION_EXAMPLES.md`, `CHANGELOG.md` | docs |
| `DESIGN.md` | design tokens (repo rule: required before UI work) |
| `frontend/src/features/integrations/api-token.service.ts` | API calls |
| `frontend/src/features/integrations/ApiTokensSection.tsx` | UI section |
| `frontend/src/features/integrations/ApiTokensSection.test.tsx` | tests |
| `frontend/src/shared/i18n/es.ts` | `dashboard.profilePage.integrations` strings |
| `frontend/src/features/auth/ProfileComponent.tsx` | mount the section |

---

### Task 1: `ApiToken` model and migration

**Files:**
- Modify: `backend/app/modules/auth/models.py`
- Create: `backend/alembic/versions/a3f7c9d1e2b4_add_api_tokens.py`
- Modify: `backend/alembic/env.py:10`
- Test: `backend/tests/unit/test_api_token_model.py`

- [ ] **Step 1: Create the branch**

```bash
git checkout dev && git pull && git checkout -b feat/ha-integration
```

- [ ] **Step 2: Write the failing test**

```python
# backend/tests/unit/test_api_token_model.py
from datetime import datetime, timezone
from backend.app.modules.auth.models import ApiToken


def test_api_token_is_active_when_not_revoked_and_not_expired():
    token = ApiToken(user_id=1, name="HA", token_hash="abc", prefix="asf_12345678")
    assert token.is_active(datetime.now(timezone.utc)) is True


def test_api_token_inactive_when_revoked():
    now = datetime.now(timezone.utc)
    token = ApiToken(user_id=1, name="HA", token_hash="abc", prefix="asf_12345678", revoked_at=now)
    assert token.is_active(now) is False


def test_api_token_inactive_when_expired():
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    token = ApiToken(user_id=1, name="HA", token_hash="abc", prefix="asf_12345678", expires_at=now)
    assert token.is_active(now) is False
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest backend/tests/unit/test_api_token_model.py -v`
Expected: FAIL with `ImportError: cannot import name 'ApiToken'`

- [ ] **Step 4: Add the model**

Append to `backend/app/modules/auth/models.py`:

```python
from sqlalchemy import ForeignKey, Integer


class ApiToken(Base):
    """
    Long-lived integration token (e.g. Home Assistant).
    Only the SHA-256 hash is stored; the raw token is shown once at creation.
    """
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    last_used_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def is_active(self, now: dt_datetime) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= now:
            return False
        return True

    def __repr__(self):
        return f"<ApiToken(id={self.id}, user={self.user_id}, prefix={self.prefix})>"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest backend/tests/unit/test_api_token_model.py -v`
Expected: 3 PASSED

- [ ] **Step 6: Write the migration**

```python
# backend/alembic/versions/a3f7c9d1e2b4_add_api_tokens.py
"""add api_tokens table for long-lived integration tokens (Home Assistant)

Revision ID: a3f7c9d1e2b4
Revises: e7f1a9b2c3d4
Create Date: 2026-09-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a3f7c9d1e2b4'
down_revision: Union[str, Sequence[str], None] = 'e7f1a9b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('prefix', sa.String(length=12), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_api_tokens_id', 'api_tokens', ['id'])
    op.create_index('ix_api_tokens_user_id', 'api_tokens', ['user_id'])
    op.create_index('ix_api_tokens_token_hash', 'api_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_api_tokens_token_hash', table_name='api_tokens')
    op.drop_index('ix_api_tokens_user_id', table_name='api_tokens')
    op.drop_index('ix_api_tokens_id', table_name='api_tokens')
    op.drop_table('api_tokens')
```

- [ ] **Step 7: Register the model in Alembic env**

In `backend/alembic/env.py` change line 10:

```python
from backend.app.modules.auth.models import User, ApiToken
```

- [ ] **Step 8: Verify migration chain**

Run: `python -c "import backend.alembic.versions.a3f7c9d1e2b4_add_api_tokens as m; print(m.revision, m.down_revision)"`
Expected: `a3f7c9d1e2b4 e7f1a9b2c3d4`

If a local Postgres is available: `cd backend && alembic upgrade head && alembic downgrade -1 && alembic upgrade head`.

- [ ] **Step 9: Commit**

```bash
git add backend/app/modules/auth/models.py backend/alembic/versions/a3f7c9d1e2b4_add_api_tokens.py backend/alembic/env.py backend/tests/unit/test_api_token_model.py
git commit -m "feat(auth): add ApiToken model and api_tokens migration"
```

---

### Task 2: Token schemas and service

**Files:**
- Modify: `backend/app/modules/auth/schemas.py`
- Create: `backend/app/modules/auth/api_token_service.py`
- Test: `backend/tests/unit/test_api_token_service.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/unit/test_api_token_service.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest backend/tests/unit/test_api_token_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.modules.auth.api_token_service'`

- [ ] **Step 3: Add the schemas**

Append to `backend/app/modules/auth/schemas.py`:

```python
# Integration (API) Tokens
class ApiTokenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Label for this token, e.g. 'Home Assistant'")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="Optional expiry in days. Null = never expires")

class ApiTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    prefix: str = Field(..., description="First 12 characters, to identify the token in the UI")
    last_used_at: Optional[dt_datetime] = None
    expires_at: Optional[dt_datetime] = None
    created_at: dt_datetime

class ApiTokenCreated(ApiTokenRead):
    token: str = Field(..., description="Raw token. Shown only once at creation")
```

- [ ] **Step 4: Write the service**

```python
# backend/app/modules/auth/api_token_service.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest backend/tests/unit/test_api_token_service.py -v`
Expected: 12 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/auth/schemas.py backend/app/modules/auth/api_token_service.py backend/tests/unit/test_api_token_service.py
git commit -m "feat(auth): add api token service and schemas"
```

---

### Task 3: Token endpoints

**Files:**
- Create: `backend/app/modules/auth/api_token_router.py`
- Modify: `backend/app/modules/router.py`
- Test: `backend/tests/unit/test_api_token_endpoints.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/unit/test_api_token_endpoints.py
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from backend.app.modules.auth.models import ApiToken
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest backend/tests/unit/test_api_token_endpoints.py -v`
Expected: FAIL, every test gets 404 (route does not exist)

- [ ] **Step 3: Write the router**

```python
# backend/app/modules/auth/api_token_router.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.auth import service as auth_service
from backend.app.modules.auth import api_token_service
from backend.app.modules.auth.schemas import ApiTokenCreate, ApiTokenCreated, ApiTokenRead
from backend.app.modules.billing import service as billing_service
from backend.app.modules.security import service as security_service
from backend.app.shared.infrastructure.database.session import get_db

router = APIRouter(
    tags=["Integration Tokens"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Plan Basic or higher required"},
    },
)

REQUIRED_FEATURE = "read_devices"  # Basic+; Free plan cannot use the HA integration


def _require_plan(user: auth_service.User):
    if not billing_service.can_access_feature(user, REQUIRED_FEATURE):
        raise HTTPException(status_code=403, detail="Integration tokens require a BASIC plan or higher.")


@router.post(
    "",
    response_model=ApiTokenCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an integration token",
    description="""
    Create a long-lived token for external integrations (e.g. Home Assistant).
    The raw token is returned **only once**. Store it securely.

    **Required Plan**: Basic or higher. Maximum 10 active tokens per user.
    """,
)
async def create_token(
    body: ApiTokenCreate,
    request: Request,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_plan(current_user)
    try:
        token, raw = await api_token_service.create_api_token(
            db, user_id=current_user.id, name=body.name, expires_in_days=body.expires_in_days
        )
    except api_token_service.TokenLimitExceeded:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum of {api_token_service.MAX_ACTIVE_TOKENS} active tokens reached. Revoke one first.",
        )

    await security_service.log_request_action(
        db=db, request=request, user_id=current_user.id,
        action="API_TOKEN_CREATED", status_code=201, severity="INFO",
        resource_id=str(token.id), payload={"prefix": token.prefix, "name": token.name},
    )
    return ApiTokenCreated(
        id=token.id, name=token.name, prefix=token.prefix,
        last_used_at=token.last_used_at, expires_at=token.expires_at,
        created_at=token.created_at, token=raw,
    )


@router.get(
    "",
    response_model=List[ApiTokenRead],
    summary="List integration tokens",
    description="List active (non-revoked) integration tokens. Raw tokens are never returned.",
)
async def list_tokens(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_plan(current_user)
    return await api_token_service.list_api_tokens(db, user_id=current_user.id)


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an integration token",
    description="Revoke a token. Any client using it gets 401 immediately.",
)
async def revoke_token(
    token_id: int,
    request: Request,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_plan(current_user)
    revoked = await api_token_service.revoke_api_token(db, user_id=current_user.id, token_id=token_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Token not found.")
    await security_service.log_request_action(
        db=db, request=request, user_id=current_user.id,
        action="API_TOKEN_REVOKED", status_code=204, severity="INFO", resource_id=str(token_id),
    )
    return None
```

- [ ] **Step 4: Include the router**

In `backend/app/modules/router.py` add the import and include it **before** the `/auth` router line so `/auth/api-tokens` is not shadowed:

```python
from backend.app.modules.auth.api_token_router import router as api_token_router
...
api_router.include_router(api_token_router, prefix="/auth/api-tokens")
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest backend/tests/unit/test_api_token_endpoints.py -v`
Expected: 7 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/auth/api_token_router.py backend/app/modules/router.py backend/tests/unit/test_api_token_endpoints.py
git commit -m "feat(auth): add /auth/api-tokens endpoints"
```

---

### Task 4: `get_current_user` accepts `asf_` tokens

**Files:**
- Modify: `backend/app/modules/auth/service.py:71-95`
- Test: `backend/tests/unit/test_auth_api_token.py`

- [ ] **Step 1: Write the failing tests**

`/api/v1/security/audit-logs` is used as the probe endpoint: it only needs `get_current_user` and the mocked DB.

```python
# backend/tests/unit/test_auth_api_token.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest backend/tests/unit/test_auth_api_token.py -v`
Expected: first two FAIL with 401 (token is not a JWT); third FAILS on the audit assertion; fourth may pass.

- [ ] **Step 3: Modify `get_current_user`**

Add the import at the top of `backend/app/modules/auth/service.py` (after the `security_service` import):

```python
from backend.app.modules.auth import api_token_service
```

Then in `get_current_user`, right after the `Bearer ` prefix is stripped (line ~84) and **before** `try: payload = jwt.decode(...)`, add:

```python
    # Integration tokens (asf_...): opaque, validated by hash; no UA/IP binding.
    if token.startswith(api_token_service.TOKEN_PREFIX):
        api_user = await api_token_service.authenticate_api_token(db, token)
        if api_user is None:
            await security_service.log_request_action(
                db=db, request=request, user_id=None,
                action="API_TOKEN_INVALID", status_code=401, severity="WARNING",
                payload={"prefix": token[:api_token_service.PREFIX_LENGTH]}
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return api_user
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest backend/tests/unit/test_auth_api_token.py backend/tests/unit/test_auth_refresh.py -v`
Expected: all PASSED (the refresh tests prove the JWT path is untouched)

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/auth/service.py backend/tests/unit/test_auth_api_token.py
git commit -m "feat(auth): accept asf_ integration tokens in get_current_user"
```

---

### Task 5: Device telemetry fields and `groups_enabled`

**Files:**
- Modify: `backend/app/modules/ajax/schemas.py:73-108`
- Test: `backend/tests/unit/test_ajax_schemas.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/unit/test_ajax_schemas.py`:

```python
from backend.app.modules.ajax.schemas import DeviceListItem, HubDetail

# Shape produced by AjaxClient.get_hub_devices (enrich=true, properties flattened)
ENRICHED_DOOR = {
    "deviceId": "AABB0001", "hubId": "0004C602", "deviceName": "Puerta principal",
    "deviceType": "DoorProtect", "roomId": "1", "groupId": "1", "online": True,
    "batteryChargeLevelPercentage": 88, "signalLevel": "STRONG", "temperature": 21.5,
    "tampered": False, "state": "ACTIVE", "malfunctions": [],
    "reedClosed": True, "extraContactAware": True, "extraContactClosed": False,
}
ENRICHED_MOTION = {
    "deviceId": "AABB0002", "hubId": "0004C602", "deviceName": "Salón",
    "deviceType": "MotionProtect", "online": True, "motionDetected": True,
    "batteryChargeLevelPercentage": 100, "signalLevel": "STRONG",
}


def test_device_list_item_exposes_sensor_fields():
    item = DeviceListItem(**ENRICHED_DOOR)
    dumped = item.model_dump(by_alias=True)
    assert dumped["reed_closed"] is True
    assert dumped["extra_contact_aware"] is True
    assert dumped["extra_contact_closed"] is False
    assert dumped["battery_level"] == 88
    assert dumped["signal_level"] == "STRONG"
    assert dumped["temperature"] == 21.5
    assert dumped["tampered"] is False
    assert dumped["malfunctions"] == []


def test_device_list_item_motion_and_missing_fields_are_none():
    item = DeviceListItem(**ENRICHED_MOTION)
    dumped = item.model_dump(by_alias=True)
    assert dumped["motion_detected"] is True
    assert dumped["reed_closed"] is None
    assert dumped["leak_detected"] is None
    assert dumped["smoke_alarm_detected"] is None
    assert dumped["humidity"] is None
    assert dumped["co2"] is None


def test_device_detail_has_same_sensor_fields():
    detail = DeviceDetail(**{**ENRICHED_DOOR, "id": "AABB0001"})
    dumped = detail.model_dump(by_alias=True)
    assert dumped["reed_closed"] is True
    assert dumped["battery_level"] == 88
    assert dumped["firmware_version"] is None


def test_hub_detail_groups_enabled():
    hub = HubDetail(id="0004C602", groupsEnabled=True, state="ARMED_NIGHT_MODE_OFF")
    dumped = hub.model_dump(by_alias=True)
    assert dumped["groups_enabled"] is True
    assert dumped["state"] == "ARMED_NIGHT_MODE_OFF"


def test_hub_detail_groups_enabled_default_none():
    assert HubDetail(id="0004C602").groups_enabled is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest backend/tests/unit/test_ajax_schemas.py -v`
Expected: new tests FAIL with `KeyError: 'reed_closed'` / `ValidationError` (unknown field `groups_enabled`)

- [ ] **Step 3: Refactor the schemas**

In `backend/app/modules/ajax/schemas.py`, replace the `DeviceListItem` and `DeviceDetail` classes with:

```python
class DeviceTelemetry(BaseModel):
    """
    Telemetry and sensor state shared by list and detail views.
    Ajax returns these inside `properties`; AjaxClient flattens them for the list (enrich=true).
    All optional: a field is None when the device type does not report it.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    battery_level: Optional[int] = Field(None, validation_alias=AliasChoices("battery_level", "batteryChargeLevelPercentage"), serialization_alias="battery_level")
    signal_level: Optional[str] = Field(None, validation_alias=AliasChoices("signal_level", "signalLevel"), serialization_alias="signal_level")
    temperature: Optional[float] = Field(None, serialization_alias="temperature")
    humidity: Optional[float] = Field(None, serialization_alias="humidity")
    co2: Optional[float] = Field(None, serialization_alias="co2")
    tampered: Optional[bool] = Field(None, serialization_alias="tampered")
    state: Optional[str] = Field(None, serialization_alias="state")
    malfunctions: List[str] = Field(default_factory=list, serialization_alias="malfunctions")
    # Sensor flags
    reed_closed: Optional[bool] = Field(None, validation_alias=AliasChoices("reed_closed", "reedClosed"), serialization_alias="reed_closed")
    extra_contact_aware: Optional[bool] = Field(None, validation_alias=AliasChoices("extra_contact_aware", "extraContactAware"), serialization_alias="extra_contact_aware")
    extra_contact_closed: Optional[bool] = Field(None, validation_alias=AliasChoices("extra_contact_closed", "extraContactClosed"), serialization_alias="extra_contact_closed")
    motion_detected: Optional[bool] = Field(None, validation_alias=AliasChoices("motion_detected", "motionDetected"), serialization_alias="motion_detected")
    glass_break_detected: Optional[bool] = Field(None, validation_alias=AliasChoices("glass_break_detected", "glassBreakDetected"), serialization_alias="glass_break_detected")
    leak_detected: Optional[bool] = Field(None, validation_alias=AliasChoices("leak_detected", "leakDetected"), serialization_alias="leak_detected")
    smoke_alarm_detected: Optional[bool] = Field(None, validation_alias=AliasChoices("smoke_alarm_detected", "smokeAlarmDetected"), serialization_alias="smoke_alarm_detected")

class DeviceListItem(DeviceBase, DeviceTelemetry):
    online: Optional[bool] = Field(None, validation_alias=AliasChoices("online", "isOnline"), serialization_alias="online")

class DeviceDetail(DeviceBase, DeviceTelemetry):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    online: Optional[bool] = Field(True, serialization_alias="online")
    color: Optional[str] = Field(None, serialization_alias="color")
    firmware_version: Optional[str] = Field(None, validation_alias=AliasChoices("firmware_version", "firmwareVersion"), serialization_alias="firmware_version")
    night_mode_arm: Optional[bool] = Field(None, validation_alias=AliasChoices("night_mode_arm", "nightModeArm"), serialization_alias="night_mode_arm")

    arm_delay: Optional[int] = Field(None, validation_alias=AliasChoices("arm_delay", "armDelaySeconds"))
    alarm_delay: Optional[int] = Field(None, validation_alias=AliasChoices("alarm_delay", "alarmDelaySeconds"))

    cms_index: Optional[int] = Field(None, validation_alias=AliasChoices("cms_index", "cmsDeviceIndex"))
    bypassState: Optional[List[str]] = None
```

In `HubDetail` add after `hub_subtype`:

```python
    groups_enabled: Optional[bool] = Field(None, validation_alias=AliasChoices("groups_enabled", "groupsEnabled"), serialization_alias="groups_enabled")
```

- [ ] **Step 4: Run schema and endpoint tests**

Run: `python -m pytest backend/tests/unit/test_ajax_schemas.py backend/tests/unit/test_ajax_endpoints.py -v`
Expected: all PASSED (the endpoint tests prove the device list still serializes)

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/ajax/schemas.py backend/tests/unit/test_ajax_schemas.py
git commit -m "feat(ajax): expose sensor state fields in device list/detail and hub groups_enabled"
```

---

### Task 6: Backend docs and changelog

**Files:**
- Modify: `backend/docs/API_PERMISSIONS.md` (Device/Room/Group section)
- Modify: `backend/docs/INTEGRATION_EXAMPLES.md` (append)
- Modify: `CHANGELOG.md` (top)

- [ ] **Step 1: Add the permissions rows**

In `backend/docs/API_PERMISSIONS.md`, after the table under "### Device/Room/Group Endpoints (Basic+)", add a new subsection:

```markdown
### Integration Tokens (Basic+)

Long-lived tokens for external clients such as the Home Assistant integration. The token inherits the plan of its owner.

| Endpoint                          | Method | Feature        | Description                                        |
| --------------------------------- | ------ | -------------- | -------------------------------------------------- |
| `/api/v1/auth/api-tokens`         | POST   | `read_devices` | Create a token (raw value returned once). Max 10   |
| `/api/v1/auth/api-tokens`         | GET    | `read_devices` | List active tokens (prefix only)                   |
| `/api/v1/auth/api-tokens/{id}`    | DELETE | `read_devices` | Revoke a token                                     |

Use the token as `Authorization: Bearer asf_...`. Unlike session JWTs, integration tokens are not bound to IP or User-Agent and never expire unless `expires_in_days` was set or the token is revoked.
```

- [ ] **Step 2: Document the SSE contract**

Append to `backend/docs/INTEGRATION_EXAMPLES.md`:

```markdown
## Home Assistant: integration token + SSE contract

1. Create a token in the dashboard (Profile → Integraciones) or via `POST /api/v1/auth/api-tokens`.
2. Install the `ajaxsecurflow` custom integration through HACS and paste the token.

### Real-time stream

`GET /api/v1/ajax/events/stream` (Basic+) emits `event: ajax_event` lines whose `data` is the hybrid envelope:

```json
{
  "id": "12345",
  "hub_id": "0004C602",
  "event_type": "ALARM",
  "title": "🛑 ALARMA DETECTADA",
  "description": "Movimiento detectado, Salón en Planta baja",
  "severity": "critical",
  "timestamp": "2026-09-18T10:15:00+00:00",
  "media_urls": [],
  "source": "sqs",
  "data": {
    "recipient": {"id": "…", "type": "USER"},
    "event": {
      "eventId": "…", "hubId": "0004C602", "eventType": "ALARM", "eventTypeV2": "ALARM",
      "eventCode": "…", "eventTag": "MotionDetected", "transition": "TRIGGERED",
      "sourceObjectId": "AABB0002", "sourceObjectType": "MOTION_PROTECT",
      "sourceObjectName": "Salón", "sourceRoomName": "Planta baja",
      "timestamp": 1789999900000, "additionalData": {}
    }
  }
}
```

`event_type` values seen in production: `ALARM`, `SECURITY`, `COMMON`, `MALFUNCTION`, `FUNCTION_RECOVERED`. `transition` is `TRIGGERED` or `RECOVERED`. Comment lines (`: ping`) are keep-alives and must be ignored.

### Device state fields

`GET /api/v1/ajax/hubs/{hub_id}/devices` returns, per device, the telemetry Ajax reports with `enrich=true`: `battery_level`, `signal_level`, `temperature`, `humidity`, `co2`, `tampered`, `malfunctions`, and the sensor flags `reed_closed`, `extra_contact_aware`, `extra_contact_closed`, `motion_detected`, `glass_break_detected`, `leak_detected`, `smoke_alarm_detected`. A field is `null` when the device type does not report it.
```

- [ ] **Step 3: Changelog entry**

Insert after the intro paragraph in `CHANGELOG.md` (before `## [1.2.0]`):

```markdown
## [1.3.0] - Unreleased

### Added
- **Integration Tokens**: `POST/GET/DELETE /api/v1/auth/api-tokens` issue revocable `asf_` tokens for external clients (Home Assistant). Validated by hash, not bound to IP/User-Agent. Basic plan or higher, max 10 active per user.
- **Dashboard → Integraciones**: create, copy once, and revoke integration tokens from the profile page.
- **Device sensor state**: device list and detail now expose `reed_closed`, `motion_detected`, `glass_break_detected`, `leak_detected`, `smoke_alarm_detected`, `humidity`, `co2`, `malfunctions`; hub detail exposes `groups_enabled`.
- **Docs**: SSE envelope contract for integrations in `backend/docs/INTEGRATION_EXAMPLES.md`.
```

- [ ] **Step 4: Commit**

```bash
git add backend/docs/API_PERMISSIONS.md backend/docs/INTEGRATION_EXAMPLES.md CHANGELOG.md
git commit -m "docs: document integration tokens, SSE contract and device state fields"
```

---

### Task 7: `DESIGN.md` (repo rule gate before UI work)

**Files:**
- Create: `DESIGN.md`

The repo rule `.agents/rules/design-rules.md` requires a `DESIGN.md` at the project root before any UI code. It does not exist yet. Tokens below are extracted from the current dashboard (`ProfileComponent.tsx`, `DeviceTelemetry.tsx`): dark navy ground, cyan accent, large radii, black-weight uppercase micro-labels.

- [ ] **Step 1: Write the file**

```markdown
---
name: AjaxSecurFlow Dashboard
description: Industrial dark console for the AjaxSecurFlow SaaS dashboard.
colors:
  ground: "#020617"
  surface: "#0F172A"
  surface-raised: "#1E293B"
  border: "#FFFFFF0D"
  primary: "#0891B2"
  primary-hover: "#06B6D4"
  primary-text: "#22D3EE"
  on-surface: "#FFFFFF"
  on-surface-muted: "#6B7280"
  on-surface-faint: "#4B5563"
  success: "#4ADE80"
  warning: "#FACC15"
  error: "#F87171"
typography:
  headline-lg: { fontFamily: Inter, fontSize: 30px, fontWeight: 900, lineHeight: 1.1, letterSpacing: -0.02em }
  headline-md: { fontFamily: Inter, fontSize: 18px, fontWeight: 700, lineHeight: 1.2 }
  section-title: { fontFamily: Inter, fontSize: 14px, fontWeight: 900, lineHeight: 1.2, letterSpacing: 0.1em }
  body-md: { fontFamily: Inter, fontSize: 14px, fontWeight: 500, lineHeight: 1.5 }
  body-sm: { fontFamily: Inter, fontSize: 12px, fontWeight: 700, lineHeight: 1.4 }
  label-xs: { fontFamily: Inter, fontSize: 10px, fontWeight: 900, lineHeight: 1.2, letterSpacing: 0.1em }
  mono-sm: { fontFamily: ui-monospace, fontSize: 12px, fontWeight: 500, lineHeight: 1.5 }
rounded:
  md: 12px
  lg: 16px
  xl: 24px
  hero: 40px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 40px
components:
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: 32px
  field:
    backgroundColor: "#FFFFFF0D"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: 16px
    typography: "{typography.label-xs}"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-danger:
    backgroundColor: "#F8717126"
    textColor: "{colors.error}"
    rounded: "{rounded.md}"
    padding: 8px
  chip-code:
    backgroundColor: "#FFFFFF0D"
    textColor: "{colors.primary-text}"
    rounded: "{rounded.md}"
    padding: 8px
    typography: "{typography.mono-sm}"
---

# AjaxSecurFlow Dashboard

## Overview
A control-room console for security professionals. Dark, dense, confident. Everything sits on a near-black navy ground; cyan is reserved for the primary action and live status. Section titles are tiny, black-weight, uppercase and letter-spaced, like an equipment label.

## Colors
- **Ground (#020617)** page background. **Surface (#0F172A)** cards at 40% opacity over ground. **Surface raised (#1E293B)** hero gradients.
- **Primary (#0891B2)** the only saturated call to action; hover lifts to **#06B6D4**. **Primary text (#22D3EE)** for accent text and code chips.
- **Borders** are white at 5% opacity, never solid grey.
- **Success / Warning / Error** appear only on status pills and inline alerts, at 10% background + 20% border tints.

## Typography
Inter throughout. Two registers: black-weight uppercase micro-labels (`label-xs`, `section-title`) for structure, and medium-weight body for content. Monospace is used only for tokens, ids and code.

## Layout
Content column `max-width 896px`, page padding `xl`, vertical rhythm `xl` between cards, `md` inside. Two-column grid on `md+`, single column below.

## Elevation & Depth
Flat. Depth comes from tonal layering (ground → surface → field) and 5% white borders. The only shadow is the primary button glow (`shadow-cyan-500/20`).

## Shapes
Generous radii: fields `md`, buttons `lg`, cards `xl`, hero `hero`. Never mix square corners into a view.

## Components
- **Card**: `surface` at 40%, 5% border, `xl` radius, 32px padding, `section-title` heading with `md` gap below.
- **Field (read-only)**: 5% white background, 10% border, `md` radius, `body-md` text, `label-xs` muted label above.
- **Button primary**: full width in forms, `label-xs` uppercase, cyan glow, `active:scale-[0.98]`.
- **Button danger**: small, error tint background, error text, used for revoke/delete with a confirmation step.
- **Chip code**: monospace, primary-text on 5% white, for token prefixes and ids.
- **Inline alert**: 10% tint background + 20% tint border of the semantic color, `body-sm`, centered.

## Do's and Don'ts
- Do keep cyan for one primary action per card.
- Do use `label-xs` uppercase for every field label and table header.
- Don't introduce purple or gradients outside the hero card.
- Don't use solid grey borders or drop shadows on cards.
- Don't show secrets more than once; after creation, replace with the prefix chip.
```

- [ ] **Step 2: Commit**

```bash
git add DESIGN.md
git commit -m "docs: add DESIGN.md design tokens for the dashboard"
```

---

### Task 8: Frontend service and i18n strings

**Files:**
- Create: `frontend/src/features/integrations/api-token.service.ts`
- Modify: `frontend/src/shared/i18n/es.ts:188-203`
- Test: `frontend/src/features/integrations/api-token.service.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/features/integrations/api-token.service.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from '@/infrastructure/api-client'
import { apiTokenService } from './api-token.service'

vi.mock('@/infrastructure/api-client', () => ({
    apiClient: { get: vi.fn(), post: vi.fn(), delete: vi.fn() }
}))

describe('apiTokenService', () => {
    beforeEach(() => vi.clearAllMocks())

    it('lists tokens from /auth/api-tokens', async () => {
        vi.mocked(apiClient.get).mockResolvedValue([{ id: 1, name: 'HA', prefix: 'asf_abcdefgh', created_at: '2026-09-18T00:00:00Z' }])
        const tokens = await apiTokenService.list()
        expect(apiClient.get).toHaveBeenCalledWith('/auth/api-tokens')
        expect(tokens[0].prefix).toBe('asf_abcdefgh')
    })

    it('creates a token with a name', async () => {
        vi.mocked(apiClient.post).mockResolvedValue({ id: 2, name: 'HA', prefix: 'asf_abcdefgh', token: 'asf_abcdefghRAW', created_at: '2026-09-18T00:00:00Z' })
        const created = await apiTokenService.create('HA')
        expect(apiClient.post).toHaveBeenCalledWith('/auth/api-tokens', { name: 'HA' })
        expect(created.token).toBe('asf_abcdefghRAW')
    })

    it('revokes a token by id', async () => {
        vi.mocked(apiClient.delete).mockResolvedValue(undefined)
        await apiTokenService.revoke(7)
        expect(apiClient.delete).toHaveBeenCalledWith('/auth/api-tokens/7')
    })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `pnpm test:run src/features/integrations/api-token.service.test.ts`
Expected: FAIL, cannot resolve `./api-token.service`

- [ ] **Step 3: Note on `apiClient`**

`frontend/src/infrastructure/api-client.ts:93-118` exposes `get`, `post`, `put`, `patch` and `delete`, all generic `<T>`. The service below uses `get`, `post` and `delete`.

- [ ] **Step 4: Write the service**

```ts
// frontend/src/features/integrations/api-token.service.ts
import { apiClient } from '@/infrastructure/api-client'

export interface ApiToken {
    id: number
    name: string
    prefix: string
    last_used_at?: string | null
    expires_at?: string | null
    created_at: string
}

export interface ApiTokenCreated extends ApiToken {
    /** Raw token. Returned only once by the backend. */
    token: string
}

/**
 * Integration Tokens Service (Local Scope: features/integrations)
 * Long-lived tokens used by external clients such as the Home Assistant integration.
 */
export const apiTokenService = {
    list: (): Promise<ApiToken[]> => apiClient.get<ApiToken[]>('/auth/api-tokens'),
    create: (name: string): Promise<ApiTokenCreated> => apiClient.post<ApiTokenCreated>('/auth/api-tokens', { name }),
    revoke: (id: number): Promise<void> => apiClient.delete<void>(`/auth/api-tokens/${id}`),
}
```

- [ ] **Step 5: Add i18n strings**

In `frontend/src/shared/i18n/es.ts`, inside `dashboard.profilePage` after the `labels` object, add:

```ts
            integrations: {
                title: 'Integraciones',
                description: 'Tokens de acceso para Home Assistant y otros clientes externos. Cada token hereda tu plan.',
                docsLink: 'Guía de instalación en Home Assistant',
                createButton: 'Crear token',
                namePlaceholder: 'Nombre (p. ej. Home Assistant)',
                confirmCreate: 'Generar',
                cancel: 'Cancelar',
                createdTitle: 'Token creado',
                createdWarning: 'Cópialo ahora. No se volverá a mostrar.',
                copy: 'Copiar',
                copied: 'Copiado',
                done: 'Hecho',
                empty: 'No tienes tokens activos.',
                columns: {
                    name: 'Nombre',
                    prefix: 'Prefijo',
                    created: 'Creado',
                    lastUsed: 'Último uso'
                },
                never: 'Nunca',
                revoke: 'Revocar',
                revokeConfirm: '¿Revocar este token? Los clientes que lo usen dejarán de funcionar.',
                planRequired: 'Los tokens de integración requieren el plan Basic o superior.',
                limitReached: 'Has alcanzado el máximo de 10 tokens activos.',
                error: 'No se pudo completar la operación. Inténtalo de nuevo.'
            },
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pnpm test:run src/features/integrations/api-token.service.test.ts`
Expected: 3 PASSED

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/integrations/api-token.service.ts frontend/src/features/integrations/api-token.service.test.ts frontend/src/shared/i18n/es.ts
git commit -m "feat(frontend): add api token service and integrations i18n strings"
```

---

### Task 9: `ApiTokensSection` component

**Files:**
- Create: `frontend/src/features/integrations/ApiTokensSection.tsx`
- Test: `frontend/src/features/integrations/ApiTokensSection.test.tsx`

- [ ] **Step 1: Write the failing tests**

```tsx
// frontend/src/features/integrations/ApiTokensSection.test.tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiTokensSection } from './ApiTokensSection'
import { apiTokenService } from './api-token.service'
import { es as t } from '@/shared/i18n/es'

vi.mock('./api-token.service', () => ({
    apiTokenService: { list: vi.fn(), create: vi.fn(), revoke: vi.fn() }
}))

const i18n = t.dashboard.profilePage.integrations
const existing = { id: 1, name: 'HA Casa', prefix: 'asf_abcdefgh', created_at: '2026-09-18T10:00:00Z', last_used_at: null }

describe('ApiTokensSection (Local Scope: Integrations)', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.mocked(apiTokenService.list).mockResolvedValue([existing])
    })

    it('lists active tokens with prefix, never the raw token', async () => {
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(screen.getByText('HA Casa')).toBeInTheDocument())
        expect(screen.getByText('asf_abcdefgh')).toBeInTheDocument()
        expect(screen.getByText(i18n.never)).toBeInTheDocument()
    })

    it('creates a token and shows the raw value once', async () => {
        vi.mocked(apiTokenService.create).mockResolvedValue({ ...existing, id: 2, name: 'Nuevo', token: 'asf_abcdefghRAWVALUE' })
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(apiTokenService.list).toHaveBeenCalled())

        fireEvent.click(screen.getByText(i18n.createButton))
        fireEvent.change(screen.getByPlaceholderText(i18n.namePlaceholder), { target: { value: 'Nuevo' } })
        fireEvent.click(screen.getByText(i18n.confirmCreate))

        await waitFor(() => expect(screen.getByTestId('raw-token')).toHaveTextContent('asf_abcdefghRAWVALUE'))
        expect(apiTokenService.create).toHaveBeenCalledWith('Nuevo')
        expect(screen.getByText(i18n.createdWarning)).toBeInTheDocument()

        fireEvent.click(screen.getByText(i18n.done))
        await waitFor(() => expect(screen.queryByTestId('raw-token')).not.toBeInTheDocument())
        expect(apiTokenService.list).toHaveBeenCalledTimes(2)
    })

    it('revokes after confirmation', async () => {
        vi.mocked(apiTokenService.revoke).mockResolvedValue(undefined)
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(screen.getByText('HA Casa')).toBeInTheDocument())

        fireEvent.click(screen.getByText(i18n.revoke))
        expect(screen.getByText(i18n.revokeConfirm)).toBeInTheDocument()
        fireEvent.click(screen.getByTestId('confirm-revoke'))

        await waitFor(() => expect(apiTokenService.revoke).toHaveBeenCalledWith(1))
        expect(apiTokenService.list).toHaveBeenCalledTimes(2)
    })

    it('disables creation for the free plan', async () => {
        render(<ApiTokensSection plan="free" />)
        expect(screen.getByText(i18n.planRequired)).toBeInTheDocument()
        expect(screen.getByText(i18n.createButton)).toBeDisabled()
        expect(apiTokenService.list).not.toHaveBeenCalled()
    })

    it('shows the limit message on a 400 from the backend', async () => {
        vi.mocked(apiTokenService.create).mockRejectedValue(new Error('API Error: 400 Maximum of 10 active tokens reached'))
        render(<ApiTokensSection plan="pro" />)
        await waitFor(() => expect(apiTokenService.list).toHaveBeenCalled())
        fireEvent.click(screen.getByText(i18n.createButton))
        fireEvent.change(screen.getByPlaceholderText(i18n.namePlaceholder), { target: { value: 'X' } })
        fireEvent.click(screen.getByText(i18n.confirmCreate))
        await waitFor(() => expect(screen.getByText(i18n.limitReached)).toBeInTheDocument())
    })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pnpm test:run src/features/integrations/ApiTokensSection.test.tsx`
Expected: FAIL, cannot resolve `./ApiTokensSection`

- [ ] **Step 3: Write the component**

Styling follows `DESIGN.md` tokens (card, field, button-primary, button-danger, chip-code, inline alert).

```tsx
// frontend/src/features/integrations/ApiTokensSection.tsx
'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { es as t } from '@/shared/i18n/es'
import { apiTokenService, ApiToken, ApiTokenCreated } from './api-token.service'

const i18n = t.dashboard.profilePage.integrations
const HA_DOCS_URL = 'https://github.com/virapa/ajaxsecurflow-hass#readme'
const PLANS_WITH_TOKENS = ['basic', 'pro', 'premium']

interface ApiTokensSectionProps {
    plan?: string
}

const formatDate = (iso?: string | null) =>
    iso ? new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }) : i18n.never

export const ApiTokensSection: React.FC<ApiTokensSectionProps> = ({ plan }) => {
    const allowed = PLANS_WITH_TOKENS.includes(plan || '')
    const [tokens, setTokens] = useState<ApiToken[]>([])
    const [isCreating, setIsCreating] = useState(false)
    const [newName, setNewName] = useState('')
    const [created, setCreated] = useState<ApiTokenCreated | null>(null)
    const [copied, setCopied] = useState(false)
    const [pendingRevoke, setPendingRevoke] = useState<number | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)

    const load = useCallback(async () => {
        try {
            setTokens(await apiTokenService.list())
        } catch {
            setError(i18n.error)
        }
    }, [])

    useEffect(() => {
        if (allowed) load()
    }, [allowed, load])

    const handleCreate = async () => {
        if (!newName.trim()) return
        setBusy(true)
        setError(null)
        try {
            const result = await apiTokenService.create(newName.trim())
            setCreated(result)
            setIsCreating(false)
            setNewName('')
        } catch (err) {
            const message = err instanceof Error ? err.message : ''
            setError(message.includes('400') ? i18n.limitReached : i18n.error)
        } finally {
            setBusy(false)
        }
    }

    const handleDone = async () => {
        setCreated(null)
        setCopied(false)
        await load()
    }

    const handleCopy = async () => {
        if (!created) return
        try {
            await navigator.clipboard.writeText(created.token)
            setCopied(true)
        } catch {
            setCopied(false)
        }
    }

    const handleRevoke = async (id: number) => {
        setBusy(true)
        setError(null)
        try {
            await apiTokenService.revoke(id)
            setPendingRevoke(null)
            await load()
        } catch {
            setError(i18n.error)
        } finally {
            setBusy(false)
        }
    }

    return (
        <section className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-8 space-y-6" data-testid="api-tokens-section">
            <div className="space-y-2">
                <h3 className="text-sm font-black uppercase tracking-widest text-white">{i18n.title}</h3>
                <p className="text-[10px] text-gray-500 leading-tight">{i18n.description}</p>
                <a href={HA_DOCS_URL} target="_blank" rel="noreferrer" className="inline-block text-xs font-bold text-cyan-400 hover:text-cyan-300">
                    {i18n.docsLink} →
                </a>
            </div>

            {!allowed && (
                <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-xs font-bold text-center">
                    {i18n.planRequired}
                </div>
            )}

            {error && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-bold text-center">
                    {error}
                </div>
            )}

            {created && (
                <div className="p-5 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 space-y-3">
                    <p className="text-xs font-black uppercase tracking-widest text-cyan-400">{i18n.createdTitle}</p>
                    <p className="text-[10px] text-gray-400">{i18n.createdWarning}</p>
                    <code data-testid="raw-token" className="block w-full break-all bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs font-mono text-cyan-300">
                        {created.token}
                    </code>
                    <div className="flex gap-3">
                        <button onClick={handleCopy} className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-[10px] font-black uppercase tracking-widest text-white">
                            {copied ? i18n.copied : i18n.copy}
                        </button>
                        <button onClick={handleDone} className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest text-white">
                            {i18n.done}
                        </button>
                    </div>
                </div>
            )}

            {allowed && !created && (
                isCreating ? (
                    <div className="flex flex-col md:flex-row gap-3">
                        <input
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder={i18n.namePlaceholder}
                            maxLength={64}
                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-medium outline-none focus:border-cyan-500/50"
                        />
                        <button onClick={handleCreate} disabled={busy || !newName.trim()} className="px-5 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-[10px] font-black uppercase tracking-widest text-white">
                            {i18n.confirmCreate}
                        </button>
                        <button onClick={() => { setIsCreating(false); setNewName('') }} className="px-5 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest text-white">
                            {i18n.cancel}
                        </button>
                    </div>
                ) : (
                    <button onClick={() => setIsCreating(true)} className="w-full py-4 rounded-2xl bg-cyan-600 hover:bg-cyan-500 text-sm font-black uppercase tracking-widest text-white transition-all shadow-xl shadow-cyan-500/20 active:scale-[0.98]">
                        {i18n.createButton}
                    </button>
                )
            )}

            {!allowed && (
                <button disabled className="w-full py-4 rounded-2xl bg-cyan-600 opacity-40 cursor-not-allowed text-sm font-black uppercase tracking-widest text-white">
                    {i18n.createButton}
                </button>
            )}

            {allowed && (
                <div className="overflow-x-auto">
                    {tokens.length === 0 ? (
                        <p className="text-xs text-gray-500 text-center py-4">{i18n.empty}</p>
                    ) : (
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-white/5">
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.name}</th>
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.prefix}</th>
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.created}</th>
                                    <th className="py-3 pr-4 text-[10px] font-black uppercase tracking-widest text-gray-600">{i18n.columns.lastUsed}</th>
                                    <th className="py-3"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {tokens.map((token) => (
                                    <tr key={token.id} className="border-b border-white/5 last:border-0">
                                        <td className="py-3 pr-4 text-sm font-bold text-white">{token.name}</td>
                                        <td className="py-3 pr-4"><code className="px-2 py-1 rounded-lg bg-white/5 text-xs font-mono text-cyan-300">{token.prefix}</code></td>
                                        <td className="py-3 pr-4 text-xs text-gray-400">{formatDate(token.created_at)}</td>
                                        <td className="py-3 pr-4 text-xs text-gray-400">{formatDate(token.last_used_at)}</td>
                                        <td className="py-3 text-right">
                                            {pendingRevoke === token.id ? (
                                                <div className="flex flex-col items-end gap-2">
                                                    <span className="text-[10px] text-red-400">{i18n.revokeConfirm}</span>
                                                    <div className="flex gap-2">
                                                        <button data-testid="confirm-revoke" onClick={() => handleRevoke(token.id)} disabled={busy} className="px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 text-[10px] font-black uppercase tracking-widest">
                                                            {i18n.revoke}
                                                        </button>
                                                        <button onClick={() => setPendingRevoke(null)} className="px-3 py-1.5 rounded-lg bg-white/5 text-white text-[10px] font-black uppercase tracking-widest">
                                                            {i18n.cancel}
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <button onClick={() => setPendingRevoke(token.id)} className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-black uppercase tracking-widest">
                                                    {i18n.revoke}
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </section>
    )
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pnpm test:run src/features/integrations/ApiTokensSection.test.tsx`
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/integrations/ApiTokensSection.tsx frontend/src/features/integrations/ApiTokensSection.test.tsx
git commit -m "feat(frontend): add ApiTokensSection for integration tokens"
```

---

### Task 10: Mount the section in the profile page and verify the build

**Files:**
- Modify: `frontend/src/features/auth/ProfileComponent.tsx:10,171`

- [ ] **Step 1: Import the component**

After line 10 (`import { DashboardHeader } ...`) add:

```tsx
import { ApiTokensSection } from '@/features/integrations/ApiTokensSection'
```

- [ ] **Step 2: Mount it**

Inside `<div className="p-10 max-w-4xl mx-auto space-y-10">`, after the closing `</div>` of the `grid grid-cols-1 md:grid-cols-2 gap-8` block (currently line ~171) and before the container's closing `</div>`, add:

```tsx
                    <ApiTokensSection plan={user?.subscription_plan} />
```

- [ ] **Step 3: Type-check, lint and run the full frontend suite**

Run (from `frontend/`): `pnpm lint && npx tsc --noEmit && pnpm test:run`
Expected: no lint errors, no type errors, all tests pass (compare against the known baseline failures if any).

- [ ] **Step 4: Run the full backend suite**

Run (from repo root): `python -m pytest backend/tests -q`
Expected: only pre-existing baseline failures (see memory `preexisting-test-failures`); all tests added in this plan pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/auth/ProfileComponent.tsx
git commit -m "feat(frontend): show integration tokens section in profile"
```

- [ ] **Step 6: Manual smoke test (if a local stack is available)**

```bash
docker-compose up -d --build
cd backend && alembic upgrade head
```

1. Log in to the dashboard, open Perfil, create a token, copy it.
2. `curl -H "Authorization: Bearer asf_..." http://localhost:8000/api/v1/ajax/hubs` returns the hub list.
3. Revoke the token in the dashboard; the same curl returns 401.

---

## Self-review

- **Spec coverage:** 4.1 tokens → Tasks 1-4; 4.2 schemas → Task 5; 4.3/4.4 docs → Task 6; 5 frontend → Tasks 7-10; 7 error table (backend rows) → Tasks 3-4; 8 backend/frontend tests → each task. Sections 6 and the HA rows of 7/8 belong to the second plan (`2026-09-18-ha-integration-hass.md`).
- **Type consistency:** `create_api_token(db, user_id, name, expires_in_days) -> (ApiToken, str)`, `revoke_api_token(db, user_id, token_id) -> bool`, `authenticate_api_token(db, raw_token) -> Optional[User]` are used with the same signatures in Tasks 2, 3 and 4. Frontend `apiTokenService.{list, create, revoke}` match between Tasks 8 and 9.
- **Verified against the codebase:** `apiClient.delete` exists; `mock_user_subscription` / `mock_user_no_subscription` / `mock_db` fixtures exist in `backend/tests/conftest.py`; `/api/v1/security/audit-logs` only depends on `get_current_user` and `get_db`.
