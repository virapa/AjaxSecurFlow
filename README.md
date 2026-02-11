# AjaxSecurFlow - Industrial Grade Ajax Systems Proxy

## 1. Descripción General
AjaxSecurFlow es un Proxy API de grado industrial diseñado para intermediar la comunicación entre clientes finales y la API de Ajax Systems. Su objetivo principal es abstraer la complejidad de la integración, gestionar la autenticación de forma segura mediante rotación de tokens y proteger la infraestructura de Ajax aplicando límites de consumo (Rate Limiting) estrictos y personalizados. Este proyecto sirve como base tecnológica para una plataforma SaaS de gestión de seguridad.

## 2. Stack Tecnológico
El proyecto utiliza tecnologías modernas y robustas, siguiendo los estándares de la industria:

- **Lenguaje**: Python 3.11+ (Totalmente Asíncrono)
- **Framework API**: FastAPI (Alto rendimiento, validación automática)
- **Base de Datos**: PostgreSQL 15+ (con SQLAlchemy 2.0 Async para ORM)
- **Caché y Mensajería**: Redis (Gestión de sesiones, Rate Limiting, Celery Broker)
- **Tareas Background**: Celery (Sincronización de datos, procesamiento masivo)
- **Pagos y SaaS**: Stripe SDK (Gestión de suscripciones y webhooks)
- **Gestión de Configuración**: Pydantic V2 & Settings (Validación estricta)
- **Seguridad**: Bcrypt (Hashing moderno), PyJWT (Tokens), SHA256 (Ajax Auth), Endurecimiento de Errores (Opaque Errors)
- **Frontend**: Next.js 16.1.6 (Turbopack), React 19.2.3, TailwindCSS 4
- **Visualización**: Recharts (Gráficos industriales de seguridad)
- **Infraestructura**: Docker & Docker Compose (Contenerización completa)
- **Testing y Calidad**: Pytest (77 tests: 100% Pass), Vitest (45 tests), Bandit (Seguridad), pip-audit (Vulnerabilidades: 0)

## 3. Estructura del Proyecto
El proyecto sigue una arquitectura de **Monolito Modular** estricta, separando la infraestructura compartida de los servicios de dominio vertical:

```text
/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuración global y Settings
│   │   ├── modules/        # Slices Verticales (Auth, Ajax, Billing, Security, etc.)
│   │   ├── shared/         # Infraestructura compartida (DB, Redis, Utils)
│   │   └── worker/         # Tareas Background (Celery)
│   ├── tests/              # Pruebas Unitarias e Integración (Pytest)
├── docker/                 # Orquestación Centralizada
│   ├── docker-compose.yml
│   ├── backend/            # Dockerfile y configuración Backend
│   └── frontend/           # Dockerfile y configuración Frontend
├── frontend/               # Aplicación Next.js 16
├── scripts/                # Utilidades de mantenimiento
└── README.md
```

## 4. Arquitectura del Sistema
El sistema opera bajo un modelo de **Event-Driven Architecture** parcial para procesos críticos:

1.  **API Síncrona (FastAPI)**: Maneja peticiones de alto rendimiento (Proxy, Auth).
2.  **Worker Asíncrono (Celery)**: Procesa tareas pesadas (Sincronización de datos) y críticas/bloqueantes (Webhooks de Stripe).
3.  **Broker & Caché (Redis)**: Actúa como bus de mensajes para Celery y almacén de alta velocidad para Rate Limiting, Sesiones de Ajax y Caching.

