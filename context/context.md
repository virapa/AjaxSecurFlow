# Contexto del Proyecto Final de Máster: Proxy API Ajax Systems (SaaS Ready)

> **Este archivo define el contexto, las reglas y los estándares de calidad para el desarrollo del Proyecto Final del Máster.**

---

## 1. Visión del Proyecto
Estamos construyendo un **Proxy API de grado industrial** para Ajax Systems, diseñado para ser monetizado como SaaS.
El objetivo es desacoplar la complejidad de la API de Ajax, gestionar la autenticación de forma segura y aplicar límites de consumo (Rate Limiting) estrictos.
El sistema está diseñado para ser monetizado mediante un modelo SaaS (suscripciones).

## 2. Referencias al Máster (Pilares de Desarrollo)
Este proyecto debe reflejar la excelencia técnica aprendida durante todo el curso. Se aplicarán los siguientes principios:

*   **Módulo 02 & 03: Ingeniería y Arquitectura**
    *   **Clean Architecture (Arquitectura Cebolla):** Estricta separación de responsabilidades. Dependencias hacia el centro (Domain).
    *   **SOLID:** Cohesión alta, acoplamiento bajo.
*   **Módulo 06 & 10: Flujo de Desarrollo con IA**
    *   **AI Pair Programming:** Uso de la IA como copiloto experto, no solo como generador de código.
    *   **Iteración Rápida:** Ciclos cortos de desarrollo con verificación constante.
*   **Módulo 07: Calidad y Testing**
    *   **TDD (Test Driven Development):** Escribir tests antes de la implementación cuando sea factible (especialmente en lógica de negocio).
    *   **Testing Pyramid:** Base sólida de Unit Tests, seguidos de Integration Tests y E2E.
    *   **Quality Gates:** Uso de Linters (Ruff), Type Checkers (MyPy) y Hooks de pre-commit.
*   **Módulo 09: Seguridad**
    *   **Security by Design:** Autenticación robusta, manejo seguro de secretos (.env), validación de inputs (Pydantic).
*   **Módulo 08: Infraestructura**
    *   **Docker:** Contenerización de todos los servicios.

## 3. Stack Tecnológico
*   **Lenguaje:** Python 3.14+ (Moderno y Asíncrono).
*   **Framework API:** FastAPI.
*   **Base de Datos:** PostgreSQL (con SQLAlchemy 2.0 Async).
*   **Cola de Tareas & Caché:** Redis + Celery (para manejo de Rate Limits y tareas en background).
*   **Pagos:** Stripe (Suscripciones).
*   **Infraestructura:** Docker Compose.

## 4. Estructura del Proyecto (Clean Architecture)
El proyecto sigue una estructura de monorepo estricta:

```text
/
├── backend/                # Lógica del Servidor
│   ├── app/
│   │   ├── api/v1/         # Adaptadores Primarios (Endpoints: Proxy, Auth, Billing)
│   │   ├── core/           # Configuración, Seguridad, Clientes externos (Stripe)
│   │   ├── domain/         # Núcleo: Entidades y Reglas de Negocio (User, Subscription)
│   │   ├── schemas/        # DTOs y Validación (Pydantic V2)
│   │   ├── services/       # Lógica de Aplicación (AjaxClient, RateLimiter)
│   │   └── worker/         # Tareas asíncronas (Celery)
│   ├── tests/              # Tests Unitarios e Integración
│   └── alembic/            # Migraciones
├── frontend/               # Dashboard de usuario (Fase 2 - Next.js)
└── docker-compose.yml      # Definición de infraestructura
```

## 5. Rol de la IA y Reglas de Generación
Actúa como un **Senior Backend Engineer** especializado en Python/FastAPI.

### Reglas de Oro:
1.  **Scope Rule:** Respeta la arquitectura. No importes capas externas (API) dentro de capas internas (Domain).
2.  **No Inventar:** Usa las librerías definidas (SQLAlchemy 2.0, Pydantic V2). No introduzcas dependencias innecesarias.
3.  **Testing First:** Si se pide una funcionalidad de negocio, prioriza generar el test o la especificación antes del código.
4.  **SaaS First:** Cualquier acceso a recursos protegidos (Ajax API) DEBE validar el estado de suscripción del usuario (`is_subscription_active`) antes de proceder.
5.  **Explicabilidad:** Explica brevemente decisiones de arquitectura complejas.


## 6. Documentación completa y detallada (README.md)
a. Descripción general del proyecto.
b. Stack tecnológico utilizado.
c. Información sobre su instalación y ejecución.
d. Estructura del proyecto.
e. Funcionalidades principales

---
**Usa este contexto para guiar cada decisión técnica y de implementación.**
