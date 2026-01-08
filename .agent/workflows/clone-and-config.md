---
description: Guía para clonar el proyecto y configurar múltiples bases de datos en Cube.js
---

# Clonación y Configuración Multi-DB

Este workflow detalla los pasos para replicar el entorno en un nuevo servidor y conectar Cube.js a múltiples orígenes de datos.

## 1. Clonación del Proyecto

En el nuevo servidor, ejecuta:

```bash
git clone <URL_DEL_REPOSITORIO> superset-project
cd superset-project
```

## 2. Configuración de Variables de Entorno

Copia el archivo de ejemplo y genera una clave de seguridad:

```bash
cp .env.example .env
# Generar una clave secreta para SECRET_KEY en .env
openssl rand -base64 42
```

Edita el archivo `.env` con las credenciales correspondientes a tu nuevo entorno (SMTP, Postgres, etc.).

## 3. Agregar Nuevas Bases de Datos a Cube.js

Cube.js soporta múltiples de orígenes de datos mediante variables de entorno en el `docker-compose.yml`.

### Paso A: Definir las fuentes en `docker-compose.yml`

Localiza el servicio `cube` y modifica las siguientes variables:

1. **CUBEJS_DATASOURCES**: Lista separada por comas de los identificadores de tus fuentes (ej: `default,ventas_pro,clientes_db`).
2. **Configuración por Fuente**: Para cada fuente adicional (ej: `ventas_pro`), define sus credenciales siguiendo el patrón `CUBEJS_DS_<ID_EN_MAYUSCULAS>_<PROPIEDAD>`.

Ejemplo:

```yaml
environment:
  - CUBEJS_DATASOURCES=default,ventas_pro
  # Fuente principal (default)
  - CUBEJS_DB_TYPE=postgres
  - CUBEJS_DB_HOST=postgres
  - CUBEJS_DB_NAME=sales_data
  # Nueva fuente (ventas_pro)
  - CUBEJS_DS_VENTAS_PRO_TYPE=postgres
  - CUBEJS_DS_VENTAS_PRO_HOST=10.0.0.5
  - CUBEJS_DS_VENTAS_PRO_PORT=5432
  - CUBEJS_DS_VENTAS_PRO_NAME=db_produccion
  - CUBEJS_DS_VENTAS_PRO_USER=usuario_read
  - CUBEJS_DS_VENTAS_PRO_PASS=password_seguro
```

### Paso B: Usar la fuente en los esquemas (`cube_schema/`)

En tus archivos de modelo `.js` o `.yml`, especifica la fuente usando la propiedad `dataSource`:

```javascript
cube(`Pedidos`, {
  sql: `SELECT * FROM public.pedidos`,
  dataSource: `ventas_pro`, // Debe coincidir con el nombre en CUBEJS_DATASOURCES
  
  measures: { ... },
  dimensions: { ... }
});
```

## 4. Inicialización

Una vez configurado, levanta el stack:

```bash
docker compose up -d
```

Si es la primera vez, asegúrate de inicializar Superset:

```bash
docker compose exec superset superset-init
```
