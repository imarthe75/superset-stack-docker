<p align="center">
  <img src="assets/logo.png" width="250" alt="Aura Intelligence Logo">
</p>

# 🌌 Aura Intelligence Suite (v7.5) — Modern Data Stack

**Aura Intelligence Suite** es una plataforma de datos e inteligencia unificada, construida sobre Docker Compose, que combina un pipeline OLTP→CDC→OLAP→Semántico→BI con capacidades de IA generativa y observabilidad completa.

> [!TIP]
> **Requisito mínimo:** 16 GB RAM. Ver §1.2 para especificaciones detalladas.

---

## PARTE 1: Arquitectura del Stack

### 1.1 Resumen por Capas

El stack se estructura en **11 capas** que aíslan responsabilidades y maximizan el rendimiento:

| Capa | Componente | Versión | Propósito |
| :---: | :--- | :---: | :--- |
| **0** | PostgreSQL | 18.3 | Base OLTP transaccional + metadatos de Superset. WAL lógico habilitado para CDC. |
| **1** | ClickHouse | 25.4 | Motor OLAP columnar (Bronze → Silver → Gold layers). Destino principal de análisis. |
| **2** | PeerDB | stable | Change Data Capture (CDC): replica datos de Postgres → ClickHouse en tiempo real. |
| **3** | dbt (runner) | — | Transformación: ejecuta modelos SQL sobre ClickHouse (on-demand vía Prefect). |
| **4** | Valkey | 9.0.3 | Caché y broker de Celery (reemplazo drop-in de Redis). |
| **5** | Cube.js | 1.6.19 | Capa semántica: métricas unificadas, pre-agregaciones y SQL API (psql wire protocol). |
| **6** | Apache Superset | 7.5 | BI y visualización. Consulta Cube.js y ClickHouse directamente. |
| **7** | Flowise AI | latest | Orquestador visual de agentes RAG y flujos conversacionales. |
| **7** | Vanna AI | — | Asistente NL→SQL especializado (consulta Cube SQL API). |
| **7** | Superset-MCP | — | Model Context Protocol: controla Superset desde Claude Desktop / agentes externos. |
| **8** | Prefect | v3.x | Orquestación de pipelines ETL/ELT y ejecución de flujos dbt. |
| **9** | Keycloak | 26.5.5 | Identity Provider OIDC: SSO para Superset y demás frontends. |
| **10** | Prometheus + Grafana + cAdvisor + StatsD + postgres-exporter | v3/v12/v0.56/v0.29/— | Observabilidad completa: métricas, dashboards y alertas. |
| **11** | Nginx | 1.28.2 | Único gateway público (Puerto 80). Reverse proxy para todos los frontends. |

### 1.2 Requerimientos del Sistema

#### Mínimos (Desarrollo / Pruebas)
- **CPU**: 4 vCPUs
- **RAM**: 16 GB (requerido por ClickHouse)
- **Almacenamiento**: 60 GB SSD

#### Recomendados (Producción)
- **CPU**: 8 vCPUs
- **RAM**: 32 GB
- **Almacenamiento**: 200 GB NVMe
- **Red**: 1 Gbps

### 1.3 Diagrama de Arquitectura

```mermaid
graph TD
    User((Usuario)) --> Nginx["Nginx :80\n(Gateway Público)"]

    subgraph "Capa 11 — Gateway"
        Nginx
    end

    subgraph "Capa 6-7 — BI & IA"
        Nginx --> Superset["Apache Superset :8088"]
        Nginx --> Flowise["Flowise AI :3001"]
        Nginx --> Keycloak["Keycloak :8001"]
        Nginx --> Grafana["Grafana :3000"]
        Nginx --> Prefect["Prefect UI :4200"]
        Nginx --> Cube["Cube.js :4000"]

        Flowise --> VannaAI["Vanna AI :8011"]
        MCP["Superset-MCP :8010"] --> Superset
    end

    subgraph "Capa 5 — Semántica"
        Superset --> Cube
        VannaAI --> Cube
        Cube --> ClickHouse
        Cube --> Postgres
        Cube --> Valkey["Valkey :6379"]
        Superset --> Valkey
    end

    subgraph "Capa 0-3 — Data Pipeline"
        Postgres[(PostgreSQL\nOLTP)] -->|CDC / WAL| PeerDB["PeerDB"]
        PeerDB -->|Replicación real-time| ClickHouse[("ClickHouse\nOLAP")]
        Prefect -->|Orquesta| dbt["dbt runner"]
        dbt -->|Bronze → Silver → Gold| ClickHouse
    end

    subgraph "Capa 10 — Observabilidad"
        Prometheus --> cAdvisor
        Prometheus --> PostgresExp["postgres-exporter"]
        Prometheus --> StatsD["statsd-exporter"]
        Grafana --> Prometheus
    end
```

