from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.app.api.v1.auth import get_current_user
from backend.app.domain.models import User
from backend.app.schemas.support import SupportRequest
from backend.app.services import email_service
from backend.app.core.config import settings
from redis.asyncio import Redis
from backend.app.api.deps import get_redis

router = APIRouter()

@router.post("/contact")
async def send_support_request(
    request: SupportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    Handle support requests from the contact form.
    Sends an email to admins and an optional confirmation copy to the user.
    """
    import html
    
    # 0. Rate Limiting (5 requests per hour)
    RATE_LIMIT_KEY = f"rate_limit:support:{current_user.id}"
    current_count = await redis.get(RATE_LIMIT_KEY)
    
    if current_count and int(current_count) >= 5:
        raise HTTPException(
            status_code=429, 
            detail="Too many support requests. Please try again in an hour."
        )
    
    # Increment counter
    pipe = redis.pipeline()
    pipe.incr(RATE_LIMIT_KEY)
    pipe.expire(RATE_LIMIT_KEY, 3600) # 1 hour TTL
    await pipe.execute()

    if not settings.SMTP_HOST:
        raise HTTPException(status_code=503, detail="Email service not configured")

    # 1. Notify Admins (With HTML Escaping)
    safe_subject = html.escape(request.subject)
    safe_message = html.escape(request.message)
    safe_category = html.escape(request.category)

    admin_subject = f"[SUPPORT ALERT] {safe_category.upper()}: {safe_subject}"
    admin_body = f"""
    <h2>New Support Request</h2>
    <p><b>User:</b> {current_user.email}</p>
    <p><b>Category:</b> {safe_category}</p>
    <p><b>Subject:</b> {safe_subject}</p>
    <hr>
    <p><b>Message:</b></p>
    <p>{safe_message}</p>
    """
    
    # Send to all admins
    for admin_email in settings.ADMIN_EMAILS:
        background_tasks.add_task(
            email_service.send_email,
            to_email=admin_email,
            subject=admin_subject,
            body_html=admin_body,
            body_text=f"Support Request from {current_user.email}:\n\nCategory: {request.category}\nSubject: {request.subject}\n\nMessage:\n{request.message}"
        )

    # 2. Confirmation to User
    if request.email_confirmation:
        user_subject = f"Confirmación de Soporte: {safe_subject}"
        user_body = f"""
        <h2>Hola {current_user.email},</h2>
        <p>Hemos recibido tu solicitud de soporte correctamente.</p>
        <p>Nuestro equipo revisará tu mensaje lo antes posible y te daremos una respuesta a la brevedad.</p>
        <hr>
        <p><b>Resumen de tu mensaje:</b></p>
        <p><b>Asunto:</b> {safe_subject}</p>
        <p><b>Mensaje:</b> {safe_message}</p>
        <hr>
        <p>Gracias por confiar en AjaxSecurFlow.</p>
        """
        background_tasks.add_task(
            email_service.send_email,
            to_email=current_user.email,
            subject=user_subject,
            body_html=user_body,
            body_text=f"Hola {current_user.email},\n\nHemos recibido tu solicitud de soporte.\n\nAsunto: {request.subject}\n\nMensaje:\n{request.message}\n\nTe daremos respuesta lo antes posible."
        )

    return {"status": "success", "message": "Support request sent"}
