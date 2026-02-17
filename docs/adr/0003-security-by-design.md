# ADR 003: Estrategia de "Security by Design" y Blindaje Proactivo

**Fecha:** 2026-01-26  
**Estado:** Aceptado

## Contexto
Dada la naturaleza crítica del sistema (gestión de alarmas), cualquier vulnerabilidad de tipo OWASP (SSRF, Inyección, Path Traversal) podría comprometer la seguridad física de los usuarios finales.

## Decisión
Implementar una capa de **Shielding Proactivo** en el middleware:
- Normalización estricta de URIs antes del procesamiento.
- Bloqueo por reputación de patrones y extensiones maliciosas (.php, .env).
- Registro inmutable de toda petición de mutación (POST/PUT/DELETE).

## Consecuencias
- **Positivas:** Reducción drástica de la superficie de ataque. Trazabilidad total de acciones críticas.
- **Negativas:** Leve sobrecarga de latencia en cada petición debido a la inspección.
