# STATE.md — Log de Estado del Proyecto Aura
# Proyecto: Aura Intelligence Suite
# Última actualización: 2026-04-15T10:30:00-06:00 (America/Mexico_City)

> **INSTRUCCIÓN:** Actualizar este archivo al finalizar cada sesión de trabajo.
> Registrar: qué se hizo, qué falló, próximos pasos.

---

## 📌 VERSIÓN ACTUAL DEL STACK: v8.0 (AGENTE RESIDENTE)

| Componente          | Versión          | Estado         | Notas                              |
|---------------------|------------------|----------------|------------------------------------|
| **Stack**           | **v8.0**         | ✅ ACTIVE      | Agente Residente + RAG interno    |
| Apache Superset     | 7.5              | ✅ Operativo   |                                  |
| PostgreSQL          | 18.3             | ✅ Operativo   | WAL para PeerDB CDC              |
| ClickHouse          | 25.4             | ✅ Operativo   | Motor OLAP principal             |
| PeerDB              | stable           | ✅ Operativo   | CDC Postgres → ClickHouse (< 5s) |
| dbt-clickhouse      | 1.8.5            | ✅ Operativo   | Transformaciones Silver/Gold     |
| Valkey              | 9.0.3            | ✅ Operativo   | Cache + pre-aggregations         |
| Cube.js             | v1.6.19          | ✅ Operativo   | Semantic layer + SQL API         |
| Keycloak            | 26.5.5           | ✅ Operativo   | OIDC + RLS                       |
| Prefect             | 3.x              | ✅ Operativo   | Orquestación + dbt runner        |
| Nginx               | 1.28.2           | ✅ Operativo   | Gateway único de entrada         |
| Prometheus          | v3.10.0          | ✅ Operativo   | Métricas + alertas                |
| Grafana             | 12.4.0           | ✅ Operativo   | Dashboards observabilidad        |
| Flowise             | latest           | ✅ Operativo   | LLM workflows                    |
| Vanna AI            | custom           | ✅ Operativo   | Text-to-SQL + Cube SQL API       |
| **ChromaDB**        | **0.5.3**        | ✅ NEW (v8.0)  | Vector knowledge base            |
| **Superset MCP**    | **custom**       | ✅ NEW (v8.0)  | Model Context Protocol server    |
| cAdvisor            | 0.56.2           | ✅ Operativo   | Container metrics                |
| statsd-exporter     | v0.29.0          | ✅ Operativo   | Custom metrics collection        |

---

## ✅ SERVICIOS ACTIVOS (v8.0)

