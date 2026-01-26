from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import AuditLog

async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    endpoint: str,
    status_code: int,
    payload: dict = None
):
    """
    Creates an audit log entry.
    """
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        endpoint=endpoint,
        status_code=status_code,
        payload=payload,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log_entry)
    await db.commit()
