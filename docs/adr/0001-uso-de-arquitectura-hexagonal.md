# ADR 001: Uso de Arquitectura Hexagonal (Ports & Adapters)

**Fecha:** 2026-01-26  
**Estado:** Aceptado

## Contexto
El sistema AjaxSecurFlow debe ser extremadamente flexible para adaptarse a cambios en la API oficial de Ajax Systems y permitir la integración de futuros proveedores de hardware. Además, necesitamos una base de código testable de forma aislada.

## Decisión
Implementar **Arquitectura Hexagonal**.
- El dominio (reglas de negocio) no tiene dependencias hacia fuera.
- La infraestructura (FastAPI, PostgreSQL, Redis) se implementa a través de adaptadores.

## Consecuencias
- **Positivas:** Alta testabilidad de la lógica de negocio sin base de datos. Desacoplamiento total del framework.
- **Negativas:** Ligero aumento de la complejidad inicial del boilerplate.
