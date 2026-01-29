# Sistema de Notificaciones In-App y Centro de Comunicaciones

He implementado un sistema robusto de notificaciones y alertas proactivas tanto dentro del dashboard como vía email. Este sistema asegura que el usuario esté siempre informado sobre su seguridad, facturación y estado de cuenta.

## Características de Notificaciones

### 1. In-App Notifications (Dashboard)
Los nuevos endpoints permiten gestionar alertas en tiempo real:
- **`GET /api/v1/notifications/`**: Listado de todas las notificaciones con soporte para filtrado (solo no leídas) y paginación.
- **`GET /api/v1/notifications/summary`**: Diseñado para el encabezado del dashboard. Devuelve el contador de mensajes no leídos y los 5 más recientes.
- **`PATCH /api/v1/notifications/{id}/read`**: Permite al usuario marcar alertas individuales como leídas.
- **`POST /api/v1/notifications/mark-all-read`**: Acción masiva para limpiar la bandeja de entrada.

### 2. Tipos de Alerta y Severidad
El sistema categoriza los mensajes para una mejor experiencia visual:
- **SUCCESS**: Confirmaciones (ej: "Suscripción Activada", "Voucher Canjeado").
- **INFO**: Mensajes del sistema o actualizaciones menores.
- **WARNING**: Alertas preventivas (ej: "Suscripción Cancelada", "Cambio de IP detectado").
- **ERROR / SECURITY**: Alertas críticas (ej: "Fallo en el Pago", "Nueva ubicación detectada").

---

## Centro de Comunicaciones (Emails Transaccionales)
Se ha integrado un servicio de email asíncrono gestionado por **Celery + SMTP**:

### 1. Sistema de Envío Robusto
- **Multi-part Emails**: Los correos se envían en formato HTML enriquecido con un fallback de texto plano para máxima compatibilidad.
- **Background Processing**: El envío no bloquea la API; se delega a trabajadores especializados para una respuesta instantánea al usuario.

### 2. Automatización por Eventos de Stripe
El sistema ahora envía correos profesionales automáticamente en los siguientes casos:
- **Bienvenida**: Tras la activación exitosa de una suscripción Premium.
- **Renovación**: Confirmación de que el pago mensual ha sido procesado.
- **Cancelación**: Correo de despedida con información sobre la retención de datos.
- **Alertas de Pago**: Notificación crítica cuando Stripe no puede procesar un cargo, instando al usuario a actualizar su tarjeta.

---

## Seguridad Proactiva
- **Detección de IP**: Si un usuario inicia sesión o realiza acciones desde una dirección IP diferente a la habitual en su sesión actual, el sistema genera automáticamente una notificación de seguridad para avisar de un posible acceso no autorizado.

## Verificación de Calidad
- **Tests Integrados**: Se ha añadido `test_notifications.py` que valida el flujo completo de lectura y resumen de alertas.
- **SMTP Diagnostics**: Incluido script `scripts/test_smtp.py` para validar la conexión con el proveedor de correo una vez configurado el `.env`.
- **Q&A Compliance**: Todo el código de notificaciones cumple con el estándar de Docstrings Google y Tipado Estricto de Python.
