# AjaxSecurFlow - Industrial Grade Ajax Systems Proxy

## 1. Descripción General
AjaxSecurFlow es un Proxy API de grado industrial diseñado para intermediar la comunicación entre clientes finales y la API de Ajax Systems. Su objetivo principal es abstraer la complejidad de la integración, gestionar la autenticación de forma segura mediante rotación de tokens y proteger la infraestructura de Ajax aplicando límites de consumo (Rate Limiting) estrictos y personalizados. Este proyecto sirve como base tecnológica para una plataforma SaaS de gestión de seguridad.

## 2. Stack Tecnológico
El proyecto utiliza tecnologías modernas y robustas, siguiendo los estándares de la industria:

- **Lenguaje**: Python 3.14+ (Totalmente Asíncrono)
- **Framework API**: FastAPI (Alto rendimiento, validación automática)
- **Base de Datos**: PostgreSQL 15+ (con SQLAlchemy 2.0 Async para ORM)
- **Caché y Mensajería**: Redis (Gestión de sesiones, Rate Limiting, Celery Broker)
- **Tareas Background**: Celery (Sincronización de datos, procesamiento de webhooks)
- **Monitoreo**: Flower (Panel de control para tareas de Celery)
- **Pagos y SaaS**: Stripe SDK (Gestión de suscripciones y webhooks)
- **Gestión de Configuración**: Pydantic Settings (Validación estricta de variables de entorno)
- **Infraestructura**: Docker & Docker Compose (Contenerización completa)
- **Testing y Calidad**: Pytest, Bandit (Seguridad), pip-audit (Vulnerabilidades)

## 3. Instalación y Ejecución

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

### Ejecución
Para iniciar todos los servicios (API, Base de Datos, Redis):

```bash
docker-compose up -d --build
```

### Inicialización de Base de Datos
Una vez que los contenedores estén corriendo, es necesario aplicar las migraciones para crear las tablas:

```bash
# Ejecutar migraciones
docker-compose run --rm app alembic upgrade head
```

La API estará disponible en `http://localhost:8000/docs`.

### Ejecución de Tests
Para ejecutar la suite de pruebas unitarias:

```bash
docker-compose run --rm pytest
```

## 4. Estructura del Proyecto
El proyecto sigue una **Clean Architecture** (Arquitectura Cebolla) estricta:

```text
/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Endpoints (Adaptadores Primarios)
│   │   ├── core/           # Configuración (Settings), Seguridad
│   │   ├── domain/         # Modelos de Datos (SQLAlchemy)
│   │   ├── services/       # Lógica de Negocio (AjaxClient, RateLimiter)
│   │   └── worker/         # Tareas Background
│   ├── tests/              # Tests
├── context/                # Documentación de Contexto y Arquitectura
└── docker-compose.yml      # Orquestación de Contenedores
```

## 5. Arquitectura del Sistema
El sistema opera bajo un modelo de **Event-Driven Architecture** parcial para procesos críticos:

1.  **API Síncrona (FastAPI)**: Maneja peticiones de alto rendimiento (Proxy, Auth).
2.  **Worker Asíncrono (Celery)**: Procesa tareas pesadas (Sincronización de datos) y críticas/bloqueantes (Webhooks de Stripe).
3.  **Broker & Caché (Redis)**: Actúa como bus de mensajes para Celery y almacén de alta velocidad para Rate Limiting y Sesiones.

### Flujo SaaS (Billing)
1.  El usuario se registra y recibe un `status: free` (acceso limitado o nulo).
2.  Inicia una sesión de pago (`/api/v1/billing/create-checkout-session`) que redirige a Stripe.
3.  Al completar el pago, Stripe envía un webhook (`channel: customer.subscription.created`).
4.  **Celery** procesa el webhook y actualiza la BBDD del usuario a `status: active`.
5.  **Middleware de Seguridad**: Intercepta peticiones al Proxy, verifica el `status`, y permite o deniega el acceso.

## 6. Aseguramiento de Calidad (QA) & Seguridad
Este proyecto implementa controles de calidad de grado militar:

-   **Integrity Tests**: Verificación automática de la salud del entorno (`test_system_integrity.py`), validando versiones de librerías y presencia de herramientas de seguridad.
-   **Security Scanning**:
    -   `bandit`: Análisis estático para detectar vulnerabilidades en el código Python.
    -   `pip-audit`: Escaneo de dependencias con vulnerabilidades conocidas (CVEs).
-   **Rotación de Secretos**: Las credenciales de Ajax nunca se almacenan en texto plano en la BD, residen en memoria/entorno y se rotan automáticamente vía el cliente proxy.

## 7. Funcionalidades Principales (Fase 1 - Completada)
-   ✅ **Proxy Seguro**: Túnel autenticado hacia Ajax Systems.
-   ✅ **Rate Limiting**: 100 req/min por usuario (Token Bucket en Redis).
-   ✅ **SaaS Engine**: Integración profunda con Stripe (Checkout & Webhooks).
-   ✅ **Background Workers**: Procesamiento de tareas fuera del ciclo de petición-respuesta.
-   ✅ **Auditoría**: Registro inmutable de transacciones (`action`, `payload`, `timestamp`).
