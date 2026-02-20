# Security Policy

## Security by Design

AjaxSecurFlow is built with security as a first-class citizen. We follow OWASP 2025 recommendations and implement multiple layers of defense.

## Active Protections

### 1. Request Shield (Hardened)
Our backend includes a middleware "Shield" that intercepts and blocks common malicious probes. This shield performs **URI Normalization** (decoding and path resolution) before validation to prevent evasion via encoding (e.g., `%2e%2e/`).
- Legacy server extensions (`.php`, `.asp`)
- Sensitive files (`.env`, `.git`)
- Admin panel probes (`/wp-admin`, `/phpmyadmin`)
- Path traversal attempts (`../etc/passwd`)

### 2. Edge Security (Nginx Proxy Manager)
The system is shielded by an external **Reverse Proxy (NPM)**. 

> [!NOTE]
> This component is configured at the infrastructure level (outside this repository) and is responsible for:
- **Managed SSL/TLS**: Automated certificate management via Let's Encrypt for all production domains.
- **Protocol Enforcement**: Enforces HTTPS-only traffic and secure modern TLS versions.
- **Additional Filtering**: Acts as the first point of contact for external traffic, absorbing malformed requests before they reach the backend application.

### 3. IP Spoofing Protection
The system implements a centralized utility for extracting client IPs, ensuring that headers like `X-Forwarded-For` are only trusted when a proven proxy (like Nginx Proxy Manager) is present. This prevents attackers from bypassing rate limits or security logs by spoofing their origin IP.

### 4. Fingerprinted Sessions
Every JWT issued by the system is fingerprinted with the client's `User-Agent`. If a token is stolen and used from a different browser, the system rejects it immediately.

### 5. Hardened Authentication
We use a "Zero-Knowledge" approach for passwords (hashing via Bcrypt v4+) and implement **Opaque Errors**. We never reveal if a specific user exists or which part of the authentication failed (email vs password).

### 6. Audit Trail
All mutation requests (POST, PUT, DELETE) are logged in an immutable audit table (`ajax_security_audit`), including:
- Correlation ID
- User ID
- IP Address & User Agent
- Action performed and result status
- Latency

---

🌐 **Production Environments:**
- **Frontend Dashboard:** [https://www.ajaxsecurflow.com](https://www.ajaxsecurflow.com)
- **Official API Proxy:** [https://api.ajaxsecurflow.com/docs](https://api.ajaxsecurflow.com/docs)

## Reporting a Vulnerability

If you discover a security vulnerability, please do NOT open a GitHub issue. Instead, follow these steps:
1. Email us at `support@ajaxsecurflow.com`.
2. Provide a detailed description of the vulnerability and steps to reproduce.
3. We will acknowledge your report within 24 hours and provide a timeline for a resolution.

## Scanners and Tools used
- **Bandit**: Static analysis for Python security issues.
- **Pip-audit**: Dependency vulnerability scanning (Target: 0 vulnerabilities).
- **Hardened Headers**: CSP, HSTS, X-Frame-Options, and X-Content-Type-Options are applied to all responses.