### 4.1 Arquitectura de Identidad Unificada (Ajax Auth)
El sistema utiliza a **Ajax Systems** como el proveedor de identidad principal (Identity Provider):
- **Sincronización de Credenciales**: El email y la contraseña usados en la App oficial de Ajax son los mismos para acceder a este dashboard.
- **Auto-Provisioning**: Al realizar el primer login exitoso contra Ajax, el sistema crea automáticamente el perfil del usuario en la base de datos local.
- **Sesiones Multitenant**: Las sesiones de Ajax (`sessionToken` y `userId`) se gestionan de forma aislada en **Redis** usando el email del usuario como namespace (`ajax_user:{email}:token`).
- **Seguridad Pasiva (Zero-Knowledge)**: El sistema nunca almacena contraseñas en texto plano. Se guardan hashes Bcrypt para validación interna. Esto significa que si el token de Ajax es revocado (por cambio de password o cierre manual), el usuario **debe re-autenticarse** manualmente.
- **Ciclo de Vida del Token**:
    - **Session Token**: Auto-renovado cada 15 min.
    - **Refresh Token**: Válido por 7 días. Se rota automáticamente en cada uso, extendiendo la sesión indefinidamente mientras haya actividad semanal.

### 4.2 Telemetría e Interfaz de Control
El sistema expone información detallada y estructurada de todo el ecosistema Ajax:
- **Telemetría**: Información de batería, señal, firmware e IP de hubs y dispositivos.
- **Gestión de Espacios (Rooms)**: Mapeo y visualización de la estructura física del sistema.
- **Perfiles Enriquecidos**: Sincronización automática de datos de usuario (teléfono, idioma, nombre, imagen) desde la API de Ajax.
- **Control de Seguridad**: Interfaz unificada para cambiar estados de armado con flujo de confirmación determinista (1.5s delay de sincronización física).

#### Detalle de Hubs y Dispositivos
- `GET /api/v1/ajax/hubs/{hub_id}`
- `GET /api/v1/ajax/hubs/{hub_id}/devices`
- `GET /api/v1/ajax/hubs/{hub_id}/devices/{device_id}`
- `GET /api/v1/ajax/hubs/{hub_id}/rooms` (Listado completo de habitaciones)
- `GET /api/v1/ajax/hubs/{hub_id}/rooms/{room_id}` (Detalle de habitación específica)
- `GET /api/v1/ajax/hubs/{hub_id}/role` (Consulta de Rol: MASTER/PRO/USER)

#### Control de Seguridad (Armado/Desarmado)
El proxy expone una interfaz unificada para el control de estados:
- **Endpoint**: `POST /api/v1/ajax/hubs/{hub_id}/arm-state`
- **Modos Soportados**: 
    - `0`: **DISARMED** (Desactivar seguridad).
    - `1`: **ARMED** (Armado Total).
    - `2`: **NIGHT_MODE** (Modo Noche/Parcial).
- **Acción por Grupo**: Soporta el parámetro opcional `groupId` para actuar sobre particiones específicas.

### 4.3 Generic Proxy Access (Ruta Dinámica)
El sistema incluye un proxy genérico e inteligente que permite la extensibilidad total del sistema:
- **Endpoint**: `ANY /api/v1/ajax/{path:path}`
- **Propósito**: Actúa como un túnel hacia la API oficial de Ajax. Permite consumir cualquier endpoint (presente o futuro) que no esté mapeado explícitamente en el backend.
- **Inyección Automática**: El proxy gestiona e inyecta automáticamente las credenciales necesarias (`X-Api-Key` y `X-Session-Token`) recuperándolas de Redis.
- **Control Industrial**: Todas las peticiones a través del proxy pasan por:
    - **Validación de Suscripción**: Bloqueo automático si el usuario no tiene un plan activo en Stripe.
    - **Rate Limiting Global**: Protección contra abusos (100 req/min compartidos globalmente).
    - **Caching Inteligente**: Respuestas cacheadas en Redis para reducir llamadas redundantes.
    - **Auditoría**: Registro en la base de datos de cada acción, path y resultado.

### 4.4 Rate Limiting Global
El sistema implementa un **limitador de tasa global** para proteger el límite de la API de Ajax (100 req/min):

- **Contador Único**: Todas las peticiones de todos los usuarios comparten un único contador en Redis.
- **Ventana Deslizante**: El contador se reinicia cada 60 segundos.
- **Cola Asíncrona**: Si el límite se alcanza, las peticiones se encolan (máximo 30s de espera).
- **Fail-Open**: Si Redis no está disponible, las peticiones continúan (resiliencia).
- **Respuesta 503**: Si una petición excede el tiempo de espera, devuelve `Service Temporarily Unavailable` con header `Retry-After`.

