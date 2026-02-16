# Security Policy

## Security by Design

AjaxSecurFlow is built with security as a first-class citizen. We follow OWASP 2025 recommendations and implement multiple layers of defense.

## Active Protections

### 1. Request Shield
Our backend and frontend include a middleware "Shield" that intercepts and blocks common malicious probes:
- Legacy server extensions (`.php`, `.asp`)
- Sensitive files (`.env`, `.git`)
- Admin panel probes (`/wp-admin`, `/phpmyadmin`)
- Path traversal attempts (`../etc/passwd`)

### 2. Fingerprinted Sessions
Every JWT issued by the system is fingerprinted with the client's `User-Agent`. If a token is stolen and used from a different browser, the system rejects it immediately.

### 3. Hardened Authentication
We use a "Zero-Knowledge" approach for passwords (hashing via Bcrypt v4+) and implement **Opaque Errors**. We never reveal if a specific user exists or which part of the authentication failed (email vs password).

### 4. Audit Trail
All mutation requests (POST, PUT, DELETE) are logged in an immutable audit table (`ajax_security_audit`), including:
- Correlation ID
- User ID
- IP Address & User Agent
- Action performed and result status
- Latency

## Reporting a Vulnerability

If you discover a security vulnerability, please do NOT open a GitHub issue. Instead, follow these steps:
1. Email us at `security@ajaxsecurflow.com`.
2. Provide a detailed description of the vulnerability and steps to reproduce.
3. We will acknowledge your report within 24 hours and provide a timeline for a resolution.

## Scanners and Tools used
- **Bandit**: Static analysis for Python security issues.
- **Pip-audit**: Dependency vulnerability scanning (Target: 0 vulnerabilities).
- **Hardened Headers**: CSP, HSTS, X-Frame-Options, and X-Content-Type-Options are applied to all responses.
