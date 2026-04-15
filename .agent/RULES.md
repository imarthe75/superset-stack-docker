# RULES.md — Memoria Estática: Reglas Innegociables
# Proyecto: Aura Intelligence Suite v8.0 (Agente Residente)
# Última actualización: 2026-04-14
# ⚠️ ESTE ARCHIVO ES INMUTABLE. Solo modificar con aprobación explícita del equipo.

---

## 🔴 REGLA ABSOLUTA #0 — Protocolo de Lectura

> **El agente DEBE leer este archivo y `.agent/MAP.md` ANTES de generar cualquier código.**
> Si no tiene acceso al índice vectorial (ChromaDB), debe leer directamente los archivos
> referenciados en `MAP.md` para construir contexto. Nunca asumir el estado del código.

---

## 🔴 REGLAS DE DRIVERS Y DEPENDENCIAS

| ID     | Regla                                                                              | Justificación                |
|--------|------------------------------------------------------------------------------------|------------------------------|
| DRV-01 | **Prohibido** usar `psycopg2` sin sufijo `-binary` en imágenes Docker slim         | Requiere libpq-dev compilado |
| DRV-02 | Para ClickHouse en Python usar **`clickhouse-connect`** (HTTP) o **`clickhouse-driver`** (TCP). Nunca `clickhouse-sqlalchemy` legacy | Driver oficial, mantenido |
| DRV-03 | Para Redis/Valkey usar **`redis-py >= 5.0`** (compatible con Valkey 9.x)           | Valkey es fork compat. Redis 7.2 |
| DRV-04 | Para dbt-ClickHouse usar **`dbt-clickhouse >= 1.8.0`**                             | Soporte para FINAL keyword   |
| DRV-05 | Superset SQLAlchemy URI para ClickHouse: `clickhousedb://user:pass@host:8123/db`   | Via `clickhouse-connect`     |
| DRV-06 | **Nunca** hardcodear versiones `latest` en imágenes Docker de producción           | Reproducibilidad             |
| DRV-07 | ChromaDB versión: `chromadb >= 0.5.0`; nunca mezclar con `langchain < 0.2`        | API incompatible en versiones viejas |

---

## 🔴 REGLAS DE SEGURIDAD

| ID     | Regla                                                                              |
|--------|------------------------------------------------------------------------------------|
| SEC-01 | **OIDC obligatorio** via Keycloak para TODOS los servicios con UI expuesta al usuario final. Sin excepciones. |
| SEC-02 | **Cero credenciales** en código fuente o en `docker-compose.yml`. Siempre `${VAR}` desde `.env` o Vault. |
| SEC-03 | Puertos de servicios backend **NUNCA** expuestos directamente al host en producción. Solo via Nginx. |
| SEC-04 | `WTF_CSRF_ENABLED = False` solo permitido en entornos de desarrollo. En producción: `True`. |
| SEC-05 | El usuario `superset_ro` de ClickHouse tiene acceso **SOLO** a `aura_silver.*` y `aura_gold.*`. Nunca a `aura_raw`. |
| SEC-06 | Los tokens de Vault tienen TTL máximo de 24h. Rotación automática via Vault Agent. |
| SEC-07 | El slot de replicación PeerDB (`peerdb_slot`) debe monitorearse. Un slot inactivo acumula WAL indefinidamente y puede llenar el disco. |

---

## 🔴 REGLAS DE TIPADO Y CÓDIGO PYTHON

| ID     | Regla                                                                              |
|--------|------------------------------------------------------------------------------------|
| TYP-01 | **Tipado estricto obligatorio** en Python: todas las funciones deben tener type hints en parámetros y retorno. |
| TYP-02 | Usar `from __future__ import annotations` en todos los módulos Python para forward references. |
| TYP-03 | Pydantic v2 para modelos de datos. **Nunca** Pydantic v1 (API incompatible con LangChain 0.2+). |
| TYP-04 | Los flows de Prefect deben tener `@task(retries=3, retry_delay_seconds=30)` en tareas de I/O. |
| TYP-05 | Los modelos dbt deben declarar `config(materialized=...)` explícitamente en cada archivo SQL. |

---

## 🔴 REGLAS DE ARQUITECTURA MDS

| ID     | Regla                                                                              |
|--------|------------------------------------------------------------------------------------|
| MDS-01 | **Ninguna consulta analítica** debe hacerse directamente sobre PostgreSQL OLTP. Siempre via ClickHouse o Cube SQL API. |
| MDS-02 | **Vanna AI y Flowise** deben conectarse a **Cube SQL API** (`:15432`), no a ClickHouse directamente. Esto garantiza métricas validadas por la capa semántica. |
| MDS-03 | Las tablas en `aura_raw` usan motor **`ReplacingMergeTree(updated_at)`**. Las consultas sobre estas tablas DEBEN incluir el modificador `FINAL`. |
| MDS-04 | Las tablas en `aura_gold` usan motor **`MergeTree()`** (ya deduplicadas por dbt). |
| MDS-05 | El slot de replicación PeerDB se llama `peerdb_slot`. La publicación Postgres se llama `peerdb_publication`. |
| MDS-06 | Valkey DB asignación: `DB0`=Celery, `DB1`=Cube pre-aggs, `DB2`=Superset filter state, `DB3`=Superset data cache, `DB4`=Thumbnails, `DB5`=Rate limiting. |
| MDS-07 | El agente nunca debe proponer añadir una nueva fuente de datos a Superset sin primero verificar si existe modelo dbt + cubo Cube para ella. |

---

## 🔴 REGLAS DE DOCKER Y OPERACIONES

| ID     | Regla                                                                              |
|--------|------------------------------------------------------------------------------------|
| OPS-01 | Todo contenedor con API HTTP debe tener `healthcheck` con `curl -f`. Sin excepción. |
| OPS-02 | Todos los servicios pertenecen a `aura_internal`. Solo `nginx` pertenece también a `aura_public`. |
| OPS-03 | Los recursos de ClickHouse no superarán `80%` de la RAM asignada al contenedor (`max_server_memory_usage_to_ram_ratio=0.8`). |
| OPS-04 | Antes de proponer un `docker compose down -v`, el agente debe advertir explícitamente que se borrarán los volúmenes de datos. |
| OPS-05 | Los servicios del stack analítico (ClickHouse, PeerDB, dbt) usan Docker Compose `--profile analytics`. |

---

## 🟡 GUÍAS (Recomendadas, no absolutas)

- Preferir `uv` sobre `pip` para instalar dependencias Python en imágenes Docker (10x más rápido).
- En dbt, preferir vistas (`materialized=view`) para staging y tablas para marts.
- Los ADR deben escribirse en `.agent/DECISIONS/` usando la plantilla `YYYYMMDD_titulo.md`.
- Al agregar un nuevo servicio Docker, actualizar también: `prometheus.yml`, `nginx.conf`, `MAP.md`, `STATE.md`.
