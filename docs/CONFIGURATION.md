# 🌐 Environment Configuration Guide

This document provides a detailed explanation of all environment variables used in AjaxSecurFlow.

## 🗄️ Database (PostgreSQL)
These variables configure the primary data store for users, subscriptions, and audits.
- `POSTGRES_USER`: The username for the PostgreSQL database.
- `POSTGRES_PASSWORD`: The password for the database user.
- `POSTGRES_DB`: The name of the database to use.
- `POSTGRES_HOST`: The hostname of the PostgreSQL server (use `db` or `postgres` in Docker).
- `POSTGRES_PORT`: Port number for the database (default: `5432`).
- `DATABASE_URL`: Full connection string (SQLAlchemy format). If provided, it overrides individual parameters.

## 🚀 Redis (Cache & Rate Limit)
- `REDIS_URL`: The full connection string for Redis (e.g., `redis://redis:6379/0`). Used for caching Ajax sessions, global rate limiting, and temporary data.

## 🛡️ Ajax Systems API (Upstream)
- `AJAX_API_BASE_URL`: The root URL of the official Ajax API (default: `https://api.ajax.systems/api/`).
- `AJAX_API_KEY`: Your official partner API key provided by Ajax Systems.
- `AJAX_LOGIN`: (Development Only) Email used for automated testing of the Ajax flow.
- `AJAX_PASSWORD`: (Development Only) Password used for automated testing.
- `ENABLE_DEVELOPER_MODE`: Boolean (`True`/`False`). If `True`, it bypasses Stripe checks, allowing full access for local testing.

## 🏷️ Stripe (SaaS Billing)
- `STRIPE_SECRET_KEY`: Private key for the Stripe API.
- `STRIPE_PUBLIC_KEY`: Public key for the frontend Stripe Elements integration.
- `STRIPE_WEBHOOK_SECRET`: Secret used to verify that incoming requests to `/api/v1/billing/webhook` are legitimately from Stripe.
- `STRIPE_PRICE_ID_BASIC`: Stripe Price ID for the Basic Plan.
- `STRIPE_PRICE_ID_PRO`: Stripe Price ID for the Pro Plan.
- `STRIPE_PRICE_ID_PREMIUM`: Stripe Price ID for the Premium Plan.

## 🔑 Security & JWT
- `SECRET_KEY`: A long, random string used to sign JWT tokens. **Never expose this.**
- `ALGORITHM`: The hashing algorithm for JWT (default: `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: How long local access tokens remain valid (default: `30`).
- `REFRESH_TOKEN_EXPIRE_DAYS`: How long refresh tokens remain valid (default: `7`).
- `COOKIE_SECURE`: Boolean. Set to `True` in production (forces HTTPS).
- `COOKIE_DOMAIN`: The domain scope for session cookies (e.g., `.ajaxsecurflow.com`).
- `COOKIE_SAMESITE`: Policy for cross-site requests (`lax` or `strict`).
- `TRUST_PROXIES`: Boolean (`True`/`False`). If `True`, the backend trusts `X-Forwarded-For` and `X-Real-IP` headers for client IP extraction. **Must be True if using Nginx Proxy Manager in production.**

## 👻 Ghost Admin Security
- `ADMIN_EMAILS`: A JSON list of emails (e.g., `["admin@example.com"]`) that are authorized to perform hazardous administrative actions.
- `ADMIN_SECRET_KEY`: A secondary "Master Key" (X-Admin-Secret) required for high-risk endpoints (like voucher generation).

## 📬 Email & SMTP
Used for sending transactional emails (welcome, billing alerts, support confirmation).
- `SMTP_HOST`: Hostname of your email provider (e.g., `smtp.mailgun.org`).
- `SMTP_PORT`: SMTP port (usually `587` for TLS).
- `SMTP_USER`: Authentication username.
- `SMTP_PASSWORD`: Authentication password.
- `SMTP_FROM_EMAIL`: The "From" address for system emails.
- `SMTP_FROM_NAME`: The display name for system emails.
- `SMTP_TLS`: Boolean. Enables TLS encryption (default: `True`).

## ⚡ Cache TTL Settings (Optional)
Tunable expiration times (in seconds) for Redis caching to optimize performance/freshness.
- `CACHE_TTL_HUBS`: 1800 (30m) - List of hubs.
- `CACHE_TTL_HUB_DETAIL`: 120 (2m) - Details and armed status.
- `CACHE_TTL_DEVICES`: 600 (10m) - List of devices.
- `CACHE_TTL_DEVICE_DETAIL`: 30 (30s) - Telemetry (signal, battery).
- `CACHE_TTL_ROOMS`: 600 (10m) - Physical room layout.
- `CACHE_TTL_GROUPS`: 600 (10m) - Security partitions.

## 🌐 Connections & CORS
- `FRONTEND_URL`: The public-facing URL of the Next.js app (e.g., `https://www.ajaxsecurflow.com`).
- `BACKEND_CORS_ORIGINS`: A JSON list of allowed origins for the API (e.g., `["https://www.ajaxsecurflow.com"]`).
- `NEXT_PUBLIC_API_URL`: (Frontend variable) The public URL where the FastAPI backend is listening (e.g., `https://api.ajaxsecurflow.com`).
