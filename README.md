# AjaxSecurFlow - Industrial Grade Ajax Systems Proxy

## 1. Descripción General
AjaxSecurFlow es un Proxy API de grado industrial diseñado para intermediar la comunicación entre clientes finales y la API de Ajax Systems. Su objetivo principal es abstraer la complejidad de la integración, gestionar la autenticación de forma segura mediante rotación de tokens y proteger la infraestructura de Ajax aplicando límites de consumo (Rate Limiting) estrictos y personalizados. Este proyecto sirve como base tecnológica para una plataforma SaaS de gestión de seguridad.

## 2. Stack Tecnológico
El proyecto utiliza tecnologías modernas y robustas, siguiendo los estándares de la industria:

- **Lenguaje**: Python 3.11+ (Totalmente Asíncrono)
- **Framework API**: FastAPI (Alto rendimiento, validación automática)
- **Base de Datos**: PostgreSQL 15+ (con SQLAlchemy 2.0 Async para ORM)
- **Caché y Mensajería**: Redis (Gestión de sesiones, Rate Limiting, Celery Broker)
- **Tareas Background**: Celery (Sincronización de datos, procesamiento de webhooks)
- **Monitoreo**: Flower (Panel de control para tareas de Celery)
- **Pagos y SaaS**: Stripe SDK (Gestión de suscripciones y webhooks)
- **Gestión de Configuración**: Pydantic V2 & Settings (Validación estricta)
- **Seguridad**: Bcrypt (Hashing moderno), PyJWT (Tokens), SHA256 (Ajax Auth)
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

### Documentación de la API
Una vez iniciados los servicios, la documentación interactiva y técnica está disponible en:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (Para pruebas interactivas)
- **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (Para referencia técnica detallada)

### Ejecución de Tests
Para ejecutar la suite de pruebas:

```bash
docker-compose exec app python -m pytest backend/tests
```

## 4. Estructura del Proyecto
El proyecto sigue una **Clean Architecture** (Arquitectura Cebolla) estricta:

```text
/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Endpoints (Adaptadores Primarios)
│   │   ├── core/           # Configuración (Settings), Seguridad, DB
│   │   ├── domain/         # Modelos de Datos (SQLAlchemy)
│   │   ├── schemas/        # DTOs y Validación (Pydantic V2)
│   │   ├── services/       # Lógica de Negocio (AjaxClient, Billing)
│   │   └── worker/         # Tareas Background
│   ├── tests/              # Pruebas Unitarias e Integración
├── scripts/                # Utilidades y Scripts de mantenimiento
├── context/                # Documentación de Contexto y Arquitectura
└── docker-compose.yml      # Orquestación de Contenedores
```

## 5. Arquitectura del Sistema
El sistema opera bajo un modelo de **Event-Driven Architecture** parcial para procesos críticos:

1.  **API Síncrona (FastAPI)**: Maneja peticiones de alto rendimiento (Proxy, Auth).
2.  **Worker Asíncrono (Celery)**: Procesa tareas pesadas (Sincronización de datos) y críticas/bloqueantes (Webhooks de Stripe).
3.  **Broker & Caché (Redis)**: Actúa como bus de mensajes para Celery y almacén de alta velocidad para Rate Limiting, Sesiones de Ajax y Caching.

### Flujo de Sesión Ajax (Optimizado)
El `AjaxClient` implementa un patrón Singleton con persistencia en Redis para:
- Cachear el `sessionToken` y el `userId`.
- Realizar login automático usando **SHA256** solo cuando el token expira.
- Re-inyección automática de credenciales en rutas `/user/{userId}/...`.

### Control de Seguridad (Armado/Desarmado)
El proxy expone una interfaz unificada para el control de estados:
- **Endpoint**: `POST /api/v1/ajax/hubs/{hub_id}/arm-state`
- **Modos Soportados**: 
    - `0`: Desarmado.
    - `1`: Armado Total.
    - `2`: Modo Noche (Parcial).
- **Acción por Grupo**: Soporta el parámetro opcional `groupId` para actuar sobre particiones específicas.

## 6. Aseguramiento de Calidad (QA) & Seguridad
Este proyecto implementa controles de calidad de grado militar:

-   **Integrity Tests**: Verificación automática de la salud del entorno (`test_system_integrity.py`), validando versiones de librerías y presencia de herramientas de seguridad.
-   **Q&A Policies**: Código 100% documentado con Docstrings (Google format), Tipado estricto (Type Hints) y manejo de errores estandarizado.
-   **Security Scanning**:
    -   `bandit`: Análisis estático para detectar vulnerabilidades en el código Python.
    -   `pip-audit`: Escaneo de dependencias con vulnerabilidades conocidas (CVEs).
-   **Modern Hashing**: Uso de `bcrypt` (v4.0+) nativo, eliminando dependencias obsoletas como `passlib`.

## 7. Roadmap y Estado del Proyecto
### Fase 1: Core Backend (✅ Completada)
- ✅ Proxy Seguro con Auth SHA256.
- ✅ Comandos de Armado/Desarmado/Noche por Hub o Grupo.
- ✅ Rate Limiting por usuario en Redis.
- ✅ Motor de Suscripciones con Stripe.
- ✅ Suite de Tests Unitarios (100% Pass).
- ✅ Auditoría Inmutable de transacciones.

### Fase 2: Dashboard Frontend (⏳ En Progreso)
- 🔲 Panel de Control en Next.js.
- 🔲 Visualización de dispositivos en tiempo real.
- 🔲 Gestión de suscripciones para el usuario final.