### 4.5 Sistema de Caché Redis
Para optimizar el rendimiento y reducir las llamadas a la API de Ajax, el sistema cachea las respuestas:

| Dato | TTL por Defecto | Variable de Entorno |
|------|-----------------|---------------------|
| Lista de Hubs | 30 min | `CACHE_TTL_HUBS` |
| Detalle de Hub | 2 min | `CACHE_TTL_HUB_DETAIL` |
| Lista de Dispositivos | 10 min | `CACHE_TTL_DEVICES` |
| Detalle de Dispositivo | 30 seg | `CACHE_TTL_DEVICE_DETAIL` |
| Habitaciones | 10 min | `CACHE_TTL_ROOMS` |
| Grupos | 10 min | `CACHE_TTL_GROUPS` |

**Invalidación Automática**:
- Al ejecutar comandos de armar/desarmar, el caché del hub se invalida automáticamente.
- Los logs de eventos **nunca se cachean** para garantizar datos frescos.

### 4.6 Módulo de Soporte y Contacto
El sistema incluye un canal de comunicación seguro y auditado para asistencia técnica:
- **Endpoint**: `POST /api/v1/support/contact`.
- **Flujo de Comunicación**:
    - **Admins**: Reciben una alerta inmediata por email con el detalle del problema (Bug, Feedback, Pregunta) y datos de contexto del usuario.
    - **Usuarios**: Reciben un correo de confirmación automático (opcional) con el resumen de su solicitud.
- **Seguridad**:
    - **Protección contra Inyección**: Todo el contenido (Asunto, Mensaje) es sanitizado (`html.escape`) antes de procesarse.
    - **Rate Limiting Estricto**: Limitado a 5 peticiones por hora por usuario para prevenir spam.
    - **Validación de Datos**: Restricciones de longitud para evitar payloads maliciosos.

## 5. Aseguramiento de Calidad (QA) & Seguridad
Este proyecto implementa controles de calidad de grado militar:

-   **Integrity Tests**: Verificación automática de la salud del entorno (`test_system_integrity.py`), validando versiones de librerías y presencia de herramientas de seguridad.
-   **Q&A Policies**: Código 100% documentado con Docstrings (Google format), Tipado estricto (Type Hints) y manejo de errores estandarizado.
-   **Security Scanning**:
    -   `bandit`: Análisis estático para detectar vulnerabilidades en el código Python.
    -   `pip-audit`: Escaneo de dependencias. Actualmente **0 vulnerabilidades detectadas**.
-   **Modern Hashing**: Uso de `bcrypt` (v4.0+) nativo.
-   **Hardened Input Validation**:
    -   **HTML Injection Protection**: Sanitización automática de inputs en formularios de soporte.
    -   **Constraints**: Validación estricta de longitud y tipo de datos en todos los esquemas Pydantic.

### Seguridad de Grado Industrial (Security by Design)
El sistema implementa capas de defensa activa para proteger las sesiones de usuario:
- **JWT Fingerprinting (UA Hash)**: El token está vinculado al `User-Agent` del cliente que inició sesión. Si el token es robado y usado desde otro navegador, es rechazado inmediatamente.
- **Full-Stack Request Shield (Phase 9)**: Capa de defensa proactiva en Next.js (Edge) y FastAPI (Middleware) que bloquea ráfagas de escaneo automatizado y probes de vulnerabilidades (`.php`, `.asp`, `.env`, path traversal) con un **403 Forbidden** inmediato.
- **Auditoría VIP**: Registro inmutable que incluye IP, navegador y nivel de severidad (INFO, WARNING, CRITICAL) para cada acción.
- **Mensajes de Error Opacos (Hardened Auth)**: Todos los fallos de autenticación devuelven un genérico "Invalid credentials", evitando fugas de información sobre la existencia de usuarios o validez de tokens a atacantes.
- **Ofuscación de Upstream**: Los errores de la API de Ajax se filtran para eliminar URLs internas o IDs técnicos, devolviendo mensajes seguros para el cliente final.
- **Auditoría de Secretos (Remediación)**: Eliminación permanente de secretos del historial de Git y neutralización de scripts de diagnóstico mediante el uso estricto de variables de entorno.
- **Escaneo Automático**: Integración de `bandit` y `pip-audit` en el flujo de desarrollo para detectar vulnerabilidades en código y dependencias.
- **Blinded Hybrid Admin Security**: Los endpoints administrativos (Ej: Generación de Vouchers) están protegidos doblemente:
    - **Ghost Admin**: Solo emails en una lista blanca (`ADMIN_EMAILS`) tienen acceso.
    - **Master Key**: Requiere un secreto físico (`X-Admin-Secret`) no almacenado en base de datos.
