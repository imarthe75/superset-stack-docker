# MAP.md — Mapa Técnico del Proyecto Aura v8.0
# Proyecto: Aura Intelligence Suite (superset-stack-docker)
# Última actualización: 2026-04-14
# LEER ANTES DE CODIFICAR — Este archivo es el mapa de navegación del agente.

---

## 1. TOPOLOGÍA DE SERVICIOS (Flujo de Datos)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         AURA v8.0 — DATA FLOW MAP                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

[INTERNET / Usuario]
        │ HTTP:80
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NGINX 1.28.2    [aura_public + aura_internal]                      │
│  Rutas: / → superset | /cubejs/ → cube | /grafana/ → grafana        │
│         /auth/ → keycloak | /prefect/ → prefect | /peerdb/ → peerdb │
│         /vanna/ → vanna-ai | /flowise/ → flowise | /mcp/ → mcp      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ [aura_internal network: 172.28.0.0/16]
   ┌───────────────────────────┼───────────────────────────────────────┐
   │                           │                                       │
   ▼                           ▼                                       ▼
┌──────────────┐   ┌──────────────────────┐             ┌─────────────────────┐
│  KEYCLOAK    │   │     SUPERSET 6.0.0   │             │  PROMETHEUS/GRAFANA │
│  26.5.5      │   │     :8088 [OLTP]     │             │  Métricas de todos  │
│  OIDC/OAuth2 │   │   + celery-worker    │             │  los servicios      │
│  /auth/      │   │   + celery-beat      │             │  /prometheus/       │
│  Realm:superset│ │   + superset-mcp     │             │  /grafana/          │
└──────────────┘   └──────────┬───────────┘             └─────────────────────┘
                              │ metadata DB
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  POSTGRESQL 18.3  :5432  [aura_internal]                            │
│  DB: superset     → Metadatos de Superset (usuarios, dashboards)    │
│  DB: sales_data   → Datos transaccionales OLTP                      │
│  DB: peerdb_catalog → Metadatos de PeerDB                           │
│  WAL Level: logical | Replication Slots: peerdb_slot                │
│  Publication: peerdb_publication (users,orders,products,tickets,ml) │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ WAL CDC (Logical Replication)
                       ▼ [profile: analytics]
┌─────────────────────────────────────────────────────────────────────┐
│  PEERDB (stable)  :8085  [aura_internal]                            │
│  Mirror: pg_to_ch  │  Source: postgres:5432  │  Dest: clickhouse    │
│  Slot: peerdb_slot │  Publication: peerdb_publication               │
│  Engine destino: ReplacingMergeTree(updated_at)                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ Native protocol :9000
                       ▼ [profile: analytics]
┌─────────────────────────────────────────────────────────────────────┐
│  CLICKHOUSE 25.x  :8123(HTTP) :9000(native)  [aura_internal]        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  aura_raw   │  │ aura_silver  │  │       aura_gold          │   │
│  │  (Bronze)   │  │  (Silver)    │  │        (Gold)            │   │
│  │ ← PeerDB    │  │ ← dbt stg   │  │  ← dbt marts             │   │
│  │  Raw CDC    │  │  + int_*    │  │  fct_sales, dim_products  │   │
│  │ FINAL query │  │  views      │  │  (Cube + Superset)        │   │
│  └─────────────┘  └──────────────┘  └──────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
          ┌────────────┴──────────────────┐
          │                               │
          ▼ [profile: analytics]          ▼
┌──────────────────────┐    ┌─────────────────────────────────────┐
│  DBT-RUNNER          │    │   CUBE.JS v1.6.19  :4000 :15432     │
│  dbt-clickhouse 1.8  │    │   CUBEJS_DB_TYPE=clickhouse         │
│  Project: /dbt_aura  │    │   Source: aura_gold.*               │
│  Bronze→Silver→Gold  │    │   SQL API: :15432 (PG wire protocol)│
│  Triggered by Prefect│    │   Pre-aggs → Valkey DB1             │
└──────────────────────┘    └──────────────┬──────────────────────┘
                                           │ SQL :15432
                       ┌───────────────────┼───────────────────────┐
                       ▼                   ▼                       ▼
              ┌──────────────┐   ┌──────────────────┐   ┌─────────────────┐
              │  VANNA AI    │   │    FLOWISE       │   │  SUPERSET       │
              │  :8011       │   │    :3001         │   │  (también query)│
              │  NL→SQL via  │   │  AI Chatbot via  │   │  aura_gold via  │
              │  Cube SQL API│   │  Cube SQL API    │   │  clickhouse-conn│
              └──────────────┘   └──────────────────┘   └─────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  VALKEY 9.0.3  :6379  [aura_internal]                               │
│  DB0: Celery (Superset tasks)                                        │
│  DB1: Cube pre-aggregations (Rollups)                               │
│  DB2: Superset filter state cache                                    │
│  DB3: Superset data cache                                           │
│  DB4: Superset thumbnail cache                                      │
│  DB5: Rate limiting                                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  PREFECT v3  :4200  [aura_internal]                                  │
│  Flows disponibles:                                                  │
│    • ml_sales_pipeline.py → ML + Cube refresh                       │
│    • dbt_run_flow.py      → dbt run + dbt test (TODO: crear)        │
│    • peerdb_health.py     → Monitor latencia CDC (TODO: crear)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. ÁRBOL DE ARCHIVOS CRÍTICOS

