from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.modules.notifications.models import Notification
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
    """
    stmt = select(Notification).where(
        Notification.user_id == user_id,
        Notification.title == title,
        Notification.message == message,
        Notification.is_read == False
    )
    existing = await db.execute(stmt)
    existing_notification = existing.scalars().first()
    
    if existing_notification:
        return existing_notification

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

async def get_latest_notifications(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    unread_only: bool = False
) -> List[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)
    stmt = stmt.order_by(desc(Notification.created_at)).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def mark_as_read(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    stmt = update(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).values(is_read=True)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    """
    Marks all notifications for a given user as read.
    """
    stmt = update(Notification).where(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).values(is_read=True)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount

async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read == False
    )
    result = await db.execute(stmt)
    return result.scalar() or 0

# --- Email Notifications ---
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Sends a transactional email using SMTP settings.
    """
    if not settings.SMTP_HOST:
        logger.warning(f"SMTP not configured. Skipping email to {to_email}")
        return False

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email

        if body_text:
            part1 = MIMEText(body_text, "plain")
            message.attach(part1)
        
        part2 = MIMEText(body_html, "html")
        message.attach(part2)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(
                    settings.SMTP_USER,
                    settings.SMTP_PASSWORD.get_secret_value()
                )
            
            server.sendmail(
                settings.SMTP_FROM_EMAIL,
                to_email,
                message.as_string()
            )
        
        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False
