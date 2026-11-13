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
    current_user: auth_service.User = Depends(auth_service.get_current_session_user),
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
    current_user: auth_service.User = Depends(auth_service.get_current_session_user),
    db: AsyncSession = Depends(get_db),
):
    _require_plan(current_user)
    return await api_token_service.list_api_tokens(db, user_id=current_user.id)


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an integration token",
    description="Revoke a token. Any client using it is rejected on its next request. An already-open SSE stream ends when it reconnects.",
)
async def revoke_token(
    token_id: int,
    request: Request,
    current_user: auth_service.User = Depends(auth_service.get_current_session_user),
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
