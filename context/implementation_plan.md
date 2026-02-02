# Project Status & Implementation Plan: AjaxSecurFlow

This document fuses the current implementation plan for security refinements with the broader project roadmap, providing a single source of truth for completed tasks and upcoming milestones.

## ✅ Milestone 1: Stability & Localization (Completed)
- [x] **Ajax Protocol Hardening**: Corrected arming logic to use `PUT /arming` with exact string commands (`ARM`, `DISARM`) as per industrial specs.
- [x] **Global i18n**: Full Spanish translation for Landing, Login, and Dashboard features.
- [x] **Testing Excellence**: Verified 100% pass rate for the 91 backend and frontend tests.
- [x] **Dependency Upgrades**: Sanitized environment with `bcrypt v5`, `PyJWT v2.11`, and `starlette v0.52`.
- [x] **Telemetry Clean-up**: Removed mock data from production-bound components for a "Live-only" dashboard experience.

---

## 🚀 Milestone 2: Auth Refinement & Security (In Progress)

This phase covers the transition from standard header-based JWT authentication to a more secure **HTTPOnly Cookies** strategy for the Frontend Dashboard.

### [Component] Backend Authentication Refinement
Currently, the backend returns tokens in the JSON response body. To improve security for the Frontend, we will transition to using cookies while maintaining header support for external scripts.

#### [MODIFY] [auth.py](file:///c:/Users/rpalacios.SATYATEC/APPs/git-proyects/AjaxSecurFlow/backend/app/api/v1/auth.py)
- **Login**: Update `login_for_access_token` to set `access_token` and `refresh_token` as HTTPOnly, Secure, and SameSite=Lax cookies.
- **Logout**: Update `logout` to clear these cookies.
- **Refresh**: Update `refresh_token` to read from and update cookies.
- **Dependency**: Update `get_current_user` to check cookies if the Authorization header is missing.

### [Component] Frontend Dashboard Integration
Ensure the modern Dashboard follows the new security paradigms.

- [x] **Initialization**: Next.js 14+ (App Router) is active.
- [x] **Styling**: Premium Vanilla CSS implementation complete.
- [ ] **Auth Transition**: Automatically handle cookie-based sessions (Pending implementation of backend changes).
- [ ] **Hydration/SSR**: Final review for zero mismatches.

---

## 📋 Milestone 3: Resilience & Performance (Future)
- [ ] **API Resilience**: Implement Exponential Backoff in `AjaxClient` for upstream service reliability.
- [ ] **Monitoring**: Integrate centralized logging (Sentry) for production error tracking.
- [ ] **Optimization**: Review Next.js bundle size and optimize industrial icon loading.

---

## 🛠️ Product Roadmap (New Features)
- [ ] **Dashboard Multi-Hub**: Summary view for multi-site managing.
- [ ] **Webhooks**: Configurable external notifications for 3rd party integrations.
- [ ] **PDF Reports**: Monthly security and activity reporting.

---

## User Review Required

> [!IMPORTANT]
> **Why HTTPOnly Cookies?**
> Standard tokens in headers (LocalStorage) are vulnerable to XSS. By using HTTPOnly cookies, the browser handles the tokens automatically and JavaScript cannot access them, making it significantly more secure.

> [!IMPORTANT]
> **Backward Compatibility Guaranteed**
> This hybrid plan **will NOT break** your 3rd party apps or scripts:
> 1. **Header Priority**: We search the `Authorization` header first.
> 2. **Cookie Fallback**: If no header is present (Browser case), we utilize Cookies.
> 3. **Result**: Your current scripts work as they do today, while the Dashboard becomes enterprise-secure.

Por favor, confirma si podemos proceder con la implementación técnica del **Enfoque Híbrido (Cookies + Headers)** descrito en el Milestone 2.
