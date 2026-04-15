-- =============================================================================
-- Aura Intelligence Suite v7.5 — Script de Inicialización MDS
-- Archivo: scripts/init_mds.sql
-- Ejecutado automáticamente por postgres al inicializar el contenedor.
-- NOTA: Este script corre dentro del contenedor postgres como usuario superset.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SECCIÓN 1: POSTGRES — Configuración para Replicación Lógica (WAL/CDC)
-- Habilita PeerDB para capturar cambios en tiempo real.
-- -----------------------------------------------------------------------------

-- Crear base de datos de catálogo para PeerDB
CREATE DATABASE peerdb_catalog;

-- Crear usuario dedicado para replicación (mínimo privilegio)
-- En producción, la contraseña vendrá de Vault: secret/aura/peerdb
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'peerdb_user') THEN
        CREATE ROLE peerdb_user WITH LOGIN PASSWORD 'peerdb_replication_pass' REPLICATION;
    END IF;
END
$$;

-- Otorgar permisos al usuario de replicación en sales_data
\c sales_data
GRANT CONNECT ON DATABASE sales_data TO peerdb_user;
GRANT USAGE ON SCHEMA public TO peerdb_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO peerdb_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO peerdb_user;

-- Crear slot de replicación lógica para PeerDB
-- El slot persiste el WAL hasta que PeerDB confirme que procesó los cambios.
SELECT pg_create_logical_replication_slot('peerdb_slot', 'pgoutput')
WHERE NOT EXISTS (
    SELECT 1 FROM pg_replication_slots WHERE slot_name = 'peerdb_slot'
);

-- Crear publicación que incluye todas las tablas de sales_data para replicación
CREATE PUBLICATION peerdb_publication
    FOR TABLE users, orders, products, support_tickets, ml_prediccion_ventas
    WITH (publish = 'insert, update, delete');

-- Verificar configuración de replicación
SELECT
    slot_name,
    plugin,
    slot_type,
    active,
    restart_lsn,
    confirmed_flush_lsn
FROM pg_replication_slots
WHERE slot_name = 'peerdb_slot';

-- Verificar publicación
SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete
FROM pg_publication
WHERE pubname = 'peerdb_publication';

-- Volver a la base de datos principal
\c superset

-- =============================================================================
-- FIN POSTGRES — Las secciones siguientes se ejecutan contra ClickHouse
-- Usar: docker compose exec clickhouse-server clickhouse-client -u aura --password <pass>
-- O ejecutar el script: ./scripts/init_clickhouse.sh
-- =============================================================================
