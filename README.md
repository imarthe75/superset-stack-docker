<p align="center">
  <img src="assets/logo.png" width="250" alt="Aura Intelligence Logo">
</p>

# 🌌 Aura Intelligence Suite (v6.0.0) - AI & BI Unified Platform

Este documento es la guía definitiva para **Aura Intelligence Suite**, una plataforma unificada que combina lo mejor de Apache Superset (v6.0.0), modelado semántico con Cube.js, y una potente capa de Inteligencia Artificial Generativa.

## PARTE 1: Resumen Arquitectónico (Estructura de Producción)

La solución se estructura en capas para aislar responsabilidades y maximizar el rendimiento.

| Capa | Componente Clave | Propósito Principal |
| :--- | :--- | :--- |
| **Inteligencia Artificial** | Flowise AI / Vanna AI | Orquestador de agentes y asistente SQL para "Chat with Data". |
| **Orquestación** | Prefect v3.x | Gestión de Pipelines de datos (ETL/ELT) y ML Ops. |
| **Modelado Semántico** | Cube.js (v1.6.19) | Definición centralizada de métricas y caching de pre-agregados. |
| **Visualización / BI** | Apache Superset (v6.0.0) | Exploración de datos, Dashboards y reportes programados. |
| **Datos / Metadatos** | PostgreSQL (v18.3) | Almacenamiento de datos fuente, resultados de ML y metadatos. |
| **Caché / Broker** | Valkey (v9.0.3) | Reemplazo de Redis para caché y broker de Celery. |
| **Proxy / Acceso** | Nginx (v1.28.2) | Puerta de enlace unificada (Puerto 80) para todos los servicios. |
| **Identidad** | Keycloak (v26.5.5) | Gestión de identidad y acceso (OIDC) en Puerto 8001. |
| **Observabilidad** | Prometheus (v3.10.0) + Grafana (v12.4.0) | Monitoreo del estado de todos los servicios críticos. |

## PARTE 1.1: Requerimientos del Sistema

Para un funcionamiento óptimo de todos los servicios integrados, se recomiendan las siguientes especificaciones:

### Mínimos (Entornos de Desarrollo/Prueba)
- **CPU**: 2 vCPUs (Intel/AMD)
- **RAM**: 8 GB
- **Almacenamiento**: 40 GB SSD (Docker Images + Data)

### Recomendados (Producción Ligera)
- **CPU**: 4 vCPUs
- **RAM**: 16 GB
- **Almacenamiento**: 100 GB NVMe
- **Ancho de Banda**: 100 Mbps

---

### 1.1. Capa de Inteligencia y ML

El proyecto integra capacidades de IA generativa:
- **Flowise AI**: Permite crear flujos de agentes RAG y asistentes conversacionales visuales.
- **Vanna AI**: Agente especializado en generar queries SQL a partir de lenguaje natural (Natural Language to SQL).
- **Superset MCP**: Implementación del *Model Context Protocol* para controlar Superset desde agentes externos como Claude Desktop.

### 1.2. Diagrama de Arquitectura Moderna

```mermaid
graph TD
    User((Usuario)) --> Nginx[Nginx Proxy :80]
    
    subgraph "AI & Frontends"
        Nginx --> Superset[Apache Superset :8088]
        Nginx --> Flowise[Flowise AI :3001]
        Nginx --> Keycloak[Keycloak :8001]
        Nginx --> Grafana[Grafana :12.4]
    end

    subgraph "Intelligent Logic"
        Flowise --> Vanna[Vanna.ai :8011]
        Vanna --> Postgres[(PostgreSQL)]
        Superset-MCP[MCP Server :8010] --> Superset
        Prefect[Prefect Server] --> Cube[Cube.js]
    end

    subgraph "Data Backbone"
        Superset --> Postgres
        Superset --> Valkey[Valkey :9.0]
        Cube --> Postgres
        Prefect --> Postgres
    end

    subgraph "Observability"
        Prometheus[Prometheus :3.10] --> cAdvisor
        cAdvisor --> Containers
        Grafana --> Prometheus
    end
```

---

## PARTE 2: Guía de Instalación Avanzada (Docker)

### 2.1. Requisitos y Configuración

El proyecto usa Docker Compose. La configuración clave se maneja en `.env`.

**Clonar y configurar:**

```bash
# Copiar variables de ejemplo
cp .env.example .env

# Editar .env:
# - DOMAIN: Define tu IP pública (ej: 40.233.31.165) para Grafana/Nginx.
# - SECRETS & SMTP: Configura tus claves y correo.
# - SUPERSET CONFIG: ROW_LIMIT, PUERTOS, OIDC, REPORTING.
nano .env
```