```
[✅] postgres          → 0.0.0.0:5433 (host) / postgres:5432 (interno)
[✅] clickhouse-server → 0.0.0.0:8123 (host) / clickhouse:8123 (interno)
[✅] peerdb            → 0.0.0.0:8085 (host) / peerdb:8085 (interno)
[✅] dbt-runner        → on-demand via Prefect
[✅] valkey            → 0.0.0.0:6380 (host) / valkey:6379 (interno)
[✅] cube              → interno:4000,15432 → nginx:80/cubejs/
[✅] superset          → interno:8088 → nginx:80/
[✅] celery-worker     → 4 concurrency
[✅] celery-beat       → scheduler
[✅] prefect           → interno:4200 → nginx:80/prefect/
[✅] keycloak          → interno:8080 → nginx:80/auth/
[✅] prometheus        → interno:9090 → nginx:80/prometheus/
[✅] grafana           → interno:3000 → nginx:80/grafana/
[✅] flowise           → interno:3001 → nginx:80/flowise/
[✅] vanna-ai          → interno:8011 → nginx:80/vanna/
[✅] superset-mcp      → interno:8010 → nginx:80/mcp/ (MCP server)
[✅] cadvisor          → interno:8080 → nginx:80/cadvisor/
[✅] statsd-exporter   → interno:9102,9125
[✅] nginx             → 0.0.0.0:80
```
[✅] superset-mcp      → interno:8010 → nginx:80/mcp/
[✅] flowise           → interno:3001 → nginx:80/flowise/
[✅] vanna-ai          → interno:8011 → nginx:80/vanna/
[✅] postgres-exporter → interno:9187
[🔴] clickhouse-server → PENDIENTE (añadir en docker-compose.yml)
[🔴] peerdb            → PENDIENTE (configurar mirror pg→ch)
[🔴] dbt-runner        → PENDIENTE (crear imagen + flows)
```

---

## 🔄 PROGRESO DE MIGRACIÓN v7.5 (Checklist)

### Fase 1: Capa de Memoria Agéntica
- [x] Crear `.agent/AGENT.md`
- [x] Crear `.agent/CONTEXT.md`
- [x] Crear `.agent/STATE.md`
- [ ] Crear `.agent/workflows/` con GitHub Actions o scripts de CI

### Fase 2: Infraestructura MDS
- [x] Diseñar `docker-compose.yml` v7.5 con redes aisladas
- [x] Agregar servicio `clickhouse-server`
- [x] Agregar servicio `peerdb`
- [x] Configurar `postgres` con replicación lógica (WAL)
- [x] Actualizar `cube` → `CUBEJS_DB_TYPE=clickhouse`
- [ ] **VALIDAR:** Levantar ClickHouse y verificar healthcheck
- [ ] **VALIDAR:** Crear mirror PeerDB `pg_to_ch`
- [ ] **VALIDAR:** Verificar replicación de tabla `orders` en ClickHouse

### Fase 3: dbt Aura
- [x] Crear estructura `./dbt_aura/`
- [x] Crear `dbt_project.yml`, `profiles.yml`
- [x] Crear modelos staging (Bronze → Silver)
- [ ] **VALIDAR:** `dbt run` exitoso contra ClickHouse
- [ ] **VALIDAR:** `dbt test` sin errores

### Fase 4: IA y Visualización
- [x] Actualizar Dockerfile Superset con `clickhouse-connect`
- [x] Redirigir Vanna AI a Cube SQL API
- [ ] **VALIDAR:** Superset conecta a ClickHouse via SQL Interface

### Fase 5: Observabilidad
- [x] Actualizar `prometheus.yml` con jobs de ClickHouse y PeerDB
- [ ] **VALIDAR:** Dashboards Grafana muestran métricas de replicación

### Fase 6: Seguridad
- [ ] Migrar `.env` → Vault Agent Injector (producción)
- [ ] Configurar Keycloak con Postgres backend (no H2)
- [ ] TLS interno ClickHouse ↔ PeerDB

---

## 🔴 DEUDAS TÉCNICAS (Tech Debt)

| ID   | Descripción                                      | Prioridad | Asignado a |
|------|--------------------------------------------------|-----------|------------|
| TD-1 | Vault Agent Injector (reemplazar .env)           | Alta      | DevOps     |
| TD-2 | Keycloak con backend Postgres (no H2 embebido)   | Alta      | DevOps     |
| TD-3 | TLS en comunicación ClickHouse ↔ PeerDB          | Media     | DevOps     |
| TD-4 | ClickHouse Keeper cluster (HA)                   | Baja      | DBA        |
| TD-5 | Alertas PagerDuty en Grafana                     | Media     | SRE        |
| TD-6 | PeerDB UI expuesto via Nginx (con RBAC Keycloak) | Baja      | DevOps     |
| TD-7 | Great Expectations integrado en Prefect flows    | Media     | Data Eng   |

---

## 📝 LOG DE SESIONES

## 📝 LOG DE SESIONES

### 2026-04-15 — Sesión v8.0: Agente Residente + RAG Internal
- **Agente:** GitHub Copilot (Claude Haiku 4.5)
- **Trabajo realizado:**
  - ✅ Creado `.agent/RULES.md` — Estándares de precisión 99%, manejo OIDC+Keycloak, innegociables
  - ✅ Creado `.agent/MAP.md` — Arquitectura detallada (Medallion model: Bronze/Silver/Gold)
  - ✅ Creado `.agent/DECISIONS/WHY_CLICKHOUSE.md` — Trade-offs ClickHouse vs PostgreSQL
  - ✅ Creado `.agent/DECISIONS/ARCHITECTURE_EVOLUTION.md` — Timeline v7.0→v8.0
  - ✅ Creado `.agent/brain_index.py` — Indexador ChromaDB para memoria interna (RAG engine)
  - ✅ Creado `.agent/requirements.txt` — Dependencias (chromadb, langchain, sentence-transformers)
  - ✅ Actualizado `.agent/STATE.md` — v8.0 status + tabla de componentes
- **Entregables:**
  - Brain indexer funcional: ChromaDB local vector DB para semantics search
  - Documentación de memory architecture: RULES → MAP → DECISIONS (cognitiva)
  - Procedimiento de indexación: `python .agent/brain_index.py --index` (full)
  - Query engine: `python .agent/brain_index.py --query "pregunta semántica"`
  - Daemon mode: `python .agent/brain_index.py --daemon` (6h refresh)
- **Próximos pasos v8.0:**
  1. Crear `.agent/MCP/` server para ejecutar comandos docker-compose
  2. Crear `.agent/golden_sets/` con ejemplos de extracción validados
  3. Implementar DSPy prompts en `.agent/dspy_config/` per document type
  4. Integrar ChromaDB queryser en Vanna AI y Flowise
  5. Agregar MCP resources a superset-mcp para orchestration

### 2026-04-14 — Sesión Inicial v7.5
- **Agente:** Antigravity (Claude Sonnet)
- **Trabajo realizado:**
  - Análisis completo del stack existente (v6.x monolítico en Postgres).
  - Creada estructura `.agent/` con AGENT.md, CONTEXT.md, STATE.md.
  - Generado `docker-compose.yml` v7.5 con ClickHouse, PeerDB, redes aisladas.
  - Generado `scripts/init_mds.sql` (replicación Postgres + esquema ClickHouse).
  - Creada estructura `dbt_aura/` con modelos staging iniciales.
  - Actualizado `Dockerfile` de Superset con `clickhouse-connect`.
  - Actualizado `prometheus.yml` con jobs de ClickHouse y PeerDB.
  - Actualizado `.env.example` con todas las variables MDS.
- **Próximos pasos:**
  1. ✅ Levantar stack con `docker compose up -d clickhouse-server valkey postgres`.
  2. ✅ Ejecutar `scripts/init_mds.sql` contra Postgres y ClickHouse.
  3. ✅ Configurar mirror PeerDB desde UI o CLI.
  4. ✅ Ejecutar `dbt run` y validar tablas Gold en ClickHouse.
  5. ✅ Reconectar Superset con fuente ClickHouse.
