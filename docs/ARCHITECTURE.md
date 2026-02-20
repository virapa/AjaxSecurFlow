# AjaxSecurFlow Architecture

## System Overview

AjaxSecurFlow operates as a high-security proxy between end-users and the Ajax Systems API. It adds a multi-tenant business layer (Subscriptions, Auditing, Rate Limiting) on top of the standard Ajax functionality.

## High-Level Flow

```mermaid
graph TD
    User([End User / Client]) -->|HTTPS Request| NPM[Nginx Proxy Manager]
    NPM -->|SSL Termination| Frontend[Next.js Dashboard]
    NPM -->|API Proxy| Backend[FastAPI Proxy]
    
    subgraph "AjaxSecurFlow Backend"
        Backend -->|Middleware| Shield[Security Shield]
        Shield -->|Check| RateLimiter[Redis Rate Limiter]
        RateLimiter -->|Verify| Subs[Stripe/Voucher Logic]
        Subs -->|Data| DB[(PostgreSQL)]
    end
    
    subgraph "External Integration"
        Backend -->|Identity| AjaxAPI[Official Ajax Systems API]
        Backend -->|Payments| Stripe[Stripe API]
    end
    
    Backend -->|Cache| RedisCache[Redis Session/Data Cache]
```

## Architectural Decissions

### 1. Modular Monolith
The project is structured into vertical modules (`backend/app/modules`) to ensure isolation of concerns. 
- **Auth**: Local authentication tied to Ajax IdP.
- **Ajax**: Upstream communication and endpoint mapping.
- **Billing**: Stripe integration and Voucher logic.
- **Security**: Auditing and Request Shielding.

### 2. Identity Synchronization
Instead of maintaining a separate user database for credentials, AjaxSecurFlow validates credentials against Ajax Systems on first login and auto-provisions the local user profile. This ensures a "Single Sign-On" experience: the same credentials are valid and operational both in this gateway and in the official **Ajax Security System** app.

### 3. Shared Global Rate Limiter
To prevent being banned by the official Ajax API, all requests from all tenants are throttled through a shared Redis counter. If the limit (100 req/min) is reached, requests are queued in an asynchronous buffer rather than simply dropped.

### 4. Dual-State Session Management
The system handles two session types:
1. **Local Session**: JWT-based, managed by our FastAPI backend.
2. **Ajax Session**: Managed by Redis, mapped to the user's email, and automatically refreshed by the backend.

### 5. Edge Proxy & SSL Termination
The production environment uses **Nginx Proxy Manager (NPM)** as the entry point. 

> [!NOTE]
> **External Component:** Nginx Proxy Manager is an external infrastructure component managed independently. It is not included in this project's codebase or Docker Compose orchestration; it must be configured separately to point to the `frontend` and `backend` containers.

NPM handles:
- **Automatic HTTPS**: Automated Let's Encrypt certificate issuance and renewal.
- **Reverse Proxying**: Routing traffic between the frontend (Port 3000) and API (Port 8000).
- **Network Shielding**: Acting as the first layer of defense against volumetric attacks and malformed requests.

## Deployment Strategy
The system is fully containerized via Docker and orchestrated with an **external reverse proxy**.
- `backend`: FastAPI server.
- `worker`: Celery worker for background synchronization and Stripe webhooks.
- `frontend`: Next.js optimized build.
- `postgres`: Data persistence.
- `redis`: Shared cache and broker.
