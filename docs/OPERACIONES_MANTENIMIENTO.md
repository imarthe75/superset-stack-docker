# Manual de Operaciones y Mantenimiento (MDS)
# Rol: Administrador de Sistemas / SRE
# Versión: Aura v8.3

Este documento contiene los procedimientos operativos estándar para mantener la salud del stack Aura.

---

## 1. Gestión de Servicios (Docker Compose)

### Orden de Arranque Crítico
Si el sistema se apaga por completo, el orden de arranque debe ser:
1. `postgres`, `valkey`, `clickhouse-server` (Bases de datos)
2. `peerdb`, `temporal` (Capa de Ingesta)
3. `keycloak`, `nginx` (Seguridad y Gateway)
4. `superset`, `cube`, `prefect` (Capa de Aplicación)

### Comandos Útiles
```bash
# Reiniciar el stack respetando dependencias
docker compose up -d

# Ver logs en tiempo real de un servicio específico
docker compose logs -f [servicio]

# Revisar consumo de recursos
docker stats
```

---

## 2. Mantenimiento de Bases de Datos

### ClickHouse: Limpieza de Espacio
ClickHouse gestiona particiones automáticamente. Si necesitas borrar datos antiguos de la capa `aura_raw`:
```sql
ALTER TABLE aura_raw.tu_tabla DROP PARTITION '202301';
```

### Postgres: Bloqueos de Replicación
Si el `replication_slot` de PeerDB crece demasiado, puede llenar el disco de Postgres.
1. Verifica el tamaño: `SELECT slot_name, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) FROM pg_replication_slots;`
2. Si está estancado, reinicia el contenedor de `peerdb`.

---

## 3. Gestión de Caché (Valkey)

Aura usa Valkey para acelerar Superset y Cube.js.
- **DB0:** Celery (No borrar)
- **DB1:** Cube.js (Se puede borrar si hay datos inconsistentes en los tableros)

**Para limpiar la caché de Cube.js:**
```bash
docker exec -it superset-valkey-1 valkey-cli -n 1 flushdb
```

---

## 4. Troubleshooting Rápido

| Síntoma | Posible Causa | Solución |
|---------|---------------|----------|
| Superset da "502 Bad Gateway" | Nginx no llega al contenedor | `docker compose restart superset` |
| Datos desactualizados en tableros | Lag en PeerDB o Caché de Cube | Limpiar DB1 en Valkey / Check PeerDB logs |
| Error de Login (OIDC) | Keycloak está caído o mal configurado | Check http://<ip>/auth/ |
| ClickHouse lento | Falta de RAM o consultas pesadas | Revisar `docker stats` y límites en compose |
