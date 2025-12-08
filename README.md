# 📚 Documentación Completa de Arquitectura e Instalación de Apache Superset (v5.0.x) - Dockerizado

Este documento sirve como la guía definitiva para el despliegue de producción de Apache Superset (versión estable 5.0.x), incluyendo componentes de alto rendimiento, capa semántica (Cube.js), orquestación con Prefect y un pipeline de prueba para Machine Learning (ML).

## PARTE 1: Resumen Arquitectónico (Estructura de Producción)

La solución se estructura en capas para aislar responsabilidades y maximizar el rendimiento.

| Capa | Componente Clave | Propósito Principal |
| :--- | :--- | :--- |
| **Orquestación** | Prefect 2.x | Gestión de Pipelines de datos (ETL/ELT) y ML Ops. **(Imagen Personalizada con ML libs)** |
| **Modelado Semántico** | Cube.js (Store) | Definición centralizada de métricas y caching de pre-agregados (Motor Cube Store). |
| **Visualización/BI** | Apache Superset (v5.0.x) | Exploración de datos, Dashboards y reportes programados. |
| **Datos / Metadatos** | PostgreSQL (v16) | Almacenamiento de datos fuente, resultados de ML y metadatos de Superset. |
| **Caché / Broker** | Valkey | Reemplazo open-source de Redis para caché de Superset y broker de Celery. |
| **Proxy / Acceso** | Nginx | Puerta de enlace unificada (Puerto 80) para todos los servicios. |
| **Observabilidad** | Prometheus + Grafana | Monitoreo del estado de todos los servicios críticos. |

### 1.1. Integración de ML (Proof of Concept)

Se ha implementado un flujo de prueba de concepto (`ml_sales_pipeline.py`) que demuestra:

1. **Extracción**: Prefect verifica datos en PostgreSQL.
2. **ML**: Prefect entrena un modelo (`scikit-learn`) y genera predicciones de ventas.
3. **Carga**: Guarda resultados en la tabla `ml_prediccion_ventas`.
4. **Refresco**: Prefect notifica a Cube.js para refrescar la semántica.
5. **Visualización**: Cube.js sirve los datos frescos a Superset.

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
| **Prefect UI** | `http://TU_IP/prefect/` |
| **Grafana** | `http://TU_IP/grafana/` |
| **Cube.js API** | `http://TU_IP/cubejs/` |
| **Prometheus** | `http://TU_IP/prometheus/` |

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
2. Añadir nueva base de datos **Cube**.
3. SQLAlchemy URI: `cubejs://cube:4000?token=TU_SECRET_KEY` (El token puede ser tu `SECRET_KEY` en modo dev).

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
