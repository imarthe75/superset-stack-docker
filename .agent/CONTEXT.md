# CONTEXT.md (v8.0) — Aura Intelligence: Campos Críticos, Validaciones y Knowledge Base

## Visión: Modern Data Stack Operacionalizado

**Aura Intelligence Suite** v8.0 integra:
- **Inyestion en tiempo real** (CDC via PeerDB)
- **Transformaciones codificadas** (dbt + ClickHouse)
- **Capa semántica normalizada** (Cube.js)
- **IA augmented analytics** (Vanna AI + Flowise)
- **Memoria interna del agente** (ChromaDB + brain_index.py)

---

## 1. CAMPOS CRÍTICOS POR DOMINIO

### Dominio: Ventas (Sales)

**Tabla:** `aura_bronze.sales` → `aura_silver.stg_sales` → `aura_gold.fct_sales`

| Campo | Tipo | Obligatorio | Validación | Enriquecimiento |
|-------|------|-------------|------------|-----------------|
| `order_id` | UUID | ✅ | Crear PK, no NULL | Generar UUID v4 si falta |
| `customer_id` | Int64 | ✅ | FK → dim_customer | Buscar en golden sets |
| `product_id` | Int64 | ✅ | FK → dim_product | Lookup de catálogo |
| `amount` | Decimal(18,2) | ✅ | > 0, ≤ 999999.99 | Validar contra presupuesto |
| `currency` | String(3) | ✅ | Enum: MXN, USD, EUR | Default: MXN |
| `created_at` | DateTime | ✅ | Entre 2020-01-01 y HOY | Usar NOW() si falta |
| `updated_at` | DateTime | ⚠️ | Si es UPDATE, ≥ created_at | Auto-set en SCD2 |
| `status` | String | ⚠️ | Enum: pending, confirmed, cancelled | Default: pending |
| `region_id` | Int64 | ⚠️ | FK → dim_region | Geolocalizar si falta |
| `is_deleted` | Boolean | ✅ | Soft-delete marker | Default: false |
| `version` | UInt64 | ✅ | CDC version (ReplacingMergeTree) | Auto-increment |

**Validaciones dbt:**
```yaml
models:
  - name: fct_sales
    tests:
      - unique:
          column_name: order_id
      - not_null: [order_id, customer_id, amount]
      - accepted_values:
          column_name: currency
          values: ['MXN', 'USD', 'EUR']
      - relationships:
          column_name: customer_id
          to: ref('dim_customer')
```

### Dominio: Clientes (Customer)

**Tabla:** `aura_bronze.customers` → `aura_silver.stg_customers` → `aura_gold.dim_customer`

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `customer_id` | Int64 | ✅ | PK, no duplicados |
| `name` | String | ✅ | Regex: `[a-zA-Z\s]{3,100}` |
| `email` | String | ✅ | Regex RFC 5322 válido |
| `phone` | String | ⚠️ | Formato E.164 si presente |
| `country` | String(2) | ✅ | ISO 3166-1 alpha-2 |
| `segment` | String | ⚠️ | Enum: premium, standard, vip |
| `lifetime_value` | Decimal(18,2) | ✅ | ≥ 0 |
| `created_at` | DateTime | ✅ | Valid date, ≤ NOW() |
| `is_active` | Boolean | ✅ | RLS filter key |
| `is_deleted` | Boolean | ✅ | Soft-delete |

### Dominio: Productos (Catalog)

**Tabla:** `aura_bronze.products` → `aura_silver.stg_products` → `aura_gold.dim_product`

| Campo | Tipo | Obligatorio | Validación |
|-------|------|-------------|------------|
| `product_id` | Int64 | ✅ | PK, no cambiar |
| `sku` | String | ✅ | Unique, Regex: `^[A-Z0-9\-]{5,20}$` |
| `name` | String | ✅ | No vacío, ≤ 200 chars |
| `category_id` | Int64 | ✅ | FK → dim_category |
| `price` | Decimal(18,2) | ✅ | > 0 |
| `cost` | Decimal(18,2) | ⚠️ | ≤ price |
| `stock_quantity` | Int64 | ✅ | ≥ 0 |
| `is_discontinued` | Boolean | ✅ | SCD2 marker |

---

## 2. MÉTRICAS DE CALIDAD

Por cada tabla, validar:

- **Completeness**: NULL count ≤ 5% en columnas críticas
- **Uniqueness**: No duplicados en PK
- **Timeliness**: CDC lag < 30s
- **Accuracy**: Sample validation vs source
- **Consistency**: Valores en rango, formatos válidos, integridad FK

---

## 3. INDEXACIÓN DE MEMORIA (ChromaDB + brain_index.py)

**Estado actual (v8.0):**

