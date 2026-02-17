# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-17

### Added
- **Visual Identity**: Migrated themes and assets to new Cyan/Teal branding palette.
- **Premium UI**: Implemented `brand-pulse` animations and high-end gradients for the "Flow" concept.
- **Security Audit**: Completed thorough secrets verification; no hardcoded credentials found in the codebase.

### Changed
- **Dashboard Refinement**: Resized sidebar logo and removed "Industrial Security" subtitle for a cleaner look.
- **Tailwind v4 Optimization**: Refactored `globals.css` into a CSS-first configuration, resolving IDE linting warnings.

## [1.0.0] - 2026-02-16

### Added
- **Core Proxy**: Full implementation of the Ajax Systems API proxy.
- **SaaS Billing**: Integrated Stripe for tiered subscription management.
- **Voucher System**: Added B2B offline activation via vouchers.
- **Security Shield**: Proactive protection middleware in both Backend (FastAPI) and Frontend (Next.js).
- **Compliance Auditing**: Immutable request logging for all mutations.
- **Global Rate Limiting**: Shared Redis counter to prevent upstream API bans.
- **Analytics Dashboard**: Real-time signal and battery charts using Recharts.
- **Enhanced Documentation**: Created comprehensive README, Architecture, Security, Configuration, and Contributing guides.
- **OpenAPI Sync**: Synchronized `OPENAPI_ENHANCEMENTS.md` with the latest backend server and path-handling implementation.
- **AI Discovery**: Added `llms.txt` for better indexing by AI agents.

### Changed
- **Modular Monolith**: Refactored codebase into vertical domain slices (Auth, Ajax, Billing, Security).
- **Frontend Navigation**: Centralized sidebar and header navigation across all views.

### Fixed
- **Docker Orchestration**: Centralized and optimized Docker configuration in `docker/` directory.
- **Security Hardening**: Removed all technical secrets from Git history and established strict `.env` usage.
