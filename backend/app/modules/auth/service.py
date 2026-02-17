import logging
import hashlib
import uuid
from datetime import datetime as dt_datetime, timezone
from typing import Annotated, Optional, List

import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, get_client_ip
from backend.app.modules.auth.models import User
from backend.app.modules.auth.schemas import UserCreate
from backend.app.modules.security import service as security_service
from backend.app.modules.notifications import service as notification_service
from backend.app.shared.infrastructure.database.session import get_db
from backend.app.shared.infrastructure.redis.deps import get_redis

logger = logging.getLogger(__name__)

# Security Schemes
oauth2_scheme = APIKeyHeader(name="Authorization", scheme_name="JWT Token", description="Enter: Bearer <your_token>", auto_error=False)

# --- CRUD Operations ---

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    return await db.get(User, user_id)

async def create_user(db: AsyncSession, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_stripe_customer_id(db: AsyncSession, customer_id: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.stripe_customer_id == customer_id))
    return result.scalars().one_or_none()

async def update_user_subscription(
    db: AsyncSession, 
    user_id: int, 
    status: str, 
    plan: str, 
    subscription_id: str = "",
    expires_at: Optional[dt_datetime] = None
) -> bool:
    user = await db.get(User, user_id)
    if not user:
        return False
    user.subscription_status = status
    user.subscription_plan = plan
    user.subscription_id = subscription_id
    if expires_at:
        user.subscription_expires_at = expires_at
    await db.commit()
    return True

# --- Auth Dependencies & Logic ---

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None, 
) -> User:
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
        token_type: str = payload.get("type")
        user_email: str = payload.get("sub")
        jti: str = payload.get("jti")
        uah: str = payload.get("uah")
        uip: str = payload.get("uip")
        
        if user_email is None or token_type != "access":
             raise HTTPException(status_code=401, detail="Invalid credentials")
             
        # Fingerprint Verification
        current_ua = request.headers.get("user-agent", "")
        current_uah = hashlib.sha256(current_ua.encode()).hexdigest()
        if uah and uah != current_uah:
             await security_service.log_request_action(
                 db=db, request=request, user_id=None,
                 action="SECURITY_ALERT_UA_MISMATCH", status_code=401,
                 severity="CRITICAL", payload={"email": user_email}
             )
             raise HTTPException(status_code=401, detail="Invalid credentials")

        # IP Shift Logging
        current_ip = get_client_ip(request)
        
        if uip and current_ip and uip != current_ip:
             await security_service.log_request_action(
                 db=db, request=request, user_id=None,
                 action="SECURITY_INFO_IP_SHIFT", status_code=200,
                 severity="WARNING", payload={"original_ip": uip, "current_ip": current_ip, "email": user_email}
             )

        # JTI Revocation Check 
        if jti:
            is_revoked = await redis_client.exists(f"token_blacklist:{jti}")
            if is_revoked:
                 raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = await get_user_by_email(db, email=user_email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Notify on Security Events (IP Shift)
    if uip and current_ip and uip != current_ip:
         await notification_service.create_notification(
             db=db,
             user_id=user.id,
             title="Nueva IP detectada",
             message=f"Se ha detectado un cambio de ubicación (IP: {current_ip}). Si no has sido tú, revisa tu seguridad.",
             notification_type="warning"
         )

    return user

async def check_admin(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.email not in settings.ADMIN_EMAILS:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="You do not have administrative privileges."
         )

    if settings.ADMIN_SECRET_KEY:
        admin_secret = request.headers.get("X-Admin-Secret")
        if not admin_secret or admin_secret != settings.ADMIN_SECRET_KEY.get_secret_value():
             await security_service.log_request_action(
                 db=db, request=request, user_id=current_user.id,
                 action="SECURITY_ALERT_ADMIN_KEY_FAILED", status_code=403,
                 severity="CRITICAL", payload={"email": current_user.email}
             )
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail="Administrative master key missing or invalid."
             )
    
    return current_user
