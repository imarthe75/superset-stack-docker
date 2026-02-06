# 📚 Documentación Completa de Arquitectura e Instalación de Apache Superset (v6.0.0) - Dockerizado

Este documento sirve como la guía definitiva para el despliegue de producción de Apache Superset (versión estable v6.0.0), incluyendo componentes de alto rendimiento, capa semántica (Cube.js), orquestación con Prefect (v3.x) y un pipeline de prueba para Machine Learning (ML).

## PARTE 1: Resumen Arquitectónico (Estructura de Producción)

La solución se estructura en capas para aislar responsabilidades y maximizar el rendimiento.

| Capa | Componente Clave | Propósito Principal |
| :--- | :--- | :--- |
| **Orquestación** | Prefect v3.x | Gestión de Pipelines de datos (ETL/ELT) y ML Ops. **(Imagen Personalizada con ML libs)** |
| **Modelado Semántico** | Cube.js (v0.36.0) | Definición centralizada de métricas y caching de pre-agregados (Motor Cube Store). |
| **Visualización / BI** | Apache Superset (v6.0.0) | Exploración de datos, Dashboards y reportes programados. |
| **Datos / Metadatos** | PostgreSQL (v18.1) | Almacenamiento de datos fuente, resultados de ML y metadatos de Superset. |
| **Caché / Broker** | Valkey (v8.0) | Reemplazo open-source de Redis para caché de Superset y broker de Celery. |
| **Proxy / Acceso** | Nginx (v1.27) | Puerta de enlace unificada (Puerto 80) para todos los servicios. |
| **Identidad** | Keycloak (v26.5.0) | Gestión de identidad y acceso (OIDC) en Puerto 8001. |
| **Observabilidad** | Prometheus (v2.55.1) + Grafana (v12.3.1) | Monitoreo del estado de todos los servicios críticos. |
| **Métricas Host** | cAdvisor (v0.51.0) | Exportador de métricas de contenedores para Prometheus. |

### 1.1. Integración de ML (Proof of Concept)

Se ha implementado un flujo de prueba de concepto (`ml_sales_pipeline.py`) que demuestra:

1. **Extracción**: Prefect verifica datos en PostgreSQL.
2. **ML**: Prefect entrena un modelo (`scikit-learn`) y genera predicciones de ventas.
3. **Carga**: Guarda resultados en la tabla `ml_prediccion_ventas`.
4. **Refresco**: Prefect notifica a Cube.js para refrescar la semántica.
5. **Visualización**: Cube.js sirve los datos frescos a Superset.

### 1.2. Diagrama de Arquitectura

```mermaid
graph TD
    User((Usuario)) --> Nginx[Nginx Proxy :80]
    
    subgraph "Public Services"
        Nginx --> Superset[Apache Superset :8088]
        Nginx --> Keycloak[Keycloak :8001]
        Nginx --> PrefectUI[Prefect UI :4200]
        Nginx --> Grafana[Grafana :3000]
    end

    subgraph "Data & Logic"
        Superset --> Postgres[(PostgreSQL :5432)]
        Superset --> Valkey[Valkey Cache :6379]
        Superset --> Cube[Cube.js :4000]
        Cube --> Postgres
        Prefect[Prefect Server] --> Postgres
        Prefect --> Cube
    end

    subgraph "Observability"
        Prometheus --> Superset
        Prometheus --> Postgres
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

> [!TIP]
> **Guía de Configuración**: Para conectar tu Claude Desktop (Windows/Mac) a este servidor, sigue la guía detallada:
> [👉 Ver Guía de Conexión (docs/claude_setup.md)](docs/claude_setup.md)

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