### 1.4 Flujo de Datos (Data Pipeline)

```
PostgreSQL (OLTP)
      │
      ▼ CDC vía PeerDB (Change Data Capture, WAL lógico)
ClickHouse — Bronze Layer  (replica 1:1 desde Postgres)
      │
      ▼ dbt transformaciones (orquestadas por Prefect)
ClickHouse — Silver Layer  (datos limpios y normalizados)
      │
      ▼ dbt modelos agregados
ClickHouse — Gold Layer    (métricas listas para consumo)
      │
      ▼ Cube.js (capa semántica + caché en Valkey)
Apache Superset / Flowise / Vanna AI  (dashboards, agentes, NL→SQL)
```

---

## PARTE 2: Instalación y Despliegue

### 2.1 Configuración Inicial

```bash
# 1. Clonar el repositorio
git clone <repo-url> && cd superset

# 2. Crear variables de entorno
cp .env.example .env

# 3. Editar .env — variables críticas:
#    SERVER_IP       → IP pública o 'localhost'
#    SECRET_KEY      → Clave aleatoria larga (openssl rand -base64 32)
#    POSTGRES_PASSWORD, CLICKHOUSE_PASSWORD, KEYCLOAK_ADMIN_PASSWORD
#    OPENAI_API_KEY  → (opcional) para Vanna AI
nano .env
```

### 2.2 Levantar el Stack

```bash
# Construir imágenes personalizadas (Superset + Prefect + Vanna AI)
docker compose build

# Levantar todo el stack en background
docker compose up -d

# Verificar estado de servicios
docker compose ps
```

> [!NOTE]
> El primer arranque puede tardar **5-10 minutos** mientras ClickHouse inicializa su almacenamiento y PeerDB configura los slots de replicación.

### 2.3 Inicialización de Superset (primera vez)

```bash
# Crear usuario administrador
docker compose exec superset superset fab create-admin \
  --username admin --password admin \
  --firstname Superset --lastname Admin \
  --email admin@example.com

# Migrar base de datos y permisos
docker compose exec superset superset db upgrade
docker compose exec superset superset init
```

### 2.4 URLs de Acceso

Todos los servicios son accesibles mediante Nginx en el puerto 80:

| Servicio | URL | Puerto directo (solo dev) |
| :--- | :--- | :--- |
| **Apache Superset** | `http://TU_IP/` | `:8088` |
| **Keycloak** | `http://TU_IP/auth/` | `:8001` |
| **Prefect UI** | `http://TU_IP/prefect/` | `:4200` |
| **Grafana** | `http://TU_IP/grafana/` | `:3000` |
| **Cube.js Playground** | `http://TU_IP/cubejs/` | `:4000` |
| **Prometheus** | `http://TU_IP/prometheus/` | `:9090` |
| **cAdvisor** | `http://TU_IP/cadvisor/` | `:8080` |
| **Flowise AI** | `http://TU_IP/flowise/` | `:3001` |
| **Vanna AI** | `http://TU_IP/vanna/` | `:8011` |
| **PeerDB UI** | — | `:8085` |
| **ClickHouse HTTP** | — | `:8123` (solo dev) |

> [!CAUTION]
> En producción, **comentar todos los `ports:`** en `docker-compose.yml` excepto los de Nginx (`:80`/`:443`). Los puertos directos son **solo para desarrollo**.

---

## PARTE 3: Componentes en Detalle

### 3.1 ClickHouse (Motor OLAP)

ClickHouse es el corazón analítico del stack. Almacena datos en tres capas:

- **Bronze** (`aura_bronze`): Réplica 1:1 de Postgres vía PeerDB.
- **Silver** (`aura_silver`): Datos transformados y normalizados por dbt.
- **Gold** (`aura_gold`): Métricas agregadas consumidas por Cube.js y Superset.

**Configuración personalizada:** `./docker/clickhouse/config.xml` y `./docker/clickhouse/users.xml`

