# AGENT.md — Fuente de Verdad del Agente de Desarrollo
# Proyecto: Aura Intelligence Suite v7.5 (MDS)
# Última actualización: 2026-04-14

> **INSTRUCCIÓN PARA EL AGENTE:** Lee este archivo COMPLETO al inicio de cada sesión antes de generar código.
> Nunca asumas un valor de variable de entorno; siempre refiérete a `.env.example` o HashiCorp Vault.

---

## 1. ESTÁNDARES DE CODIFICACIÓN

### 1.1 General
- **Lenguaje primario de configuración:** YAML (Docker Compose, dbt), SQL (ClickHouse, Postgres), Python (Prefect, Superset config).
- **Indentación:** 2 espacios para YAML, 4 espacios para Python.
- **Encoding:** UTF-8 en todos los archivos.
- **Fin de línea:** LF (Unix). Jamás CRLF.
- **Comentarios:** Todo bloque de configuración no obvio debe tener un comentario de una línea explicando su propósito.

### 1.2 Convenciones de Nombres

| Contexto             | Convención          | Ejemplo                          |
|----------------------|---------------------|----------------------------------|
| ClickHouse tablas    | `snake_case`        | `orders_raw`, `sales_daily_agg`  |
| ClickHouse columnas  | `snake_case`        | `order_date`, `total_amount`     |
| dbt modelos          | `snake_case` + prefijo de capa | `stg_orders`, `fct_sales`, `dim_products` |
| Docker services      | `kebab-case`        | `clickhouse-server`, `peerdb`    |
| Docker volumes       | `snake_case`        | `clickhouse_data`, `peerdb_data` |
| Variables de entorno | `UPPER_SNAKE_CASE`  | `CLICKHOUSE_PASSWORD`, `PEERDB_API_KEY` |
| Vault secret paths   | `snake_case` por segmento | `secret/aura/clickhouse`, `secret/aura/postgres` |
| Cube.js cubes        | `PascalCase`        | `OrdersFact`, `ProductsDim`      |

### 1.3 Capas dbt (Medallón)
```
Bronze  → stg_*   (datos crudos replicados por PeerDB, mínima transformación)
Silver  → int_*   (joins, limpieza, tipos correctos)
Gold    → fct_*, dim_*, mrt_*  (tablas analíticas para Superset/Cube)
```

---

## 2. MANEJO DE ERRORES EN DOCKER

### 2.1 Reglas de Healthcheck
- **Todos** los servicios con API HTTP deben tener healthcheck con `curl -f`.
- **Bases de datos** usan CLI nativo: `pg_isready`, `clickhouse-client --query "SELECT 1"`, `valkey-cli ping`.
- Parámetros estándar: `interval: 15s`, `timeout: 10s`, `retries: 5`, `start_period: 30s`.

### 2.2 Jerarquía de Dependencias (`depends_on`)
```
postgres (healthy) → peerdb
postgres (healthy) → superset, celery-worker, celery-beat, vanna-ai
clickhouse (healthy) → peerdb, cube, dbt-runner
valkey (healthy) → superset, celery-worker, celery-beat, cube
superset (healthy) → celery-worker, celery-beat, superset-mcp
prefect (started) → dbt-runner
```

### 2.3 Política de Reinicio
- Servicios de UI/API críticos: `restart: unless-stopped`
- Workers (Celery, dbt-runner): `restart: on-failure`
- Init containers (one-shot): `restart: no`

### 2.4 Límites de Recursos (baseline para 16GB RAM)
| Servicio          | CPU limit | RAM limit | RAM reserva |
|-------------------|-----------|-----------|-------------|
| clickhouse-server | 4         | 6G        | 2G          |
| postgres          | 2         | 2G        | 512M        |
| superset          | 2         | 2G        | 512M        |
| celery-worker     | 2         | 2G        | 512M        |
| cube              | 1         | 2G        | 512M        |
| peerdb            | 1         | 1G        | 256M        |
| prefect           | 1         | 1G        | 256M        |
| dbt-runner        | 1         | 512M      | 128M        |
| valkey            | 0.5       | 512M      | 128M        |
| keycloak          | 1         | 1G        | 256M        |
| grafana           | 0.5       | 512M      | 128M        |
| prometheus        | 0.5       | 512M      | 128M        |
| nginx             | 0.5       | 128M      | 64M         |
| **TOTAL EST.**    | **~18**   | **~19G**  | **~5.2G**   |

> **NOTA:** En host con 16GB RAM y sin swap, activar solo los servicios necesarios. Usar perfil `--profile analytics` para ClickHouse+PeerDB+dbt.

---

## 3. PROTOCOLOS DE SEGURIDAD — HASHICORP VAULT

### 3.1 Paths de Secrets en Vault
```
secret/aura/postgres          → POSTGRES_USER, POSTGRES_PASSWORD
secret/aura/clickhouse        → CLICKHOUSE_USER, CLICKHOUSE_PASSWORD
secret/aura/peerdb            → PEERDB_PASSWORD (pg replication slot)
secret/aura/superset          → SECRET_KEY, SUPERSET_ADMIN_PASSWORD
secret/aura/cube              → CUBEJS_API_SECRET
secret/aura/keycloak          → KEYCLOAK_ADMIN_PASSWORD, OIDC_CLIENT_SECRET
secret/aura/openai            → OPENAI_API_KEY
secret/aura/smtp              → SMTP_USER, SMTP_PASSWORD
secret/aura/grafana           → GF_SECURITY_ADMIN_PASSWORD
```

### 3.2 Integración con Docker (Vault Agent Injector)
- Los contenedores leen secrets via `VAULT_ADDR` + `VAULT_TOKEN` en tiempo de arranque.
- **JAMÁS** escribir credenciales reales en `docker-compose.yml`. Usar `${VAR}` que proviene de `.env` o Vault Agent.
- El archivo `.env` en producción debe ser un symlink al output del Vault Agent template.

### 3.3 Rotación de Credenciales
1. Actualizar secret en Vault.
2. Ejecutar `docker compose restart <service>` — el agente re-inyecta el secret.
3. Verificar healthcheck antes de continuar.

### 3.4 Red Docker — Principio de Mínimo Privilegio
- **Red interna** (`aura_internal`): todos los servicios backend.
- **Red pública** (`aura_public`): solo `nginx`.
- `nginx` es el ÚNICO servicio que pertenece a ambas redes.
- Ports en `docker-compose.yml` solo para desarrollo local. En producción, eliminar todos los `ports:` excepto `nginx:80/443`.

---

## 4. VARIABLES DE ENTORNO — REFERENCIA RÁPIDA

Siempre consultar `.env.example` para la lista completa.  
Nunca hardcodear IPs; usar nombres de servicio Docker (`postgres`, `clickhouse`, `valkey`).

---

## 5. COMANDOS DE REFERENCIA RÁPIDA

```bash
# Levantar stack completo
docker compose up -d

# Levantar solo stack analítico (MDS)
docker compose --profile analytics up -d

# Ver logs de un servicio
docker compose logs -f <service>

# Ejecutar dbt manualmente
docker compose run --rm dbt-runner dbt run --project-dir /dbt_aura --profiles-dir /dbt_aura

# Forzar re-replicación PeerDB
docker compose exec peerdb peerdb mirror status

# Verificar replicación Postgres WAL
docker compose exec postgres psql -U superset -c "SELECT * FROM pg_replication_slots;"

# Ver tablas en ClickHouse
docker compose exec clickhouse-server clickhouse-client --query "SHOW TABLES FROM aura_raw"
```
