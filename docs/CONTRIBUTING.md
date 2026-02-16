# Contributing to AjaxSecurFlow

Thank you for your interest in contributing! This project follows a structured approach to ensure code quality and security.

## Development Workflow

1. **Fork the Repository**: Create your own fork and clone it.
2. **Environment Setup**: 
   - Use Docker for a consistent environment: `docker-compose -f docker/docker-compose.yml up -d`.
   - Configure your `.env` following `.env.example`.
3. **Branching**: Use descriptive branch names (e.g., `feature/add-new-widget` or `fix/auth-leak`).
4. **Code Quality**:
   - Follow PEP 8 for Python.
   - Use Type Hints in all new code.
   - Document new functions using Google-style docstrings.
5. **Testing**:
   - All PRs must maintain or increase test coverage.
   - Run backend tests: `pytest backend/tests`.
   - Run frontend tests: `vitest frontend`.
6. **Submit PR**: Provide a clear description of what was changed and why.

## Code of Conduct

Please be respectful and professional in all interactions. We aim to foster an inclusive and collaborative environment.

## Design Patterns

We strictly adhere to:
- **Vertical Domain Slices**: Logic belongs in `modules/`, not in global utils.
- **Fail-Safe Defaults**: Authentication and Subscription checks are "Close-by-Default".
- **Clean Code**: No over-engineering. Keep functions small and focused.

## Reporting Bugs

Use GitHub Issues to report bugs. Include:
- Screenshots (if applicable)
- Steps to reproduce
- Expected vs Actual behavior
- Environment details (Browser, OS, Docker version)
