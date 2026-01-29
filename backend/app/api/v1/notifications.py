from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.db import get_db
from backend.app.api.v1.auth import get_current_user
from backend.app.domain.models import User
from backend.app.services import notification_service
from backend.app.schemas.notification import NotificationRead, NotificationSummary
from typing import List

router = APIRouter()

@router.get("/", response_model=List[NotificationRead])
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationRead]:
    """
    Get user notifications (latest first).

    Args:
        unread_only: If true, filters out read notifications.
        limit: Page size (1-100).
        current_user: Automatically injected authenticated user.
        db: Async database session.

    Returns:
        List[NotificationRead]: List of notifications.
    """
    return await notification_service.get_user_notifications(
        db, current_user.id, limit=limit, unread_only=unread_only
    )

@router.get("/summary", response_model=NotificationSummary)
async def get_notifications_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationSummary:
    """
    Get unread count and the 5 most recent notifications.
    
    Useful for a dashboard header or sidebar to show status at a glance.

    Args:
        current_user: Automatically injected authenticated user.
        db: Async database session.

    Returns:
        NotificationSummary: Summary including unread count and recent items.
    """
    count = await notification_service.get_unread_count(db, current_user.id)
    latest = await notification_service.get_user_notifications(db, current_user.id, limit=5)
    return {"unread_count": count, "notifications": latest}

@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Mark a specific notification as read.

    Args:
        notification_id: ID of the notification to update.
        current_user: Automatically injected authenticated user.
        db: Async database session.

    Returns:
        dict: Success status.

    Raises:
        HTTPException: 404 if the notification is not found for this user.
    """
    success = await notification_service.mark_as_read(db, current_user.id, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}

@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Mark all unread notifications as read for the current user.

    Args:
        current_user: Automatically injected authenticated user.
        db: Async database session.

    Returns:
        dict: Success status and the number of notifications updated.
    """
    count = await notification_service.mark_all_as_read(db, current_user.id)
    return {"status": "success", "marked_read": count}
