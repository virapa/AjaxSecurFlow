# Implementación de Sistema de Vouchers (B2B)

Este plan detalla la arquitectura para permitir la activación de servicios mediante códigos de un solo uso, permitiendo ventas fuera de línea e integraciones con instaladores.

## Cambios Propuestos

### Modelos de Base de Datos
Necesitamos una nueva entidad para gestionar los vales.

#### [NEW] Voucher Model
- `code`: String único (generado aleatoriamente, ej: AJAX-XXXX-XXXX).
- `duration_days`: Duración en días que otorga el código (30, 365).
- `is_redeemed`: Estado del vale.
- `redeemed_by_id`: ID del usuario que lo activó.
- `redeemed_at`: Timestamp de la activación.

---

### Lógica de Negocio (Backend)

#### [NEW] [vouchers.py](file:///c:/Users/rpalacios.SATYATEC/APPs/git-proyects/AjaxSecurFlow/backend/app/services/voucher_service.py)
- `generate_vouchers(count, duration)`: Función administrativa para crear códigos.
- `redeem_voucher(user, code)`: Valida el código, lo marca como usado y extiende la suscripción.

---

### Endpoints de API

#### [NEW] POST `/api/v1/billing/vouchers/redeem`
- **Request**: `{ "code": "AJAX-123" }`
- **Redención**: Verifica validez y actualiza el estado del `User`.

---

## Plan de Verificación

### Pruebas Automatizadas
- [ ] Test de generación de códigos únicos.
- [ ] Test de redención exitosa (extensión de días).
- [ ] Test de prevención de doble uso (double-spend).
- [ ] Test de expiración de códigos no usados.
