import sys
import os

# Add the project root to sys.path to allow importing backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.modules.notifications.service import send_email
from backend.app.core.config import settings

def test_smtp_connection():
    print("--- SMTP Configuration Test ---")
    print(f"Host: {settings.SMTP_HOST}")
    print(f"Port: {settings.SMTP_PORT}")
    print(f"User: {settings.SMTP_USER}")
    print(f"From: {settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>")
    print(f"TLS: {settings.SMTP_TLS}")
    
    if not settings.SMTP_HOST:
        print("\nERROR: SMTP_HOST is not configured in .env")
        return

    test_recipient = input("\nEnter recipient email address for the test: ")
    
    print(f"\nSending test email to {test_recipient}...")
    
    success = send_email(
        to_email=test_recipient,
        subject="AjaxSecurFlow - SMTP Test Connection",
        body_html="<h1>SMTP Test</h1><p>If you are reading this, your SMTP configuration in AjaxSecurFlow's <b>.env</b> is working correctly.</p>",
        body_text="SMTP Test: If you are reading this, your SMTP configuration is working."
    )
    
    if success:
        print("\nSUCCESS: Email sent successfully! Check your inbox.")
    else:
        print("\nFAILURE: Failed to send email. Check the application logs for details.")

if __name__ == "__main__":
    test_smtp_connection()