| Fuente | Campos indexados | Tests | Golden Sets | Status |
|--------|-----------------|-------|-------------|--------|
| fct_sales | 12 | 8 | 3 ejemplos | ✅ |
| dim_customer | 10 | 6 | 2 ejemplos | ✅ |
| dim_product | 9 | 5 | 2 ejemplos | ⏳ |
| Lineage metadata | - | - | - | ✅ |

**Uso:**
```bash
# Indexar todo
python .agent/brain_index.py --index

# Buscar semánticamente
python .agent/brain_index.py --query "¿cómo se calcula lifetime_value?"

# Modo daemon (6h refresh)
python .agent/brain_index.py --daemon
```

---

## 4. INTEGRACIÓN VANNA AI + ChromaDB

Cuando usuario pregunta: "¿Cuál fue la venta más grande del mes?"

1. Vanna AI busca golden sets → ChromaDB query
2. Valida campos vs CONTEXT.md
3. Genera SQL sobre Cube SQL API
4. Retorna con linaje de datos

---

**Versión:** 8.0  
**Última actualización:** 2026-04-15  
**Próxima revisión:** Cuando se agreguen nuevas fuentes

---

## 1. VISIÓN DEL PROYECTO

**Aura Intelligence Suite** es una plataforma de inteligencia de negocio de alto rendimiento construida sobre el Modern Data Stack (MDS). Su objetivo es proporcionar análisis en tiempo (sub)real sobre datos operacionales, eliminando la contención de recursos entre la carga transaccional (OLTP) y la analítica (OLAP).

### Problema que Resuelve
El stack anterior ejecutaba consultas analíticas pesadas directamente en PostgreSQL, compitiendo con escrituras transaccionales, causando:
- Degradación de rendimiento en horas pico.
- Imposibilidad de ejecutar agregaciones sobre millones de filas en < 1s.
- Sin linaje de datos ni capa semántica: cada analista calculaba métricas de forma diferente → inconsistencias.

### Solución: Arquitectura Desacoplada (Medallón + MDS)
```
[PostgreSQL OLTP] → (CDC/WAL) → [PeerDB] → [ClickHouse OLAP] → [dbt] → [Cube Semántica] → [Superset / AI]
```

---

## 2. JUSTIFICACIÓN TÉCNICA DE CADA COMPONENTE

### 2.1 PeerDB — Change Data Capture (CDC)
- **¿Por qué PeerDB?** Es el único CDC nativo para PostgreSQL → ClickHouse con soporte oficial para `ReplacingMergeTree`. Alternativas (Debezium, Airbyte) requieren Kafka o más infraestructura.
- **Mecanismo:** Usa **logical replication** (WAL) de Postgres 14+. El slot de replicación `peerdb_slot` captura cada INSERT/UPDATE/DELETE y los replica en tiempo real a ClickHouse.
- **Latencia objetivo:** < 5 segundos desde escritura en OLTP hasta disponibilidad en OLAP.
- **Documentación oficial:** https://docs.peerdb.io

### 2.2 ClickHouse — Motor OLAP
- **¿Por qué ClickHouse?** Benchmarks demuestran 100-1000x de mejora en consultas analíticas vs PostgreSQL en datasets > 10M filas. Motor columnar con compresión nativa.
- **Motor de tabla:** `ReplacingMergeTree(updated_at)` en tablas replicadas desde Postgres. ClickHouse fusiona duplicados (causados por CDC) en background usando la columna de versión.
- **Esquemas:**
  - `aura_raw` → datos tal cual vienen de PeerDB (Bronze).
  - `aura_silver` → transformaciones dbt (Silver).
  - `aura_gold` → modelos finales para Cube/Superset (Gold).
- **Puerto expuesto internamente:** 8123 (HTTP), 9000 (Native protocol).
- **Documentación oficial:** https://clickhouse.com/docs

### 2.3 dbt (data build tool) — Capa de Transformación
- **¿Por qué dbt?** Transformaciones como código versionado en Git. Genera linaje automático, tests de calidad y documentación. Integración nativa con ClickHouse via `dbt-clickhouse`.
- **Adaptador:** `dbt-clickhouse` (profile `clickhouse`).
- **Directorio del proyecto:** `./dbt_aura/`
- **Estructura de modelos:**
  ```
  dbt_aura/
  ├── models/
  │   ├── staging/     (Bronze → Silver: stg_orders, stg_products, stg_users)
  │   ├── intermediate/ (Silver: joins, limpieza)
  │   └── marts/       (Gold: fct_sales, dim_products, mrt_cohort_analysis)
  ├── tests/           (dbt tests + Great Expectations)
  ├── dbt_project.yml
  └── profiles.yml
  ```
- **Orquestación:** Prefect v3 dispara `dbt run` + `dbt test` en schedule o on-demand.
- **Documentación oficial:** https://docs.getdbt.com/reference/warehouse-setups/clickhouse-setup