### 2.2. Despliegue de Servicios

El stack incluye la construcción de imágenes personalizadas para Superset (drivers) y Prefect (ML libs).

```bash
# Construir imágenes personalizadas
docker compose build

# Levantar todo el stack
docker compose up -d
```

### 2.3. Acceso a Servicios (Vía Nginx / Puerto 80)

Gracias al Proxy Inverso, todos los servicios son accesibles por la IP definida en `.env`:

| Servicio | URL |
| :--- | :--- |
| **Superset** | `http://TU_IP/` |
| **Keycloak** | `http://TU_IP:8001/` |
| **Vault** | `http://TU_IP:8200/` |
| **Prefect UI** | `http://TU_IP/prefect/` |
| **Grafana** | `http://TU_IP/grafana/` |
| **Cube.js API** | `http://TU_IP/cubejs/` |
| **Prometheus** | `http://TU_IP/prometheus/` |
| **cAdvisor** | `http://TU_IP/cadvisor/` |

### 2.4. Inicialización de Superset (Post-Instalación)

Si es la primera vez que levantas el stack:

```bash
# 1. Crear usuario admin
docker compose exec superset superset fab create-admin --username admin --password admin --firstname Superset --lastname Admin --email admin@example.com

# 2. Migrar DB y Permisos
docker compose exec superset superset db upgrade
docker compose exec superset superset init
```

### 2.5. Ejecución del Pipeline ML (PoC)

Para probar la integración de Machine Learning:

```bash
# Ejecutar el flujo manualmente dentro del contenedor de Prefect
docker compose exec prefect python /opt/prefect/flows/ml_sales_pipeline.py
```

Esto generará datos en la tabla `ml_prediccion_ventas` y refrescará Cube.js.

### 2.6 Integración de Cube.js en Superset

Para visualizar los datos de Cube.js:

1. En Superset, ir a **Settings > Database Connections**.
2. Añadir nueva base de datos **PostgreSQL**.
3. **Display Name**: Cube.js (SQL API)
4. **SQLAlchemy URI**: `postgresql://superset:superset@cube:15432/sales_data`
   *(Nota: Usamos el protocolo PostgreSQL de Cube.js en el puerto 15432 para máxima compatibilidad).*

### 2.7. Integración con Keycloak (Identity Provider)

El stack incluye **Keycloak** en el puerto **8001**.

- **URL**: `http://localhost:8001`
- **Credenciales por defecto**: `admin` / `admin`

**Para activar autenticación vía Keycloak en Superset:**

1. Crear un Realm y Cliente en Keycloak (Cliente ID: `superset`, `Client Authentication`: On, `Valid Redirect URIs`: `http://localhost:8088/*`).
2. Editar `superset_config.py`:
   - Cambiar `AUTH_TYPE = AUTH_DB` a `AUTH_TYPE = AUTH_OID`.
   - Asegurarse de que las variables `OIDC_*` en `.env` coincidan con tu Keycloak.
3. Reiniciar Superset: `docker compose restart superset`.

### 2.8. Añadir Base de Datos Externa a Cube.js

Para conectar Cube.js a una base de datos externa (ej. Oracle, Snowflake, otro Postgres) en lugar de la base de datos local `sales_data`:

1. Abrir `docker-compose.yml` (servicio `cube`).

2. Modificar las variables de entorno para el origen `extra_postgres`:

   ```yaml
   environment:
     # ...
     - CUBEJS_DS_EXTRA_POSTGRES_DB_TYPE=postgres
     - CUBEJS_DS_EXTRA_POSTGRES_DB_HOST=tu-host-externo.com
     - CUBEJS_DS_EXTRA_POSTGRES_DB_NAME=nombre_db
     - CUBEJS_DS_EXTRA_POSTGRES_DB_USER=usuario
     - CUBEJS_DS_EXTRA_POSTGRES_DB_PASS=contraseña
   ```

   *Si tu base de datos no es Postgres, cambia el sufijo `_DB_TYPE` y ajusta según corresponda.*

3. Reiniciar Cube: `docker compose restart cube`.

*Nota: Asegúrate de que el contenedor de Cube tenga acceso a la red de tu BD externa.*

### 2.9. Gestión de Secretos (Vault)

El stack incluye **HashiCorp Vault** en modo desarrollo.

- **URL**: `http://localhost:8200`
- **Token**: `root`

**Ejemplo de uso (desde tu máquina):**

```bash
# Guardar un secreto
curl -H "X-Vault-Token: root" -X POST -d '{"data": {"password": "super-secret"}}' http://localhost:8200/v1/secret/data/db_pass

# Leer un secreto
curl -H "X-Vault-Token: root" http://localhost:8200/v1/secret/data/db_pass
```

