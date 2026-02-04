from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.crud import audit as crud_audit

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
    Creates an enriched audit log entry via CRUD.
    """
    await crud_audit.create_audit_log(
        db=db,
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
    Includes Proxy-Aware IP detection (X-Forwarded-For).
    """
    # Industry standard for getting real client IP behind proxies
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For can be a list: "client, proxy1, proxy2"
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
