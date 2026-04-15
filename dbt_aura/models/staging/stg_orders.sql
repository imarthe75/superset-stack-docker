-- =============================================================================
-- Modelo: stg_orders.sql (Staging — Bronze → Silver)
-- Fuente: aura_raw.orders (replicado por PeerDB desde PostgreSQL)
-- Destino: aura_silver.stg_orders
-- =============================================================================
-- Propósito:
--   1. Filtra registros eliminados (soft-deletes del CDC).
--   2. Limpia y castea tipos de datos.
--   3. Normaliza el campo 'status' a valores conocidos.
--   4. Deduplica usando FINAL (resuelve duplicados de ReplacingMergeTree).
-- =============================================================================

{{
    config(
        materialized = 'view',
        schema = 'aura_silver',
        tags = ['staging', 'orders']
    )
}}

SELECT
    id                                                AS order_id,
    user_id,
    product_id,
    -- Normalizar status a values controlados
    CASE
        WHEN lower(trim(status)) = 'completed'  THEN 'completed'
        WHEN lower(trim(status)) = 'cancelled'  THEN 'cancelled'
        WHEN lower(trim(status)) = 'pending'    THEN 'pending'
        WHEN lower(trim(status)) = 'refunded'   THEN 'refunded'
        ELSE 'unknown'
    END                                               AS order_status,
    toDecimal64(amount, 2)                            AS amount_usd,
    toDate(order_date)                                AS order_date,
    toStartOfMonth(order_date)                        AS order_month,
    toYear(order_date)                                AS order_year,
    toStartOfWeek(order_date, 1)                      AS order_week_start,
    -- Metadatos de replicación (para debugging y auditoría)
    updated_at                                        AS source_updated_at,
    _peerdb_synced_at                                 AS replicated_at

FROM {{ source('aura_raw', 'orders') }} FINAL   -- FINAL resuelve duplicados ReplacingMergeTree

WHERE
    _peerdb_is_deleted = 0                          -- Excluir registros deleted en Postgres
    AND amount > 0                                   -- Filtrar registros inválidos
    AND order_date IS NOT NULL
