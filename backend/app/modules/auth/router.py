import logging
import hashlib
import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, create_refresh_token
from backend.app.modules.ajax.service import AjaxClient, AjaxAuthError
from backend.app.shared.infrastructure.database.session import get_db
from backend.app.shared.infrastructure.redis.deps import get_redis
from backend.app.shared.infrastructure.ajax.deps import get_ajax_client
from backend.app.modules.auth import service as auth_service
from backend.app.modules.auth.schemas import Token, TokenRefreshRequest, LoginResponse, LoginRequest, ErrorMessage, UserReadMe, UserRead, UserCreate
from backend.app.modules.security import service as security_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/token", 
    response_model=Token,
    responses={
        401: {"model": ErrorMessage, "description": "Invalid Ajax credentials"},
        403: {"model": ErrorMessage, "description": "IP Locked due to brute-force protection"},
    },
    summary="Login with Ajax Credentials"
)
async def login_for_access_token(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    ajax: AjaxClient = Depends(get_ajax_client)
):
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.headers.get("x-real-ip") or (request.client.host if request.client else None))

    if await security_service.check_ip_lockout(client_ip, redis):
        await security_service.log_request_action(
            db=db, request=request, user_id=None,
            action="SECURITY_ALERT_LOGIN_LOCKED", status_code=403, 
            severity="CRITICAL", payload={"ip": client_ip, "email": body.username}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your IP is temporarily locked due to multiple failed login attempts. Try again in 15 minutes."
        )

    try:
        ajax_data = await ajax.login_with_credentials(
            email=body.username, 
            password_raw=body.password
        )
        
        user = await auth_service.get_user_by_email(db, email=body.username)
        if not user:
            user = await auth_service.create_user(db, email=body.username, password=body.password)
        
        await security_service.reset_login_failures(client_ip, redis)
        
        jti = str(uuid.uuid4())
        user_agent = request.headers.get("user-agent", "")
        uah = hashlib.sha256(user_agent.encode()).hexdigest()

        await security_service.log_request_action(
            db=db, request=request, user_id=user.id,
            action="LOGIN_SUCCESS", status_code=200, severity="INFO"
        )
        
        access_token = create_access_token(
            subject=user.email,
            jti=jti,
            uah=uah,
            uip=client_ip
        )
        
        refresh_jti = str(uuid.uuid4())
        refresh_token = create_refresh_token(
            subject=user.email,
            jti=refresh_jti
        )
        
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "userId": ajax_data.get("userId")
        }

    except AjaxAuthError:
        await security_service.track_login_failure(client_ip, redis)
        await security_service.log_request_action(
            db=db, request=request, user_id=None,
            action="LOGIN_FAILED", status_code=401, severity="WARNING",
            payload={"email": body.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Ajax email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post(
    "/refresh", 
    response_model=Token,
    summary="Refresh Session"
)
async def refresh_token(
    request: Request,
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    ajax: AjaxClient = Depends(get_ajax_client)
):
    try:
        payload = jwt.decode(
            body.refresh_token, 
            settings.SECRET_KEY.get_secret_value(), 
            algorithms=[settings.ALGORITHM]
        )
        user_email: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")
        exp = payload.get("exp")
        
        if user_email is None or token_type != "refresh" or jti is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        is_revoked = await redis_client.exists(f"token_blacklist:{jti}")
        if is_revoked:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        from datetime import datetime as dt_datetime, timezone
        now = dt_datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now)
        if ttl > 0:
            await redis_client.set(f"token_blacklist:{jti}", "1", ex=ttl)
            
        user = await auth_service.get_user_by_email(db, email=user_email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        new_jti = str(uuid.uuid4())
        new_refresh_jti = str(uuid.uuid4())
        user_agent = request.headers.get("user-agent", "")
        uah = hashlib.sha256(user_agent.encode()).hexdigest()
        
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.headers.get("x-real-ip") or (request.client.host if request.client else None))

        access_token = create_access_token(
            subject=user.email,
            jti=new_jti,
            uah=uah,
            uip=client_ip
        )
        refresh_token = create_refresh_token(
            subject=user.email,
            jti=new_refresh_jti
        )
        
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "userId": await ajax._get_ajax_user_id(user.email)
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(auth_service.oauth2_scheme)],
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    redis_client: Redis = Depends(get_redis)
):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
             from datetime import datetime as dt_datetime, timezone
             now = dt_datetime.now(timezone.utc).timestamp()
             ttl = int(exp - now)
             if ttl > 0:
                 await redis_client.set(f"token_blacklist:{jti}", "1", ex=ttl)
        return {"detail": "Successfully logged out"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
@router.get("/me", response_model=UserReadMe)
async def read_users_me(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    ajax: AjaxClient = Depends(get_ajax_client)
):
    from backend.app.modules.billing import service as billing_service
    ajax_profile = None
    try:
        ajax_profile = await ajax.get_user_info(current_user.email)
    except Exception as e:
        logger.warning(f"Could not fetch Ajax profile for {current_user.email}: {e}")

    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "subscription_plan": current_user.subscription_plan,
        "subscription_status": current_user.subscription_status,
        "subscription_expires_at": current_user.subscription_expires_at,
        "subscription_active": billing_service.is_subscription_active(current_user),
        "billing_status": current_user.subscription_status or "inactive",
        "ajax_info": ajax_profile
    }
@router.post("/", response_model=UserRead)
async def register_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user (legacy/REST registration).
    In this project, users are also provisioned automatically on Ajax login.
    """
    existing = await auth_service.get_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return await auth_service.create_user(
        db, 
        email=body.email, 
        password=body.password
    )
