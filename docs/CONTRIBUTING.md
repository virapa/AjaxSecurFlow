# Contributing to AjaxSecurFlow

Thank you for your interest in contributing! This project is a **Proprietary/Source-Available** repository. By contributing to this project, you agree that your contributions will be licensed under the same [Proprietary License](../LICENSE) that governs this software.

## Legal Notice
By submitting a Pull Request, you represent that:
1. The contribution is your own original work.
2. You grant **virapa** full, irrevocable, and perpetual rights to use, modify, and distribute your contribution as part of the AjaxSecurFlow project.

## Development Workflow

1. **Access**: If you are an external collaborator, ensure you have explicit permission to work on this codebase.
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
