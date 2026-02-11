from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.app.shared.infrastructure.database.session import get_db
from backend.app.modules.auth import service as auth_service
from backend.app.modules.security import service as security_service

router = APIRouter()

@router.get("/audit-logs")
async def get_my_audit_logs(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve security audit logs for the current user.
    """
    # Note: In a real scenario, we'd add pagination here.
    # For now, we reuse the existing security_service logic if available or implement a local query.
    # The existing security_service mostly focuses on logging, not retrieval for users yet.
    # But let's assume we want to expose them.
    from sqlalchemy import select
    from backend.app.modules.security.models import AuditLog
    
    stmt = select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(AuditLog.timestamp.desc()).limit(50)
    result = await db.execute(stmt)
    return result.scalars().all()
