-- =============================================================================
-- Modelo: stg_users.sql (Staging — Bronze → Silver)
-- Fuente: aura_raw.users
-- =============================================================================

{{
    config(
        materialized = 'view',
        schema = 'aura_silver',
        tags = ['staging', 'users']
    )
}}

SELECT
    id                                      AS user_id,
    trim(name)                              AS user_name,
    lower(trim(email))                      AS email,
    trim(country)                           AS country,
    -- Normalizar país a código ISO si es posible (extensible)
    toDate(created_at)                      AS signup_date,
    toStartOfMonth(toDate(created_at))      AS signup_month,
    toYear(toDate(created_at))              AS signup_year,
    updated_at                              AS source_updated_at,
    _peerdb_synced_at                       AS replicated_at

FROM {{ source('aura_raw', 'users') }} FINAL

WHERE _peerdb_is_deleted = 0
    AND email != ''
