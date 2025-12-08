# 📚 Documentación Completa de Arquitectura e Instalación de Apache Superset (v5.0.x) - Dockerizado

Este documento sirve como la guía definitiva para el despliegue de producción de Apache Superset (versión estable 5.0.x), incluyendo componentes de alto rendimiento, capa semántica (Cube.js) y el marco para la integración de Machine Learning (ML), adaptado para un entorno contenerizado con **Docker y Docker Compose**.

## PARTE 1: Resumen Arquitectónico (Estructura de Producción)

Esta arquitectura avanzada utiliza componentes clave para mejorar la escalabilidad, el rendimiento y la capacidad de integrar modelos de IA/ML, siendo Superset el front-end de visualización.

### 1.1. Visión General de la Arquitectura

La solución se estructura en capas para aislar responsabilidades y maximizar el rendimiento.

| Capa | Componente Clave | Propósito Principal |
| :--- | :--- | :--- |
| **Orquestación** | Prefect 2.x (o Airflow) | Gestión de Pipelines de datos (ETL/ELT) y refresco de modelos ML. |
| **Modelado Semántico** | Cube.js (Opcional) | Definición centralizada de métricas (cubos) y caching de pre-agregados. |
| **Visualización/BI** | Apache Superset (v5.0.x) | Exploración de datos, Dashboards y reportes programados. |
| **Datos / Metadatos** | PostgreSQL (v16/18) | Almacenamiento de datos fuente y base de metadatos de Superset. |
| **Caché / Broker** | Valkey | Proporciona caché a Superset y es el broker de mensajes para Celery. |
| **Observabilidad** | Prometheus + Grafana | Monitoreo del estado de todos los servicios críticos. |

### 1.2. Integración Clave: Cube.js y ML

**Cube.js (Capa Semántica)**
*   Actúa como intermediario entre Superset y PostgreSQL.
*   Asegura la consistencia definiendo métricas y lógica en código (Data Schema).
*   Su principal beneficio es el Caching de Pre-Agregados, sirviendo consultas recurrentes de Superset a velocidad de caché, reduciendo la carga de PostgreSQL.

**Integración con IA/ML (Enfoque Robusto)**
La IA se integra de forma externa a Superset a través del orquestador (Prefect/Airflow):
1.  El orquestador ejecuta el entrenamiento del modelo ML.
2.  El resultado del modelo (predicciones, scores, clasificaciones) se guarda como datos en una tabla de PostgreSQL.
3.  Superset simplemente consulta y visualiza esta tabla de resultados. Esto es más escalable que la integración directa de IA en la interfaz de Superset.

---

## PARTE 2: Guía de Instalación Avanzada (Docker)

Esta guía asume que ya tienes instalado **Docker** y **Docker Compose** en tu servidor Ubuntu/Linux.

### 2.1. Estructura del Proyecto y Requisitos

El proyecto ya incluye un `docker-compose.yml` preconfigurado con:
*   **PostgreSQL**: Base de datos de metadatos y warehousing.
*   **Valkey**: Reemplazo open-source de Redis para caché y broker.
*   **Superset**: Imagen personalizada con drivers necesarios.
*   **Celery w/ Beat**: Para tareas asincrónicas (reportes, alertas).
*   **Nginx, Prometheus, Grafana, Prefect**: Servicios auxiliares.

**Clonar/Preparar el entorno:**

```bash
# Copiar variables de entorno de ejemplo
cp .env.example .env

# Editar .env con tus credenciales SMTP y SECRET_KEY segura
nano .env
```

### 2.2. Despliegue de Servicios (Valkey, Postgres, etc.)

A diferencia de la instalación manual, Docker gestiona las versiones y dependencias. Al ejecutar el stack, se descargarán las imágenes correctas (Postgres 16+, Valkey, etc.).

```bash
# Levantar todo el stack en segundo plano
docker compose up -d
```

Verifica que los servicios estén corriendo:
```bash
docker compose ps
# Todos los estados deberían ser "Up" o "healthy"
```

### 2.3. Inicialización de Superset

Una vez que los contenedores estén arriba, debemos inicializar la aplicación Superset. Ejecuta estos comandos **dentro** del contenedor:

```bash
# 1. Crear usuario administrador
docker compose exec superset superset fab create-admin \
  --username admin \
  --firstname Superset \
  --lastname Admin \
  --email admin@example.com \
  --password admin

# 2. Inicializar base de datos (Metadatos)
docker compose exec superset superset db upgrade

# 3. Inicializar roles y permisos
docker compose exec superset superset init
```

### 2.4. Integración de Cube.js (Opcional/Avanzado)

Para añadir Cube.js al stack Docker, agrega el siguiente servicio a tu `docker-compose.yml`:

```yaml
  cube:
    image: cubejs/cube:latest
    ports:
      - "4000:4000"
    environment:
      - CUBEJS_DB_TYPE=postgres
      - CUBEJS_DB_HOST=postgres
      - CUBEJS_DB_NAME=superset
      - CUBEJS_DB_USER=superset
      - CUBEJS_DB_PASS=superset
      - CUBEJS_API_SECRET=tu_api_secret_seguro_aqui
    depends_on:
      - postgres
      - valkey
    volumes:
      - ./cube_schema:/cube/conf/schema
```

Luego, en Superset, conecta Cube.js como una base de datos usando la URL:
`cubejs://cube:4000?token=TU_CUBE_API_TOKEN_GENERADO`

### 2.5. Gestión y Logs

Para ver los logs de cualquier servicio (ej. si falla la conexión a base de datos):

```bash
# Ver logs de Superset
docker compose logs -f superset

# Ver logs del Worker (Celery)
docker compose logs -f celery-worker
```

---

## PARTE 3: Pasos para subir a GitHub

Para subir este proyecto a tu repositorio de GitHub, sigue estos pasos en tu terminal (en la raíz del proyecto):

**1. Inicializar Git y .gitignore**
Asegúrate de tener el archivo `.gitignore` (ya creado en este proyecto) para no subir credenciales (`.env`) o carpetas pesadas (`venv/`, `data/`).

```bash
git init
git add .
git commit -m "Initial commit: Superset v5 Stack with Docker"
```

**2. Renombrar rama principal (Standard)**
```bash
git branch -M main
```

**3. Conectar con GitHub**
Crea un repositorio **vacío** en GitHub (sin README, sin .gitignore). Copia la URL del repositorio (HTTPS o SSH).

```bash
# Reemplaza URL_DEL_REPO con tu link, ej: https://github.com/usuario/mi-superset.git
git remote add origin URL_DEL_REPO
```

**4. Subir código**
```bash
git push -u origin main
```

¡Listo! Tu arquitectura de Superset estará versionada en GitHub.
