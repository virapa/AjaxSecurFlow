import sys
import os

# Añadir el directorio raíz al path para poder importar backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.worker.tasks import send_transactional_email
from backend.app.core.config import settings

def test_email_fixed():
    print(f"--- Probando Configuración SMTP ---")
    print(f"Host: {settings.SMTP_HOST}")
    print(f"Port: {settings.SMTP_PORT}")
    print(f"User: {settings.SMTP_USER}")
    print(f"From: {settings.SMTP_FROM_EMAIL}")
    print(f"-----------------------------------")
    
    destinatario = "ajaxflow@domoopen.es"
    
    print(f"\nEnviando email de prueba a {destinatario}...")
    
    # Llamamos a la tarea directamente
    result = send_transactional_email(
        to_email=destinatario,
        subject="Prueba de Configuración AjaxSecurFlow",
        html_content="<h1>¡Funciona!</h1><p>Si estás leyendo esto, tu configuración SMTP es correcta.</p>",
        text_content="¡Funciona! Tu configuración SMTP es correcta."
    )
    
    if result:
        print("\n✅ ¡Éxito! El email se ha enviado correctamente.")
    else:
        print("\n❌ Error: El envío ha fallado. Revisa los logs.")

if __name__ == "__main__":
    test_email_fixed()