### 2.4 Cube.js — Capa Semántica
- **¿Por qué Cube?** Actúa como "single source of truth" para métricas. Define KPIs una sola vez; todos los consumidores (Superset, Flowise, Vanna AI) los consultan via SQL API o REST API garantizando consistencia.
- **Fuente de datos:** ClickHouse (tablas Gold de dbt). `CUBEJS_DB_TYPE=clickhouse`.
- **Pre-agregaciones (Rollups):** Almacenadas en **Valkey** (Redis-compatible). Respuestas < 50ms para queries pre-calculadas.
- **SQL API:** Expone puerto `15432` (PostgreSQL wire protocol). Flowise y Vanna AI se conectan aquí, no directamente a ClickHouse.
- **Documentación oficial:** https://cube.dev/docs/product/configuration/data-sources/clickhouse

### 2.5 Valkey v9.0.3 — Cache de Pre-agregaciones
- **¿Por qué Valkey?** Fork open-source de Redis 7.2 (sin licencia SSPL). Compatible 100% con redis-py. Usado como:
  1. Cache de Celery (Superset tasks).
  2. Store de pre-agregaciones de Cube (Rollups).
- **Configuración:** `appendonly yes` para persistencia. Separar DBs: DB 0 para Celery, DB 1 para Cube.

### 2.6 Prefect v3 — Orquestación
- **Flows disponibles:**
  - `dbt_run_flow`: ejecuta `dbt run --select +fct_sales+` y `dbt test`.
  - `great_expectations_flow`: valida calidad de datos en tablas Gold.
  - `peerdb_health_check_flow`: alerta si la latencia de replicación > 30s.
- **Schedule:** Nightly full-refresh a las 02:00 UTC. Incremental cada hora.

---

## 3. FLUJO DE DATOS END-TO-END

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCCIÓN / OLTP                        │
│  PostgreSQL 18 (sales_data DB)                              │
│  Tables: users, orders, products, support_tickets           │
└───────────────────┬──────────────────────────────────────────┘
                    │ WAL logical replication (slot: peerdb_slot)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   PeerDB (CDC Engine)                        │
│  Mirror: pg_to_ch (PostgreSQL → ClickHouse)                 │
│  Engine: ReplacingMergeTree                                  │
└───────────────────┬──────────────────────────────────────────┘
                    │ Native ClickHouse protocol (port 9000)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              ClickHouse Server (OLAP)                        │
│  aura_raw.*    ← PeerDB (Bronze)                            │
│  aura_silver.* ← dbt staging/intermediate (Silver)          │
│  aura_gold.*   ← dbt marts (Gold)                           │
└──────────┬────────────────────────┬────────────────────────-─┘
           │ dbt-clickhouse         │ clickhouse-connect
           ▼                        ▼
┌──────────────────┐    ┌──────────────────────────────────────┐
│   dbt_aura       │    │         Cube.js (Semántica)           │
│   (Transform)    │    │  SQL API :15432 / REST API :4000      │
│   Prefect trigger│    │  Pre-aggs en Valkey DB1               │
└──────────────────┘    └────────────┬─────────────────────────┘
                                     │ SQL queries
                    ┌────────────────┼────────────────────┐
                    ▼                ▼                     ▼
             ┌──────────┐   ┌──────────────┐   ┌─────────────────┐
             │ Superset │   │  Vanna AI    │   │    Flowise      │
             │ (BI/Viz) │   │  (Chat SQL)  │   │  (AI Chatbot)   │
             └──────────┘   └──────────────┘   └─────────────────┘
```

---

## 4. SEGURIDAD Y GOBERNANZA

| Aspecto          | Implementación                                      |
|------------------|-----------------------------------------------------|
| Autenticación    | Keycloak v26.5 OIDC → Superset, Grafana, Flowise    |
| Secrets          | HashiCorp Vault (paths en `AGENT.md §3.1`)          |
| Red Docker       | `aura_internal` (backend) + `aura_public` (nginx)   |
| TLS              | Nginx termina TLS; tráfico interno en HTTP plano    |
| Auditoría        | Superset audit logs → Postgres `superset` DB        |
| Calidad de datos | dbt tests + Great Expectations en Prefect flows     |

---

## 5. DEUDAS TÉCNICAS CONOCIDAS (Ver STATE.md para estado actual)
1. **Vault en producción:** Actualmente se usa `.env`. Migrar a Vault Agent Injector.
2. **TLS interno:** Comunicación ClickHouse ↔ PeerDB en texto plano dentro de Docker.
3. **ClickHouse Keeper:** Usando modo standalone (sin ZooKeeper/Keeper cluster). OK para < 100GB.
4. **Keycloak DB:** Usando H2 embebido (solo dev). Migrar a Postgres para producción.
5. **PeerDB UI:** No expuesto via Nginx. Agregar `/peerdb/` location cuando se establezca RBAC.
