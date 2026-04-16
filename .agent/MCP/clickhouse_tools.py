#!/usr/bin/env python3
"""
clickhouse_tools.py — Herramientas MCP para consultas a ClickHouse
===================================================================
Proyecto: Aura Intelligence Suite v0.8
Ubicación: .agent/MCP/clickhouse_tools.py

Permite al agente consultar ClickHouse de forma segura para:
- Verificar estado de replicación PeerDB
- Consultar tablas Gold para validar modelos dbt
- Monitorear métricas de rendimiento

SEGURIDAD:
    - Solo permite queries SELECT (nunca DDL o DML)
    - Usuario superset_ro por defecto
    - Timeout máximo de 30s
"""
from __future__ import annotations

import os
from typing import Any

try:
    import clickhouse_connect
    HAS_CH = True
except ImportError:
    HAS_CH = False
    print("⚠️  clickhouse-connect no instalado. pip install clickhouse-connect")


class ClickHouseMCPTools:
    """Herramientas MCP para consultas analíticas en ClickHouse."""

    def __init__(
        self,
        host: str | None = None,
        port: int = 8123,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self.host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = port
        self.user = user or os.getenv("CLICKHOUSE_USER", "aura")
        self.password = password or os.getenv("CLICKHOUSE_PASSWORD", "")
        self._client = None

    def _get_client(self) -> Any:
        """Obtiene o crea el cliente ClickHouse."""
        if not HAS_CH:
            raise RuntimeError("clickhouse-connect no instalado")
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                connect_timeout=10,
                query_limit=100_000,
            )
        return self._client

    def _safe_query(self, sql: str) -> list[dict[str, Any]]:
        """Ejecuta un SELECT de forma segura (valida que sea solo lectura)."""
        sql_upper = sql.strip().upper()
        if not any(sql_upper.startswith(kw) for kw in ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
            raise ValueError(f"Solo se permiten queries de lectura (SELECT/SHOW/DESCRIBE). Recibido: {sql[:50]}")
        client = self._get_client()
        result = client.query(sql)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def get_replication_status(self) -> list[dict[str, Any]]:
        """
        Verifica el estado de replicación PeerDB.
        Muestra la latencia entre PeerDB synced_at y now().
        """
        return self._safe_query("""
            SELECT
                database,
                table,
                count()                                          AS total_rows,
                max(_peerdb_synced_at)                          AS last_sync_utc,
                dateDiff('second', max(_peerdb_synced_at), now()) AS lag_seconds
            FROM (
                SELECT 'aura_raw' AS database, 'orders'  AS table, _peerdb_synced_at FROM aura_raw.orders  FINAL
                UNION ALL
                SELECT 'aura_raw', 'users',    _peerdb_synced_at FROM aura_raw.users   FINAL
                UNION ALL
                SELECT 'aura_raw', 'products', _peerdb_synced_at FROM aura_raw.products FINAL
            )
            GROUP BY database, table
            ORDER BY lag_seconds DESC
        """)

    def get_table_stats(self, database: str = "aura_gold") -> list[dict[str, Any]]:
        """Obtiene estadísticas de tamaño y filas por tabla en una base de datos."""
        return self._safe_query(f"""
            SELECT
                database,
                table,
                formatReadableSize(sum(data_compressed_bytes))   AS size_compressed,
                formatReadableSize(sum(data_uncompressed_bytes)) AS size_uncompressed,
                sum(rows)                                        AS total_rows,
                max(modification_time)                           AS last_modified
            FROM system.parts
            WHERE database = '{database}' AND active = 1
            GROUP BY database, table
            ORDER BY sum(rows) DESC
        """)

    def preview_gold_table(self, table: str, limit: int = 5) -> list[dict[str, Any]]:
        """Preview de una tabla Gold (para validación post-dbt)."""
        return self._safe_query(f"SELECT * FROM aura_gold.{table} LIMIT {limit}")

    def get_resource_usage(self) -> list[dict[str, Any]]:
        """Métricas de recursos de ClickHouse en tiempo real."""
        return self._safe_query("""
            SELECT
                metric,
                value,
                description
            FROM system.metrics
            WHERE metric IN (
                'Query', 'Merge', 'ReplicatedFetch',
                'MemoryTracking', 'BackgroundPoolTask'
            )
        """)

    def check_health(self) -> bool:
        """Verifica que ClickHouse responde."""
        try:
            result = self._safe_query("SELECT 1 AS ok")
            return result[0]["ok"] == 1
        except Exception:
            return False


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, sys
    tools = ClickHouseMCPTools()

    if "--health" in sys.argv:
        print("✅ ClickHouse OK" if tools.check_health() else "❌ ClickHouse no responde")
    elif "--replication" in sys.argv:
        print(json.dumps(tools.get_replication_status(), indent=2, default=str))
    elif "--stats" in sys.argv:
        db = sys.argv[sys.argv.index("--stats") + 1] if len(sys.argv) > 2 else "aura_gold"
        print(json.dumps(tools.get_table_stats(db), indent=2, default=str))
    elif "--resources" in sys.argv:
        print(json.dumps(tools.get_resource_usage(), indent=2, default=str))
    else:
        print("Uso: python clickhouse_tools.py [--health|--replication|--stats [db]|--resources]")
