# ADR 002: Redis como Limitador de Tasa Global y Caché de Sesiones

**Fecha:** 2026-01-26  
**Estado:** Aceptado

## Contexto
La API de Ajax Systems limita las peticiones a 100 por minuto a nivel global. Necesitamos una forma de que todos nuestros nodos/contenedores compartan un contador de rate limits y las sesiones de usuario de forma atómica y rápida.

## Decisión
Utilizar **Redis** como almacén centralizado para:
- Contadores de Rate Limiting.
- Caché de tokens de sesión de Ajax.

## Consecuencias
- **Positivas:** Sincronización perfecta entre múltiples instancias del backend. Latencia extremadamente baja.
- **Negativas:** Añade una dependencia de infraestructura adicional (Redis).
