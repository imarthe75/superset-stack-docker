-- =============================================================================
-- Modelo: fct_sales.sql (Mart Gold — tabla de hechos principal)
-- Fuente: aura_silver.stg_orders + stg_products + stg_users
-- Destino: aura_gold.fct_sales
-- Consumidores: Cube.js (Semántica), Superset (BI), Vanna AI (Chat)
-- =============================================================================
-- Este es el modelo central de la arquitectura Aura.
-- Todas las métricas de ventas deben derivarse de esta tabla.
-- =============================================================================

{{
    config(
        materialized = 'table',
        schema = 'aura_gold',
        engine = 'MergeTree()',
        order_by = ['order_date', 'category', 'country'],
        partition_by = 'toYYYYMM(order_date)',
        tags = ['mart', 'sales', 'gold']
    )
}}

SELECT
    o.order_id,
    o.user_id,
    o.product_id,

    -- Dimensiones de producto
    p.product_name,
    p.category,
    p.price_usd                            AS unit_price_usd,

    -- Dimensiones de usuario/geografía
    u.user_name,
    u.email,
    u.country,
    u.signup_date,

    -- Métricas de orden
    o.order_status,
    o.amount_usd,
    -- Margen aproximado (precio unitario vs monto real)
    o.amount_usd - p.price_usd            AS gross_margin_usd,

    -- Dimensiones de tiempo
    o.order_date,
    o.order_month,
    o.order_year,
    o.order_week_start,
    toDayOfWeek(o.order_date)              AS day_of_week,         -- 1=Mon, 7=Sun
    toDayOfMonth(o.order_date)             AS day_of_month,

    -- Flags calculados
    if(o.order_status = 'completed', 1, 0) AS is_completed,
    if(o.order_status = 'cancelled', 1, 0) AS is_cancelled,

    -- Metadatos de pipeline
    o.replicated_at                        AS data_replicated_at,
    now()                                  AS dbt_updated_at

FROM {{ ref('stg_orders') }} AS o
LEFT JOIN {{ ref('stg_products') }} AS p ON o.product_id = p.product_id
LEFT JOIN {{ ref('stg_users') }}    AS u ON o.user_id    = u.user_id

WHERE o.order_status != 'unknown'   -- Excluir registros con status inválido
