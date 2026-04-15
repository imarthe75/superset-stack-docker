# ADR-002 — Migración a ClickHouse como motor OLAP (MDS v7.5 → v8.0)
# Fecha: 2026-04-14
# Estado: ACEPTADO
# Autor: Equipo Aura / Agente Residente v8.0

## Contexto

El stack v6.x ejecutaba todas las consultas analíticas directamente sobre PostgreSQL OLTP,
generando contención de I/O y tiempos de respuesta de 3-30 segundos en dashboards.

## Decisión

Implementar la arquitectura **Medallón MDS**:
```
PostgreSQL (OLTP) → PeerDB (CDC) → ClickHouse (OLAP) → dbt (Transform) → Cube (Semántica)
```

## Alternativas Evaluadas

| Opción              | Ventajas                  | Desventajas                        | Decisión   |
|---------------------|---------------------------|------------------------------------|------------|
| PostgreSQL read-replica | Simple, sin nueva tech | Sigue siendo row-store, lento en OLAP | ❌ Rechazado |
| DuckDB              | Ligero, sin servidor     | Sin CDC nativo, no escala a >100GB | ❌ Rechazado |
| BigQuery/Snowflake  | Managed, potente         | Costo, requiere internet, vendor lock | ❌ Rechazado |
| **ClickHouse**      | **Columnar, CDC nativo, OSS** | **Necesita más RAM**           | **✅ ELEGIDO** |

## Justificación de ClickHouse

1. **Motor `ReplacingMergeTree`**: Maneja upserts del CDC sin duplicados. Consultas con `FINAL`.
2. **Compresión LZ4**: 5-10x reducción en espacio de disco vs PostgreSQL.
3. **Velocidad OLAP**: 100-1000x más rápido en aggregaciones sobre millones de filas.
4. **PeerDB native support**: PeerDB (elegido para CDC) tiene soporte oficial para ClickHouse.

## Justificación de PeerDB para CDC

- Alternativas evaluadas: Debezium (requiere Kafka), Airbyte (pesado, UI-driven).
- PeerDB replica WAL de PostgreSQL → ClickHouse con latencia < 5 segundos.
- Configuración mínima: 1 contenedor, sin Kafka.

## Configuración Crítica del Agente

```yaml
# ClickHouse tablas Bronze (aura_raw):
ENGINE = ReplacingMergeTree(updated_at)
# SIEMPRE consultar con:
SELECT * FROM aura_raw.orders FINAL

# dbt perfil:
type: clickhouse
driver: http   # NO tcp, más estable con dbt
port: 8123

# Cube.js:
CUBEJS_DB_TYPE=clickhouse
CUBEJS_DB_HOST=clickhouse-server
CUBEJS_DB_PORT=8123
CUBEJS_DB_NAME=aura_gold   # SIEMPRE apuntar a capa Gold, no raw
```

## Consecuencias

- Superset requiere `clickhouse-connect >= 0.8.0` en Dockerfile.
- Vanna AI y Flowise deben consultar **Cube SQL API** (`,15432`), no ClickHouse directamente.
- dbt-runner necesita imagen Python con `dbt-clickhouse >= 1.8.0`.
- El stack analítico solo levanta con `--profile analytics`.

## Deuda Técnica Generada

- TD-3: TLS en comunicación ClickHouse ↔ PeerDB (pendiente).
- TD-4: ClickHouse Keeper cluster para HA (actualmente modo standalone).
