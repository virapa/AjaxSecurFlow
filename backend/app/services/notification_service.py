from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import Notification
from typing import List, Optional

async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    link: Optional[str] = None
) -> Notification:
    """
    Creates a new in-app notification for a user.

    Args:
        db: Async database session.
        user_id: ID of the user to notify.
        title: Short title for the notification.
        message: Detailed message content.
        notification_type: Category (info, warning, success, error, security).
        link: Optional destination URL for the user.

    Returns:
        Notification: The created notification object.
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        link=link
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

async def get_user_notifications(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    unread_only: bool = False
) -> List[Notification]:
    """
    Retrieves notifications for a specific user, sorted by most recent.

    Args:
        db: Async database session.
        user_id: ID of the user.
        limit: Maximum number of notifications to return.
        unread_only: If true, filters out read notifications.

    Returns:
        List[Notification]: List of notification objects.
    """
    stmt = select(Notification).where(Notification.user_id == user_id)
    
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)
        
    stmt = stmt.order_by(desc(Notification.created_at)).limit(limit)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def mark_as_read(db: AsyncSession, user_id: int, notification_id: int) -> bool:
    """
    Marks a specific notification as read.

    Args:
        db: Async database session.
        user_id: ID of the owner user.
        notification_id: ID of the notification to update.

    Returns:
        bool: True if a row was updated, False otherwise.
    """
    stmt = update(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).values(is_read=True)
    
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def mark_all_as_read(db: AsyncSession, user_id: int) -> int:
    """
    Marks all notifications for a user as read.

    Args:
        db: Async database session.
        user_id: ID of the user.

    Returns:
        int: Number of rows updated.
    """
    stmt = update(Notification).where(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).values(is_read=True)
    
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount

async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    """
    Returns the count of unread notifications for a user.

    Args:
        db: Async database session.
        user_id: ID of the user.

    Returns:
        int: Total unread notifications count.
    """
    from sqlalchemy import func
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read == False
    )
    result = await db.execute(stmt)
    return result.scalar() or 0
