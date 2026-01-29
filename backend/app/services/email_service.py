import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Sends a transactional email using SMTP settings.
    
    This is a synchronous function intended to be called from Celery workers.
    It supports multi-part (HTML + Plain text) email generation.

    Args:
        to_email: Target recipient email address.
        subject: Email subject line.
        body_html: HTML content of the email.
        body_text: Optional plain text fallback for the email.

    Returns:
        bool: True if the email was successfully sent, False otherwise.
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
