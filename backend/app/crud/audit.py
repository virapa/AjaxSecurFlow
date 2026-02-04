from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import AuditLog

async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    endpoint: str,
    method: str,
    status_code: int,
    payload: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    severity: str = "INFO",
    resource_id: Optional[str] = None,
    latency_ms: Optional[int] = None,
    correlation_id: Optional[str] = None
) -> AuditLog:
    """Create a new audit log entry."""
    db_obj = AuditLog(
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
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