```bash
# Conectar al cliente ClickHouse
docker compose exec clickhouse-server clickhouse-client \
  --user aura --password <CLICKHOUSE_PASSWORD>

# Ver bases de datos disponibles
SHOW DATABASES;
```

**Conexión desde Superset:**
1. Settings → Database Connections → + Database
2. Tipo: `ClickHouse Connect`
3. Host: `clickhouse-server`, Puerto: `8123`
4. Database: `aura_gold` (para dashboards finales)

### 3.2 PeerDB (Change Data Capture)

PeerDB replica cambios de PostgreSQL a ClickHouse en tiempo real usando el WAL lógico.

**Requisito:** PostgreSQL tiene habilitado `wal_level=logical` (ya configurado en `docker-compose.yml`).

```bash
# Verificar que PeerDB esté saludable
docker compose logs peerdb --tail=50

# Acceder a la UI de PeerDB (solo dev)
# http://localhost:8085
```

**Configurar un Mirror (replicación):**
1. Abrir PeerDB UI en `http://localhost:8085`
2. Crear un **Peer** de tipo PostgreSQL apuntando a `postgres:5432`
3. Crear un **Peer** de tipo ClickHouse apuntando a `clickhouse-server:9000`
4. Crear un **Mirror** CDC entre ambos peers

### 3.3 dbt (Transformaciones)

dbt ejecuta modelos SQL para transformar datos en ClickHouse (Bronze → Silver → Gold).

**Estructura:** `./dbt_aura/`

```bash
# Ejecutar modelos dbt manualmente
docker compose run --rm dbt-runner dbt run

# Ejecutar solo una capa específica
docker compose run --rm dbt-runner dbt run --select tag:silver

# Verificar tests de calidad de datos
docker compose run --rm dbt-runner dbt test
```

> En producción, los modelos dbt se ejecutan automáticamente vía **Prefect flows** en `./prefect_flows/`.

### 3.4 Cube.js (Capa Semántica)

Cube.js proporciona una capa semántica unificada sobre ClickHouse (Gold layer) y PostgreSQL legacy.

- **REST API**: `http://TU_IP/cubejs/` — Playground interactivo.
- **SQL API (PostgreSQL wire)**: `cube:15432` — Consultas SQL estándar.

**Conectar Superset a Cube SQL API:**
1. Settings → Database Connections → + Database
2. Tipo: `PostgreSQL`
3. SQLAlchemy URI: `postgresql://superset:superset@cube:15432/aura_gold`

**Esquemas de datos:** `./cube_schema/` — Define métricas, dimensiones y pre-agregaciones.

### 3.5 PrefECT (Orquestación de Pipelines)

Prefect v3 gestiona la ejecución de flows de datos, dbt y ML.

```bash
# Ver flows registrados
docker compose exec prefect prefect flow ls

# Ejecutar un flow manualmente
docker compose exec prefect python /opt/prefect/flows/<flow_name>.py
```

**Directorio de flows:** `./prefect_flows/`

### 3.6 Keycloak (Identity Provider)

Keycloak gestiona la autenticación SSO para todos los servicios del stack.

- **Admin Console**: `http://localhost:8001/auth/`
- **Credenciales default**: `admin` / `admin` (cambiar en `.env`)

**Activar autenticación OIDC en Superset:**
1. Crear un Realm y Cliente en Keycloak (Client ID: `superset`, Grant Type: `authorization_code`)
2. Configurar `Valid Redirect URIs`: `http://TU_IP/*`
3. Actualizar variables en `.env`:
   ```env
   OIDC_CLIENT_ID=superset
   OIDC_OPENID_REALM=<tu-realm>
   OIDC_ISSUER_URL=http://TU_IP/auth/realms/<tu-realm>
   ```
4. En `superset_config.py`: cambiar `AUTH_TYPE = AUTH_OID`
5. Reiniciar: `docker compose restart superset`

### 3.7 Capa de IA (Flowise + Vanna AI + Superset-MCP)

#### Flowise AI
Crea flujos de agentes RAG, chatbots y pipelines de IA de forma visual.
- **UI**: `http://TU_IP/flowise/`
- **Consulta datos vía**: Cube SQL API (`cube:15432`)

#### Vanna AI
Asistente especializado en generación de SQL desde lenguaje natural (NL→SQL).
- **Endpoint**: `:8011`
- **Fuente de datos**: Cube SQL API (métricas validadas) + PostgreSQL (fallback legacy)
- **Build personalizado**: `./vanna-ai/`

