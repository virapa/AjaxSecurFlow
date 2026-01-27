from datetime import datetime, timezone, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt 
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import create_access_token
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core import crud_user
from backend.app.domain.models import User
from backend.app.services.ajax_client import AjaxClient, AjaxAuthError
from backend.app.services import audit_service, security_service

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

import hashlib
import uuid
from backend.app.services.rate_limiter import get_redis

async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: AsyncSession = Depends(get_db)
):
    """
    Validate the JWT token and retrieve the current authenticated user.
    Now includes JTI and Fingerprint (uah) verification.

    Args:
        request: FastAPI Request object for contextual validation.
        token: The bearer JWT token from the Authorization header.
        db: Async database session.

    Returns:
        User: The database user object if the token is valid.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or fingerprint doesn't match.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        jti: str = payload.get("jti")
        uah: str = payload.get("uah")
        uip: str = payload.get("uip")
        
        if user_email is None:
             raise HTTPException(status_code=401, detail="Invalid credentials")
             
        # 1. Fingerprint Verification (Fixed Context)
        current_ua = request.headers.get("user-agent", "")
        current_uah = hashlib.sha256(current_ua.encode()).hexdigest()
        if uah and uah != current_uah:
             from backend.app.services import audit_service
             await audit_service.log_request_action(
                 db=db, request=request, user_id=None,
                 action="SECURITY_ALERT_UA_MISMATCH", status_code=401,
                 severity="CRITICAL", payload={"email": user_email}
             )
             raise HTTPException(status_code=401, detail="Security context mismatch")

        # 2. IP Shift Logging (Flexible Context - Do NOT block)
        forwarded = request.headers.get("x-forwarded-for")
        current_ip = forwarded.split(",")[0].strip() if forwarded else (request.headers.get("x-real-ip") or (request.client.host if request.client else None))
        
        if uip and current_ip and uip != current_ip:
             from backend.app.services import audit_service
             await audit_service.log_request_action(
                 db=db, request=request, user_id=None,
                 action="SECURITY_INFO_IP_SHIFT", status_code=200,
                 severity="WARNING", payload={"original_ip": uip, "current_ip": current_ip, "email": user_email}
             )

        # 3. JTI Revocation Check 
        if jti:
            redis_client = await get_redis()
            is_revoked = await redis_client.exists(f"token_blacklist:{jti}")
            if is_revoked:
                 raise HTTPException(status_code=401, detail="Token has been revoked")
        
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = await crud_user.get_user_by_email(db, email=user_email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/token")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Unified login: Verify email/password against Ajax Systems.
    Includes Brute-Force Protection (Fail2Ban) and Session Fingerprinting.
    """
    # 0. Extract Client IP (Proxy-Aware)
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.headers.get("x-real-ip") or (request.client.host if request.client else None))

    # 1. Check if IP is locked out
    if await security_service.check_ip_lockout(client_ip):
        await audit_service.log_request_action(
            db=db, request=request, user_id=None,
            action="SECURITY_ALERT_LOGIN_LOCKED", status_code=403, 
            severity="CRITICAL", payload={"ip": client_ip, "email": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your IP is temporarily locked due to multiple failed login attempts. Try again in 15 minutes."
        )

    ajax = AjaxClient()
    try:
        # 2. Verify credentials directly with Ajax API
        ajax_data = await ajax.login_with_credentials(
            email=form_data.username, 
            password_raw=form_data.password
        )
        
        # 3. Get or create user in local database
        user = await crud_user.get_user_by_email(db, email=form_data.username)
        if not user:
            # Auto-provision user if they exist in Ajax but not in our DB
            from backend.app.schemas.user import UserCreate
            user_in = UserCreate(
                email=form_data.username,
                full_name=form_data.username.split("@")[0],
                password=form_data.password 
            )
            user = await crud_user.create_user(db, user_in=user_in)
        
        # 4. Success Tasks
        await security_service.reset_login_failures(client_ip)
        
        # Generate Security Context (JTI, UAH, UIP)
        jti = str(uuid.uuid4())
        user_agent = request.headers.get("user-agent", "")
        uah = hashlib.sha256(user_agent.encode()).hexdigest()

        # Audit: Successful Login
        await audit_service.log_request_action(
            db=db, request=request, user_id=user.id,
            action="LOGIN_SUCCESS", status_code=200, severity="INFO"
        )
        
        # 5. Generate our system's Access Token
        access_token = create_access_token(
            subject=user.email,
            jti=jti,
            uah=uah,
            uip=client_ip
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except AjaxAuthError:
        # 6. Failure Tracking (Fail2Ban logic)
        await security_service.track_login_failure(client_ip)
        
        # Audit: Failed Login
        await audit_service.log_request_action(
            db=db, request=request, user_id=None,
            action="LOGIN_FAILED", status_code=401, severity="WARNING",
            payload={"email": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Ajax email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke the current JWT access token using its JTI.
    """
    try:
        # We decode without verification just to get the JTI and exp
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti and exp:
            redis_client = await get_redis()
            # Calculate TTL for the blacklist entry
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - now)
            if ttl > 0:
                await redis_client.set(f"token_blacklist:{jti}", "1", ex=ttl)
        
        return {"detail": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token for logout")