### 2.10. Integración Continua (CI/CD)

Se ha configurado un flujo de trabajo en GitHub Actions (`.github/workflows/ci.yml`) que:

1. Valida la configuración de Docker Compose.
2. Construye las imágenes del stack.
3. Levanta el entorno y valida los healthchecks.
4. Verifica los endpoints principales (Superset, Keycloak, Vault).

Este flujo se ejecuta automáticamente en cada **Push** o **Pull Request** a la rama `main`.

### 2.11. Persistencia de Datos

Todos los servicios críticos persisten su estado en carpetas locales (`./*_data`) para facilitar backups y acceso directo:

- **PostgreSQL**: `./postgres_data`
- **Grafana**: `./grafana_data`
- **Prometheus**: `./prometheus_data`
- **Prefect**: `./prefect_data` (Base de datos SQLite local)
- **Valkey**: `./valkey_data` (Caché persistente y mensajes)

### 2.12. Observabilidad y Monitoreo (Grafana)

El sistema incluye una pila completa de monitoreo con **Prometheus**, **Grafana**, **cAdvisor**, **Exporter de Postgres** y **StatsD Exporter** para Superset.

**Tableros Pre-configurados:**

- **Docker Monitoring**: Uso de CPU, RAM y Red de todos los contenedores.
- **PostgreSQL Monitoring**: Conexiones activas, tamaño de DB y transacciones.
- **Application Metrics**: Métricas internas de Superset y Cube.js vía StatsD.

**Alertas Pre-configuradas:**

- **Base de Datos**: Notifica si la latencia P99 de PostgreSQL excede **1000ms**.
- **Caché**: Notifica si la tasa de aciertos de Cube.js cae por debajo del **80%**.
- **Pipelines**: Notifica si no hubo tareas exitosas en Prefect en las últimas **24h**.

### 2.13. Optimización de Recursos

- **Superset Workers**: Se ha configurado `SERVER_WORKER_AMOUNT=5` (Optimizado para ~2 CPUs mediante la regla `2*CPU + 1`).
- **Límites de Memoria**: Servicios pesados (Superset, Cube, Postgres-Exporter) tienen límites estrictos de RAM para proteger el host.

### 2.14. Integración con Claude Desktop (Superset MCP)

Se ha integrado el **Model Control Protocol (MCP)** para permitir controlar Superset directamente desde Claude Desktop.

- **Servicio**: `superset-mcp` en el puerto **8010**.
- **Autenticación**: Automática (usa las credenciales de `.env`).
- **Capacidades**:
  - Listar y crear Dashboards/Charts.
  - Ejecutar consultas SQL (SQL Lab).
  - Gestionar Datasets y Bases de datos.

---

## PARTE 4: Personalización y Mantenimiento

### 4.1. Personalización de Marca (Logo y Favicon)

El sistema permite cambiar la imagen corporativa sin modificar el código interno:

1. **Carpeta de Activos**: Coloca tus archivos en `./superset_assets/`.
2. **Nombres Obligatorios**:
   - `logo.png`: Reemplaza el logo de Superset.
   - `favicon.png`: Reemplaza el icono de la pestaña.
3. **Aplicar Cambios**: Reinicia el servicio para refrescar el mapeo (aunque al ser volumen, suele bastar con refrescar el navegador):
   ```bash
   docker compose restart superset
   ```

### 4.2. Configuración de Subrutas (Opcional)

El proyecto está configurado para correr en la raíz (`/`). Si deseas ponerlo bajo un prefijo (ej: `/tableros`), debes actualizar:
- `docker-compose.yml`: Añadir `SCRIPT_NAME=/tu-prefijo` a los servicios.
- `superset_config.py`: `APPLICATION_ROOT` y `SESSION_COOKIE_PATH` a `/tu-prefijo`.
- `nginx.conf`: Crear una directiva `location /tu-prefijo/` y configurar el proxy correspondientemente.

### 4.3. Solución de Problemas de Construcción (Build)

En entornos con restricciones de red, la construcción puede fallar debido a bloqueos en PyPI. Se han configurado mirrors automáticos en los `Dockerfiles`. Puedes ajustar el mirror en `.env` mediante la variable `PYPI_MIRROR`.

---

## PARTE 3: Gestión del Proyecto

**Comandos Útiles:**

```bash
# Ver logs en tiempo real
docker compose logs -f [servicio]

# Reiniciar un servicio específico
docker compose restart [servicio]

# Bajar todo el stack
docker compose down
```