#### Superset-MCP (Model Context Protocol)
Permite a agentes externos (Claude Desktop, etc.) controlar Superset programáticamente.
- **Endpoint SSE**: `http://TU_IP:8010`
- **Capacidades**: Listar/crear dashboards y charts, ejecutar SQL Lab, gestionar datasets.
- **Build personalizado**: `./superset-mcp/`

**Configurar Claude Desktop:**
```json
{
  "mcpServers": {
    "superset": {
      "url": "http://TU_IP:8010/sse"
    }
  }
}
```

### 3.8 Observabilidad (Prometheus + Grafana)

El stack incluye monitoreo completo con métricas de todos los servicios.

**Exporters incluidos:**
- `cadvisor`: Métricas de contenedores Docker (CPU, RAM, red).
- `postgres-exporter`: Métricas de PostgreSQL (conexiones, transacciones, tamaño).
- `statsd-exporter`: Métricas internas de Superset y Cube.js.

**Dashboards pre-configurados** en `./docker/grafana/dashboards/`:
- Docker Container Monitoring
- PostgreSQL Overview
- Application Metrics (Superset + Cube.js)

**Alertas pre-configuradas:**
- Latencia P99 de PostgreSQL > 1000ms
- Tasa de aciertos de Cube.js < 80%
- Sin tareas exitosas en Prefect en las últimas 24h

---

## PARTE 4: Gestión y Mantenimiento

### 4.1 Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f [servicio]

# Reiniciar un servicio específico
docker compose restart [servicio]

# Bajar todo el stack (preserva volúmenes)
docker compose down

# Bajar y eliminar todos los datos (¡DESTRUCTIVO!)
docker compose down -v

# Ver uso de recursos
docker stats
```

### 4.2 Persistencia de Datos

| Dato | Ubicación |
| :--- | :--- |
| PostgreSQL | `./postgres_data/` |
| ClickHouse (datos) | Volumen Docker `aura_clickhouse_data` |
| ClickHouse (logs) | Volumen Docker `aura_clickhouse_logs` |
| Grafana | `./grafana_data/` |
| Prometheus | `./prometheus_data/` |
| Prefect | `./prefect_data/` |
| Valkey | `./valkey_data/` |
| Flowise | Volumen Docker `flowise_data` |
| Vanna AI | Volumen Docker `vanna_data` |
| Superset home | Volumen Docker `superset_home` |

### 4.3 Personalización de Marca

1. Coloca tu logo en `./superset_assets/logo.png`
2. Coloca tu favicon en `./superset_assets/favicon.png`
3. Reinicia Superset: `docker compose restart superset`

### 4.4 Solución de Problemas

**ClickHouse no inicia:**
```bash
docker compose logs clickhouse-server --tail=100
# Verificar permisos del volumen y espacio en disco
```

**PeerDB no replica:**
```bash
docker compose logs peerdb --tail=100
# Verificar que postgres tenga wal_level=logical:
docker compose exec postgres psql -U superset -c "SHOW wal_level;"
```

**Superset no conecta con Cube.js:**
```bash
# Verificar que Cube esté saludable
docker compose exec cube curl http://localhost:4000/cubejs-api/v1/meta
```

**Build falla por restricciones de red (PyPI):**
Ajustar el mirror en `.env`:
```env
PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 4.5 Integración Continua

`.github/workflows/ci.yml` valida automáticamente en cada Push/PR a `main`:
1. Sintaxis de `docker-compose.yml`
2. Build de imágenes personalizadas
3. Healthchecks de todos los servicios
4. Endpoints principales (Superset, ClickHouse, Cube.js)

---

## PARTE 5: Seguridad en Producción

> [!CAUTION]
> Las siguientes acciones son **obligatorias** antes de exponer el stack a internet.

1. **Cambiar todas las contraseñas default** en `.env` (PostgreSQL, ClickHouse, Keycloak, Grafana).
2. **Generar `SECRET_KEY` aleatoria**: `openssl rand -base64 32`
3. **Comentar todos los `ports:`** en `docker-compose.yml` excepto Nginx `:80`/`:443`.
4. **Activar HTTPS** en Nginx con certificado TLS (Let's Encrypt recomendado).
5. **Activar Keycloak OIDC** en Superset (ver §3.6).
6. **Revisar** `./docker/clickhouse/users.xml` para restringir permisos por usuario.

---

*Aura Intelligence Suite v7.5 — Stack basado en columnar OLAP + CDC + Semantic Layer + GenAI*