- **In-App & Email Notifications**: Sistema proactivo de comunicación con el usuario:
    - **Alertas en Dashboard**: Notificaciones de seguridad, facturación y sistema.
    - **Transactional Emails**: Envío asíncrono (Celery + SMTP) para bienvenida, renovaciones y fallos de pago.

## 6. Instalación y Ejecución

### Requisitos Previos
- Docker y Docker Compose instalados.
- Git.

### Instalación
1. Clonar el repositorio:
   ```bash
   git clone <url-repo>
   cd AjaxSecurFlow
   ```

2. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales de Ajax Systems y configuración local
   ```

3. **Modo Desarrollador (Bypass Stripe)**:
   Para desarrollo local sin una cuenta de Stripe activa, puedes activar el bypass en el `.env`:
   ```bash
   ENABLE_DEVELOPER_MODE=True
   ```

### Ejecución
Para iniciar todos los servicios (API, Base de Datos, Redis) desde la raíz del proyecto:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

### Inicialización de Base de Datos
Una vez que los contenedores estén corriendo, aplica las migraciones:

```bash
docker compose -f docker/docker-compose.yml run --rm backend alembic upgrade head
```

### 4.4 Gestión de Planes y Suscripciones (SaaS Logic)
El sistema implementa una lógica de facturación híbrida (Stripe + Vouchers) diseñada para ser transparente y robusta:

- **subscription_plan**: Define el nivel de servicio actual del usuario (`free`, `basic`, `pro`, `premium`).
- **subscription_active**: Booleano de estado final. Indica si el usuario tiene permiso de acceso. Es `true` si el plan de pago está vigente (según Stripe) o si tiene un cupón activo.
- **billing_status**: Estado técnico descriptivo que permite depurar el ciclo de vida del usuario:
    - `active`: Suscripción o Voucher al día.
    - `trialing`: Periodo de prueba.
    - `past_due`: Fallo en el último pago (proporciona un periodo de gracia).
    - `inactive` / `expired`: Acceso revocado (reversión automática a `free` visualmente).

#### Dinámica de Vouchers B2B
Los vouchers (`Voucher`) permiten una activación offline. Al canjear un código `AJAX-XXXX`:
1. El `billing_status` cambia a `active`.
2. El `subscription_plan` se establece en `premium`.
3. El acceso se extiende por la duración del cupón de forma aditiva.
4. Al expirar, una tarea programada (`Celery`) limpia el estado, asegurando que la seguridad del proxy sea siempre coherente con la facturación real.

### Gestión de Sesión Premium (Dual Token)
El sistema implementa una estrategia de **Dual Token** para máxima seguridad y una experiencia de usuario fluida:
1.  **Login (`/auth/token`)**: Al autenticarse, el sistema devuelve un `access_token` (30m) y un `refresh_token` (7d).
2.  **Transparencia**: El backend gestiona automáticamente el refresco de la sesión de Ajax Systems.
3.  **Refreso Local (`/auth/refresh`)**: El dashboard puede usar el `refresh_token` para obtener un nuevo par de tokens sin que el usuario reintroduzca su contraseña.
4.  **Token Rotation**: Por seguridad, cada vez que se usa un refresh token, el anterior se invalida.
5.  **Fingerprinting**: Los tokens están vinculados al `User-Agent` e IP del cliente para prevenir el secuestro de sesiones.

### Documentación de la API
Una vez iniciados los servicios, la documentación interactiva y técnica está disponible en:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (Para pruebas interactivas y manual visual)
- **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (Para referencia técnica detallada)

### Ejecución de Tests
Para ejecutar la suite de pruebas en el entorno de contenedores:

```bash
docker compose -f docker/docker-compose.yml exec backend python -m pytest tests
```

## 7. Roadmap y Estado del Proyecto
### Fase 1: Core Backend (✅ Completada)
- ✅ Proxy Seguro con Auth SHA256.
- ✅ Comandos de Armado/Desarmado/Noche por Hub o Grupo.
- ✅ Gestión de Rooms y mapeo de dispositivos por habitación.
- ✅ Perfiles de usuario enriquecidos con datos reales de Ajax.
- ✅ Telemetría Enriquecida (Estados de batería, señal, hardware detalle).
- ✅ Proxy Genérico Catch-all (Extensibilidad total).
- ✅ Motor de Suscripciones con Stripe.
- ✅ Suite de Tests Unitarios e Integración (100% Pass).
- ✅ Auditoría de Seguridad (Bandit) y limpieza de historial de secretos.
- ✅ Auditoría Inmutable de transacciones.
- ✅ Sistema de Vouchers B2B (Activación Offline).
- ✅ Sistema de Notificaciones In-App y Alertas por Email.
- ✅ Rate Limiting Global con Cola Asíncrona (100 req/min compartido).
- ✅ Sistema de Caching Redis con TTLs configurables.

### Fase 2: Dashboard Frontend (✅ Completada)
- ✅ Panel de Control en Next.js (Dashboard funcional).
- ✅ Visualización de dispositivos en tiempo real.
- ✅ Gestión de suscripciones para el usuario final (Página de Billing).
- ✅ Integración de alertas en tiempo real.
- ✅ Modo Desarrollo (Bypass Stripe) operativo.
- ✅ **Localización**: Traducción de logs de eventos al Español (frontend-side).
- ✅ **Navegación Unificada**: Cabecera común y consistente (`DashboardHeader`) en todas las vistas (Dashboard, Profile, Billing, Support).
- ✅ **Páginas completas**:
    -   **Dashboard**: Monitorización, Gráficos de tendencias, Status del sistema.
    -   **Profile**: Información del usuario y ajustes.
    -   **Billing**: Gestión de planes y canjeo de Vouchers.
    -   **Support**: Formulario de contacto integrado.

### Fase 7: Analytics Dashboard (✅ Completada)
- ✅ Instalación e integración de `recharts`.
- ✅ Gráfico de Tendencias de Seguridad (Situado centralmente en el Dashboard).
- ✅ Distribución de Señal & Salud de Batería (Gráficos circulares).
- ✅ Fix de tipos y Build de producción.

### Fase 9: Security Hardening (✅ Completada)
- ✅ Implementación de "Request Shield" en Next.js Middleware.
- ✅ Implementación de "Request Shield" en FastAPI Backend.
- ✅ Bloqueo proactivo de scanners de vulnerabilidades.
-   ✅ Protección de archivos sensibles y traversals.

### Fase 10: Support System (✅ Completada)
- ✅ Diseño de API y Esquemas de Soporte.
- ✅ Integración con Servicio de Email (SMTP/Mailgun).
- ✅ Frontend: Formulario de Soporte con validación y Feedback visual.
- ✅ Navegación Unificada (Sidebar en todas las vistas).
- ✅ Security Hardening: Rate Limiting y Sanitización de Inputs.

### Fase 11: Modular Monolith Refactoring (✅ Completada)
- ✅ Migración de lógica dispersa a módulos verticales (`auth`, `ajax`, `billing`, `security`).
- ✅ Consolidación de infraestructura compartida (`shared/infrastructure`).
- ✅ Estandarización de Mocks y mejora de estabilidad de tests de integración.

### Fase 12: Docker Cleanup & Architecture (✅ Completada)
- ✅ Centralización de archivos Docker en carpeta `docker/`.
- ✅ Optimización de contextos de construcción y rutas relativas.
- ✅ Limpieza de scripts de diagnóstico y protección de secretos.
