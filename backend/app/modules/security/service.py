from typing import Optional
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.modules.security.models import AuditLog

# Configuration for Lockout (Can move to settings later)
FAILED_LOGIN_LIMIT = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes

async def log_action(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    endpoint: str,
    status_code: int,
    method: str = "GET",
    payload: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    severity: str = "INFO",
    resource_id: Optional[str] = None,
    latency_ms: Optional[int] = None,
    correlation_id: Optional[str] = None
):
    """
    Creates an enriched audit log entry.
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
        severity=severity,
        resource_id=resource_id,
        latency_ms=latency_ms,
        correlation_id=correlation_id
    )
    db.add(audit_log)
    await db.commit()

async def log_request_action(
    db: AsyncSession,
    request: Request,
    user_id: Optional[int],
    action: str,
    status_code: int,
    severity: str = "INFO",
    resource_id: Optional[str] = None,
    payload: Optional[dict] = None,
    latency_ms: Optional[int] = None,
    correlation_id: Optional[str] = None
):
    """
    Helper to log actions using data extracted from a FastAPI Request object.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.headers.get("x-real-ip") or (request.client.host if request.client else None)

    await log_action(
        db=db,
        user_id=user_id,
        action=action,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=status_code,
        payload=payload,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
        severity=severity,
        resource_id=resource_id,
        latency_ms=latency_ms,
        correlation_id=correlation_id
    )

# Security Logic (IP Lockout)
async def check_ip_lockout(ip_address: str, redis_client: Redis) -> bool:
    if not ip_address:
        return False
    is_locked = await redis_client.exists(f"lockout:{ip_address}")
    return bool(is_locked)

async def track_login_failure(ip_address: str, redis_client: Redis) -> int:
    if not ip_address:
        return 0
    key = f"failed_attempts:{ip_address}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 86400)
    if count >= FAILED_LOGIN_LIMIT:
        await redis_client.set(f"lockout:{ip_address}", "1", ex=LOCKOUT_DURATION_SECONDS)
        await redis_client.delete(key)
    return count

async def reset_login_failures(ip_address: str, redis_client: Redis):
    if not ip_address:
        return
    await redis_client.delete(f"failed_attempts:{ip_address}")
# Legacy Aliases
create_audit_log = log_action
