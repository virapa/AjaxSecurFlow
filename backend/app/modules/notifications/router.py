from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.app.shared.infrastructure.database.session import get_db
from backend.app.modules.auth import service as auth_service
from backend.app.modules.notifications import service as notification_service
from backend.app.modules.notifications.schemas import NotificationRead, NotificationSummary

router = APIRouter()

@router.get("/summary", response_model=NotificationSummary)
async def get_notifications_summary(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a summary of unread count and latest notifications.
    """
    unread_count = await notification_service.get_unread_count(db, current_user.id)
    notifications = await notification_service.get_latest_notifications(db, current_user.id, limit=20)
    return {
        "unread_count": unread_count,
        "notifications": notifications
    }

@router.get("", response_model=List[NotificationRead])
async def list_notifications(
    limit: int = 50,
    unread_only: bool = False,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List historical notifications for the user.
    """
    return await notification_service.get_latest_notifications(db, current_user.id, limit=limit, unread_only=unread_only)

@router.patch("/{notification_id}/read", response_model=NotificationRead)
@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a specific notification as read.
    """
    notification = await notification_service.mark_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/mark-all-read")
@router.post("/read-all")
async def mark_all_read(
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications as read for the current user.
    """
    await notification_service.mark_all_read(db, current_user.id)
    return {"detail": "All notifications marked as read"}
