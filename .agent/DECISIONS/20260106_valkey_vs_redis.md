# ADR-001 — Uso de Valkey en lugar de Redis
# Fecha: 2026-01-06
# Estado: ACEPTADO
# Autor: Equipo Aura

## Contexto

El stack requería un broker de mensajes y cache compatible con Redis API para:
- Celery (Superset tasks)
- Cube.js pre-agregaciones (Rollups)

## Decisión

Usar **Valkey 9.0.3** en lugar de Redis 7.x.

## Justificación

| Factor            | Redis 7.x              | Valkey 9.x              |
|-------------------|------------------------|-------------------------|
| Licencia          | SSPL (no OSI-aprobada) | BSD-3 (OSI-aprobada)    |
| Compatibilidad    | API propia             | 100% compatible Redis   |
| Mantenimiento     | Redis Inc.             | Linux Foundation        |
| Docker image      | `redis:7`              | `valkey/valkey:9.0.3`   |
| Riesgo legal      | Alto en empresas       | Ninguno                 |

**Nota crítica para el agente:** La imagen Docker es `valkey/valkey:9.0.3`.
El cliente Python es `redis-py >= 5.0` (Valkey es API-compatible).
Las URLs de conexión usan el esquema `redis://` (no `valkey://`).

## Consecuencias

- `redis-py` funciona sin modificación.
- Superset `superset_config.py` usa `redis://valkey:6379/X`.
- Cube.js usa `CUBEJS_REDIS_URL=redis://valkey:6379/1`.
- Si en el futuro Redis corrige su licencia, la migración es trivial (cambiar imagen).