```
superset/                           ← RAÍZ DEL PROYECTO
│
├── .agent/                         ← MEMORIA DEL AGENTE (no tocar sin razón)
│   ├── RULES.md                    ← Reglas inmutables
│   ├── MAP.md                      ← Este archivo
│   ├── AGENT.md                    ← Estándares de codificación
│   ├── CONTEXT.md                  ← Visión técnica y justificaciones
│   ├── STATE.md                    ← Estado actual y deudas técnicas
│   ├── BRAIN/                      ← RAG interno (ChromaDB index)
│   │   ├── bootstrap.py            ← Script de indexación vectorial
│   │   ├── query_brain.py          ← Query helper para el agente
│   │   └── chroma_db/              ← Base de datos vectorial local
│   ├── DECISIONS/                  ← ADR (Architecture Decision Records)
│   │   ├── 20260106_valkey_vs_redis.md
│   │   └── 20260414_clickhouse_mds.md
│   └── MCP/                        ← Model Context Protocol tools
│       ├── docker_tools.py         ← Herramientas Docker para el agente
│       ├── clickhouse_tools.py     ← Herramientas ClickHouse
│       └── keycloak_tools.py       ← Herramientas Keycloak
│
├── .mcp/
│   └── server-config.json          ← Configuración servidor MCP
│
├── docker-compose.yml              ← Orquestación de servicios (v7.5 MDS)
├── nginx.conf                      ← Gateway único (172.28.0.0/16)
├── prometheus.yml                  ← Scrape jobs: CH, PeerDB, Postgres, etc.
├── superset_config.py              ← Configuración Python de Superset
├── custom_security_manager.py      ← OIDC con Keycloak
│
├── docker/
│   ├── superset/Dockerfile         ← +clickhouse-connect, +playwright
│   ├── dbt/Dockerfile              ← dbt-clickhouse + great-expectations
│   ├── clickhouse/
│   │   ├── config.xml              ← Prometheus endpoint, LZ4, timezone
│   │   └── users.xml               ← superset_ro readonly user
│   ├── grafana/provisioning/       ← Dashboards auto-provisioning
│   └── postgres/init_sales_db.sql  ← Schema ventas + datos semilla
│
├── dbt_aura/                       ← Proyecto dbt (Medallón)
│   ├── dbt_project.yml             ← Config adaptador clickhouse
│   ├── profiles.yml                ← Conexión HTTP ClickHouse
│   └── models/
│       ├── staging/                 ← Bronze→Silver (stg_*)
│       │   ├── sources.yml
│       │   ├── stg_orders.sql
│       │   ├── stg_products.sql
│       │   └── stg_users.sql
│       ├── intermediate/            ← Silver joins (int_*)  [TODO]
│       └── marts/                   ← Gold final (fct_*, dim_*)
│           └── fct_sales.sql
│
├── cube_schema/                    ← Cubos Cube.js (YAML/JS)
├── prefect_flows/
│   └── ml_sales_pipeline.py        ← Pipeline ML + Cube refresh
├── vanna-ai/
│   └── main.py                     ← Vanna AI Flask API (→ Cube SQL API)
├── scripts/
│   ├── init_mds.sql                ← Postgres: WAL slot + publicación
│   └── init_clickhouse.sh          ← ClickHouse: DBs + tablas + usuarios
│
├── .agent/BRAIN/bootstrap.py       ← Indexación RAG de este repo
└── .mcp/server-config.json         ← Permisos MCP
```

---

## 3. PUERTOS Y RUTAS (Referencia Rápida)

| Servicio            | Puerto Interno | Ruta Nginx         | Notas                          |
|---------------------|----------------|--------------------|--------------------------------|
| Superset            | 8088           | `/`                | UI principal                   |
| Cube REST API       | 4000           | `/cubejs/`         | Playground + REST              |
| Cube SQL API        | 15432          | Directo (interno)  | PostgreSQL wire protocol       |
| ClickHouse HTTP     | 8123           | Directo (interno)  | Solo desde servicios internos  |
| ClickHouse Native   | 9000           | Directo (interno)  | PeerDB + dbt                   |
| PeerDB UI           | 8085           | `/peerdb/`         | CDC management                 |
| Prefect UI          | 4200           | `/prefect/`        | Workflow orchestration         |
| Grafana             | 3000           | `/grafana/`        | Dashboards observabilidad      |
| Prometheus          | 9090           | `/prometheus/`     | Métricas raw                   |
| Keycloak            | 8080           | `/auth/`           | OIDC IdP                       |
| Flowise             | 3001           | `/flowise/`        | AI chatbot builder             |
| Vanna AI            | 8011           | `/vanna/`          | NL→SQL (via Cube)              |
| Superset MCP        | 8010           | `/mcp/`            | SSE para agentes externos      |
| cAdvisor            | 8080           | `/cadvisor/`       | Container metrics              |
| Valkey              | 6379           | No expuesto        | Cache interno                  |
| statsd-exporter     | 9102/9125      | No expuesto        | Métricas StatsD                |
| postgres-exporter   | 9187           | No expuesto        | Postgres metrics               |

---

## 4. VARIABLES DE ENTORNO CRÍTICAS (rápida referencia)

Ver `.env.example` para la lista completa. Las más críticas:

```bash
SECRET_KEY          # Superset + Cube API auth — NEVER default en producción
CLICKHOUSE_USER     # aura
CLICKHOUSE_PASSWORD # Ver Vault: secret/aura/clickhouse
POSTGRES_USER       # superset
POSTGRES_PASSWORD   # Ver Vault: secret/aura/postgres
OPENAI_API_KEY      # Ver Vault: secret/aura/openai
SERVER_IP           # IP del host para URLs externas
```
