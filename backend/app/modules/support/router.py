import html
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from redis.asyncio import Redis

from backend.app.core.config import settings
from backend.app.shared.infrastructure.redis.deps import get_redis
from backend.app.modules.auth import service as auth_service
from backend.app.modules.support.schemas import SupportRequest
from backend.app.modules.notifications import service as notification_service
email_service = notification_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/contact")
async def send_support_request(
    request: SupportRequest,
    background_tasks: BackgroundTasks,
    current_user: auth_service.User = Depends(auth_service.get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    Handle support requests with rate limiting and email notification.
    """
    # Rate Limiting: 5 requests per hour
    rate_limit_key = f"rate_limit:support:{current_user.id}"
    current_count = await redis.get(rate_limit_key)
    
    if current_count and int(current_count) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail="Too many support requests. Please try again in an hour."
        )
    
    await redis.incr(rate_limit_key)
    await redis.expire(rate_limit_key, 3600)

    if not settings.SMTP_HOST:
        raise HTTPException(status_code=503, detail="Email service not configured")

    # Notify Admins
    safe_subject = html.escape(request.subject)
    safe_message = html.escape(request.message)
    
    admin_body = f"""
    <h2>New Support Request</h2>
    <p><b>User:</b> {current_user.email}</p>
    <p><b>Category:</b> {request.category}</p>
    <hr>
    <p><b>Message:</b></p>
    <p>{safe_message}</p>
    """
    
    for admin_email in settings.ADMIN_EMAILS:
        background_tasks.add_task(
            notification_service.send_email,
            to_email=admin_email,
            subject=f"[SUPPORT] {request.category.upper()}: {safe_subject}",
            body_html=admin_body
        )

    # Confirmation to User
    if request.email_confirmation:
        background_tasks.add_task(
            notification_service.send_email,
            to_email=current_user.email,
            subject=f"Confirmación de Soporte: {safe_subject}",
            body_html=f"<p>Hemos recibido tu solicitud: <b>{safe_subject}</b>. Te daremos respuesta a la brevedad.</p>"
        )

    return {"status": "success", "message": "Support request sent"}
