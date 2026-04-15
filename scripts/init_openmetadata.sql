-- =============================================================================
-- Scripts de Inicialización para OpenMetadata en Postgres
-- =============================================================================

-- Crear la base de datos si no existe
SELECT 'CREATE DATABASE openmetadata_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openmetadata_db')\gexec

-- Crear usuario específico (opcional, aquí usamos superset por simplicidad según docker-compose)
-- GRANT ALL PRIVILEGES ON DATABASE openmetadata_db TO superset;
