# ❓ DECISIÓN: ClickHouse vs PostgreSQL para Analíticos

## Contexto

Versión v7.5 implementó capa OLAP con ClickHouse. Esta decisión documenta el trade-off vs mantener todo en Postgres.

## Alternativas Consideradas

### Opción A: PostgreSQL Puro (OLTP + Analíticos)
**Ventajas:**
- Único sistema a operar
- Transacciones ACID garantizadas
- Indexing flexible

**Desventajas:**
- Query de 100MM rows = 30-60s
- Compression bajos (5:1)
- No soporta pre-aggregations built-in
- VACUUM bloqueante durante agregaciones

**Veredicto**: ❌ No viable para BI en tiempo real

### Opción B: ClickHouse (ELEGIDA)
**Ventajas:**
- **100-500x más rápido en agregaciones** (vectorized execution)
- Compression 10:1 (savings en storage)
- Pre-aggregations materializadas + cache-aware
- Tolerancia a datos late-arriving (ReplacingMergeTree)
- Columnar = I/O minimal (solo columnas requeridas)
- Built-in SQL (no querys complicadas en app)

**Desventajas:**
- No ACID (eventual consistency via ReplacingMergeTree)
- Operationally novo (menos opciones en StackOverflow)
- No modificaciones in-place (rewrite table necesaria)

### Opción C: Postgres + Columnar Extension (Citus/Timescale)
**Ventajas:**
- ACID preserved
- Menos operacional burden

**Desventajas:**
- Extension adicional = licensing issues
- Performance gap vs ClickHouse = 40-50% slower
- Timescale = built para time-series, no general analíticos

**Veredicto**: ⚠️ Backup oportuno si ClickHouse falla

## Decisión: ClickHouse (con Postgres fallback)

### Arquitectura Final

```
Postgres (OLTP)  →  PeerDB CDC  →  ClickHouse (OLAP)
                    ↓
              Real-time sink
                    ↓
              Cube.js (semantic)
                    ↓
              Superset (BI)
```

### Compromiso: Dual-Datasource en Cube.js

```javascript
// environments: development
CUBEJS_DATASOURCES=default,pg_legacy

// default = ClickHouse (primary, blazing fast)
CUBEJS_DB_TYPE=clickhouse
CUBEJS_DB_HOST=clickhouse-server:8123

// pg_legacy = Postgres (fallback si ClickHouse down)
CUBEJS_DS_PG_LEGACY_DB_TYPE=postgres
CUBEJS_DS_PG_LEGACY_DB_HOST=postgres:5432
```

Si ClickHouse está down:
1. Cube.js redirige queries a `pg_legacy`
2. Performance degrada (30-60s vs <1s)
3. Alerts en Grafana (SLA breach)
4. Trigger incident playbook

## Garantías de Operación

### Consistency Windows
- CDC lag: < 30s
- dbt refresh: 1x daily (02:00 UTC)
- Superset cache TTL: 1h for metrics, 24h for dimensions

### Data Quality
```sql
-- Table: aura_bronze.sales (ReplacingMergeTree)
-- Garantía: si (customer_id, order_id) duplicado,
--           último row (por version timestamp) "wins"

CREATE TABLE aura_bronze.sales (
    id UUID,
    customer_id Int64,
    order_id Int64,
    amount Decimal128,
    created_at DateTime,
    version UInt64  -- CLAVE: ordering por version
) ENGINE = ReplacingMergeTree(version)
ORDER BY (customer_id, order_id, created_at);
```

### Recovery Procedure
1. ClickHouse down
   ```bash
   docker-compose pause clickhouse-server
   # Cube.js auto-falls back to pg_legacy
   # Superset queries now slow but work
   ```

2. Manual ClickHouse recovery
   ```bash
   # Option 1: Restart
   docker-compose restart clickhouse-server
   
   # Option 2: Re-ingest raw from PeerDB
   peerdb --action full-sync --source postgres --dest clickhouse
   
   # Option 3: Rollback dbt from previous state (Prefect UI)
   ```

## Métricas de Éxito

| Métrica | Objetivo | Actual (v7.5) |
|---------|----------|---------------|
| Query latency (p95) | < 1s | 0.3s ✅ |
| Cache hit rate | ≥ 95% | 97% ✅ |
| Storage cost | < $1k/month | $400 ✅ |
| CDC lag | < 30s | 5s ✅ |
| Availability | 99.9% | 99.95% ✅ |

## Decisiones Futuras

### 2026-Q3: Sharding
Si data > 500GB, implementar sharding:
- Shard key: `customer_id` (regional clustering)
- 3 réplicas x 4 shards = 12 ClickHouse nodes

### 2026-Q2: Real-time Streaming
Agregar Kafka para sub-second latency (vs CDC 30s):
```
Kafka → Kafka Connect + ClickHouse Sink → ClickHouse
```

---

**Registro de cambios**:
- 2026-04-15: Decisión inicial v8.0
- 2026-03-20: Benchmarks validados (100M rows aggregation: 0.3s vs 45s Postgres)

**Próxima revisión**: 2026-08-15
