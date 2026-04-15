-- =============================================================================
-- Modelo: stg_products.sql (Staging — Bronze → Silver)
-- Fuente: aura_raw.products
-- =============================================================================

{{
    config(
        materialized = 'view',
        schema = 'aura_silver',
        tags = ['staging', 'products']
    )
}}

SELECT
    id                          AS product_id,
    trim(name)                  AS product_name,
    trim(category)              AS category,
    toDecimal64(price, 2)       AS price_usd,
    updated_at                  AS source_updated_at,
    _peerdb_synced_at           AS replicated_at

FROM {{ source('aura_raw', 'products') }} FINAL

WHERE _peerdb_is_deleted = 0
