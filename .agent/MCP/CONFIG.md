# 🤖 MCP (Model Context Protocol) — Configuración para Agente Residente Aura

## Objetivo

Permitir que el agente residente Aura ejecute comandos de orchestración (docker-compose, validación de conectividad) de forma segura y rastreada.

## Arquitectura

```
Agente Residente (Copilot)
        ↓
   MCP Client
        ↓
Superset MCP Server (puerto 8010)
        ↓
   Tools disponibles:
   - docker_compose_up
   - docker_compose_down
   - docker_compose_restart
   - validate_clickhouse_health
   - validate_peerdb_sync
   - validate_cube_cache
   - query_prometheus_metrics
        ↓
Docker daemon (socket: /var/run/docker.sock)
```

## Herramientas Disponibles

### 1. `docker_compose_up`
**Descripción:** Levantar servicios específicos del stack Aura.

**Parámetros:**
- `services`: Lista de servicios (comma-separated)
  - Válidos: `postgres`, `clickhouse-server`, `peerdb`, `dbt-runner`, `valkey`, `cube`, `superset`, `prefect`, `keycloak`, `nginx`, `all`
- `detach`: Boolean (default: true)
- `wait_healthy`: Boolean (default: true) — esperar healthchecks

**Ejemplo:**
```json
{
  "tool": "docker_compose_up",
  "parameters": {
    "services": "clickhouse-server,peerdb",
    "detach": true,
    "wait_healthy": true
  }
}
```

**Resultado:**
```json
{
  "status": "success",
  "services_started": ["clickhouse-server", "peerdb"],
  "exit_code": 0,
  "duration_seconds": 45,
  "log_tail": "peerdb | Starting service...\nclickhouse | Ready to accept connections"
}
```

### 2. `docker_compose_down`
**Descripción:** Detener servicios (sin remover volúmenes).

**Parámetros:**
- `services`: Lista de servicios o `all`
- `remove_volumes`: Boolean (default: false)
- `timeout`: Segundos (default: 30)

### 3. `docker_compose_restart`
**Descripción:** Reiniciar servicios (útil para debugging).

**Parámetros:**
- `services`: Lista de servicios
- `timeout`: Segundos (default: 30)

### 4. `validate_clickhouse_health`
**Descripción:** Verificar salud de ClickHouse (query SELECT 1).

**Parámetros:** ninguno

**Resultado:**
```json
{
  "status": "healthy",
  "latency_ms": 12,
  "version": "25.4.1.1",
  "uptime_seconds": 3600,
  "tables_in_aura_bronze": 5,
  "storage_gb": 2.4
}
```

### 5. `validate_peerdb_sync`
**Descripción:** Verificar lag de replicación CDC.

**Parámetros**: ninguno

**Resultado:**
```json
{
  "status": "synced",
  "replication_lag_seconds": 2,
  "tables_replicated": 4,
  "last_sync": "2026-04-15T10:30:05Z",
  "alert_threshold_exceeded": false
}
```

### 6. `validate_cube_cache`
**Descripción:** Verificar tasa de hit del cache Cube (Valkey).

**Parámetros**: ninguno

**Resultado:**
```json
{
  "status": "healthy",
  "cache_hit_rate": 0.97,
  "memory_used_mb": 256,
  "memory_max_mb": 400,
  "pre_aggregations_cached": 12
}
```

### 7. `query_prometheus_metrics`
**Descripción:** Ejecutar PromQL para obtener métricas.

**Parámetros:**
- `query`: String PromQL (ejemplo: `rate(clickhouse_query_duration_ms[5m])`)
- `time_range`: "5m", "1h", "24h" (default: "5m")

**Resultado:**
```json
{
  "query": "rate(clickhouse_query_duration_ms[5m])",
  "results": [
    {
      "metric": {"instance": "clickhouse:8123"},
      "value": 0.042
    }
  ],
  "timestamp": "2026-04-15T10:30:00Z"
}
```

## Seguridad

### Restricciones (TODO v8.0)
1. **RBAC:** Solo usuarios con rol `data-engineer` pueden ejecutar MCP tools
2. **Audit logging:** Todas las acciones vía MCP registradas en `audit_log` table
3. **Rate limiting:** Max 10 docker-compose ops por minuto (prevent DoS)
4. **Sandboxing:** MCP server corre en contenedor separado sin acceso a filesystem host (solo docker socket)

### Ejemplo de audit log
```sql
-- tabla: aura_silver.audit_log
INSERT INTO aura_silver.audit_log VALUES (
  'mcp_docker_compose_up',
  'data-engineer@example.com',
  ['clickhouse-server', 'peerdb'],
  'success',
  'Started replication testing',
  NOW()
);
```

## Integración con Agente

### Invocación desde chat del agente

**Usuario:** "¿El ClickHouse está saludable?"

**Agente:**
```
Voy a validar el estado de ClickHouse usando MCP.
[Ejecutando: validate_clickhouse_health]
→ ClickHouse está saludable (latencia: 12ms, v25.4.1)
→ Tablas en aura_bronze: 5
→ Storage usado: 2.4GB
```

### Invocación automática desde workflows

El agente puede invocar MCP en workflows para auto-remediate:

```python
# .agent/workflows/healthcheck.py
import mcp_client

def healthcheck_and_repair():
    """Ejecutar healthchecks y auto-repararr si es necesario"""
    
    # Check ClickHouse
    ch_status = mcp_client.validate_clickhouse_health()
    if ch_status['status'] != 'healthy':
        # Auto-remediate: restart
        mcp_client.docker_compose_restart(services='clickhouse-server')
        logger.warning("ClickHouse restarted via MCP")
    
    # Check PeerDB replication lag
    peerdb_status = mcp_client.validate_peerdb_sync()
    if peerdb_status['replication_lag_seconds'] > 30:  # SLA breached
        # Trigger manual sync
        # ... alert to Slack
        pass
    
    return {
        'clickhouse': ch_status,
        'peerdb': peerdb_status
    }

if __name__ == '__main__':
    healthcheck_and_repair()
```

## Instalación

1. Activar MCP en Superset (ya configurado en docker-compose.yml):
   ```bash
   docker-compose up -d superset-mcp
   ```

2. Verificar MCP server está activo:
   ```bash
   curl http://localhost:8010/health
   # {"status": "ok", "version": "1.0"}
   ```

3. Hacer available a Copilot (via VS Code settings):
   ```json
   {
     "@copilot/mcp": {
       "transports": [
         {
           "type": "sse",
           "url": "http://localhost:8010"
         }
       ]
     }
   }
   ```

## Próximos Pasos (v8.0)

- [ ] Implementar RBAC + audit logging en superset-mcp
- [ ] Crear webhooks para alertas (Slack, PagerDuty)
- [ ] Auto-remediate workflows (healthcheck + restart)
- [ ] Dashboard Grafana para audit trail MCP
- [ ] Rate limiting + circuit breaker patterns

---

**Versión:** 1.0 (2026-04-15)  
**Mantenedor:** Data Engineering Team
