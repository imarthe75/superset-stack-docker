#!/usr/bin/env bash
# =============================================================================
# Aura Intelligence Suite v7.5 — Inicialización ClickHouse
# Archivo: scripts/init_clickhouse.sh
# Ejecutar DESPUÉS de que el contenedor clickhouse-server esté healthy.
# Uso: ./scripts/init_clickhouse.sh
# =============================================================================

set -euo pipefail

CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-8123}"
CLICKHOUSE_USER="${CLICKHOUSE_USER:-aura}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-aura_secure_pass}"

CH_CMD=(clickhouse-client
  --host "$CLICKHOUSE_HOST"
  --port 9000
  --user "$CLICKHOUSE_USER"
  --password "$CLICKHOUSE_PASSWORD"
)

echo "🔷 [1/4] Creando bases de datos (Medallón: Bronze → Silver → Gold)..."

docker compose exec clickhouse-server clickhouse-client \
  --user "$CLICKHOUSE_USER" \
  --password "$CLICKHOUSE_PASSWORD" \
  --multiquery <<'SQL'

-- =============================================================================
-- BASES DE DATOS (Arquitectura Medallón)
-- =============================================================================
CREATE DATABASE IF NOT EXISTS aura_raw    ENGINE = Atomic;  -- Bronze (PeerDB raw)
CREATE DATABASE IF NOT EXISTS aura_silver ENGINE = Atomic;  -- Silver (dbt staging)
CREATE DATABASE IF NOT EXISTS aura_gold   ENGINE = Atomic;  -- Gold   (dbt marts)


-- =============================================================================
-- CAPA BRONZE: aura_raw — Tablas replicadas por PeerDB
-- Motor: ReplacingMergeTree para manejar upserts del CDC sin duplicados.
-- La columna updated_at actúa como "versión": ClickHouse conserva el registro
-- más reciente tras el proceso de merging en background.
-- =============================================================================

CREATE TABLE IF NOT EXISTS aura_raw.users (
    id            UInt64,
    name          String,
    email         String,
    country       String,
    created_at    DateTime64(3, 'America/Mexico_City'),
    updated_at    DateTime64(3, 'America/Mexico_City') DEFAULT now(),
    _peerdb_is_deleted  UInt8  DEFAULT 0,       -- PeerDB marca eliminaciones lógicas
    _peerdb_synced_at   DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY (id)
SETTINGS index_granularity = 8192;


CREATE TABLE IF NOT EXISTS aura_raw.products (
    id            UInt64,
    name          String,
    category      String,
    price         Decimal(10, 2),
    updated_at    DateTime64(3, 'America/Mexico_City') DEFAULT now(),
    _peerdb_is_deleted  UInt8  DEFAULT 0,
    _peerdb_synced_at   DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (id)
SETTINGS index_granularity = 8192;


CREATE TABLE IF NOT EXISTS aura_raw.orders (
    id            UInt64,
    user_id       UInt64,
    product_id    UInt64,
    status        LowCardinality(String),  -- 'completed', 'cancelled', etc.
    amount        Decimal(10, 2),
    order_date    Date,
    updated_at    DateTime64(3, 'America/Mexico_City') DEFAULT now(),
    _peerdb_is_deleted  UInt8  DEFAULT 0,
    _peerdb_synced_at   DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(order_date)
ORDER BY (id, order_date)
SETTINGS index_granularity = 8192;


CREATE TABLE IF NOT EXISTS aura_raw.support_tickets (
    id            UInt64,
    user_id       UInt64,
    subject       String,
    priority      LowCardinality(String),
    status        LowCardinality(String),
    updated_at    DateTime64(3, 'America/Mexico_City') DEFAULT now(),
    _peerdb_is_deleted  UInt8  DEFAULT 0,
    _peerdb_synced_at   DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (id)
SETTINGS index_granularity = 8192;


CREATE TABLE IF NOT EXISTS aura_raw.ml_prediccion_ventas (
    id                  UInt64,
    fecha               Date,
    prediccion_monto    Decimal(10, 2),
    timestamp_ejecucion DateTime64(3, 'America/Mexico_City') DEFAULT now(),
    updated_at          DateTime64(3, 'America/Mexico_City') DEFAULT now(),
    _peerdb_is_deleted  UInt8  DEFAULT 0,
    _peerdb_synced_at   DateTime64(3, 'UTC') DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(fecha)
ORDER BY (id, fecha)
SETTINGS index_granularity = 8192;


-- =============================================================================
-- CAPA GOLD: aura_gold — Tablas finales para Cube.js / Superset
-- Creadas por dbt como vistas o tablas materializadas.
-- Los siguientes son placeholders que dbt sobreescribirá.
-- =============================================================================

CREATE TABLE IF NOT EXISTS aura_gold.fct_sales (
    order_id        UInt64,
    user_id         UInt64,
    product_id      UInt64,
    product_name    String,
    category        LowCardinality(String),
    country         LowCardinality(String),
    status          LowCardinality(String),
    amount          Decimal(10, 2),
    order_date      Date,
    order_month     Date,
    order_year      UInt16
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(order_date)
ORDER BY (order_date, category, country)
SETTINGS index_granularity = 8192;


CREATE TABLE IF NOT EXISTS aura_gold.dim_products (
    product_id      UInt64,
    name            String,
    category        LowCardinality(String),
    price           Decimal(10, 2),
    updated_at      DateTime64(3, 'America/Mexico_City')
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (product_id)
SETTINGS index_granularity = 8192;


-- =============================================================================
-- USUARIO READONLY para Superset (principio de mínimo privilegio)
-- =============================================================================
CREATE USER IF NOT EXISTS superset_ro
IDENTIFIED WITH plaintext_password BY 'superset_readonly_pass';

GRANT SELECT ON aura_gold.* TO superset_ro;
GRANT SELECT ON aura_silver.* TO superset_ro;


-- =============================================================================
-- VERIFICACIÓN FINAL
-- =============================================================================
SELECT
    name       AS database,
    engine     AS engine,
    countIf(type = 'Table') AS tables
FROM system.tables
WHERE database IN ('aura_raw', 'aura_silver', 'aura_gold')
GROUP BY database, engine
ORDER BY database;

SQL

echo "✅ [4/4] ClickHouse inicializado correctamente."
echo ""
echo "📋 Resumen:"
echo "  Bases de datos: aura_raw (Bronze), aura_silver (Silver), aura_gold (Gold)"
echo "  Tablas raw: users, orders, products, support_tickets, ml_prediccion_ventas"
echo "  Tablas gold: fct_sales, dim_products (placeholders para dbt)"
echo "  Usuario readonly: superset_ro (acceso solo a aura_silver y aura_gold)"
echo ""
echo "🚀 Próximo paso: Configurar mirror PeerDB desde http://localhost:8085"
echo "   Mirror name: pg_to_ch"
echo "   Source: postgres (host=postgres, port=5432)"
echo "   Destination: clickhouse-server (host=clickhouse-server, port=9000)"
echo "   Destination DB: aura_raw"
echo "   Publication: peerdb_publication"
echo "   Slot: peerdb_slot"
