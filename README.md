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

## 5. Funcionalidades Principales (Fase 1)
- **Gestión de Sesiones Ajax**: Login automático, caché de tokens en Redis y renovación automática en caso de expiración (401).
- **Rate Limiting Inteligente**: Protección contra abuso mediante algoritmo Token Bucket en Redis (100 req/min).
- **Monetización SaaS (Stripe)**: Flujo completo de suscripciones con verificación de estado antes de permitir el acceso al Proxy.
- **Procesamiento Asíncrono**: Worker dedicado de Celery para tareas pesadas y persistencia de estados vía Webhooks.
- **Arquitectura Resiliente**: Implementación de *Exponential Backoff* para reintentos de conexión.
- **Seguridad**: Escaneo continuo de vulnerabilidades y cumplimiento de estándares de seguridad en el código.
