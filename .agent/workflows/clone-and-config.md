---
description: Guía para clonar el proyecto y configurar múltiples bases de datos en Cube.js
---

# Clonación y Configuración Multi-DB

Este workflow detalla los pasos para replicar el entorno en un nuevo servidor Ubuntu y conectar Cube.js a múltiples orígenes de datos.

## 0. Preparación del Sistema

Si el servidor es nuevo, actualiza el sistema e instala las herramientas según tu distribución:

### Ubuntu / Debian

```bash
# 1. Actualizar e instalar dependencias iniciales y Git
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg git

# 2. Añadir la llave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Configurar el repositorio oficial (Compatible con Ubuntu 22.04 y 24.04)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Instalar Docker y sus plugins
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Verificar e iniciar servicio
sudo systemctl enable --now docker
docker --version
git --version
```

### RHEL / CentOS / Rocky / AlmaLinux

```bash
# Actualizar e instalar Git
sudo dnf update -y
sudo dnf install -y curl git-all

# Configurar repositorio de Docker
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Iniciar y habilitar Docker (Crucial en RHEL)
sudo systemctl enable --now docker

# Verificar instalaciones
docker --version
git --version
```

*Nota: Para correr docker sin sudo, ejecuta `sudo usermod -aG docker $USER` y reinicia tu sesión.*

## 1. Clonación del Proyecto

En el nuevo servidor, ejecuta:

```bash
git clone <URL_DEL_REPOSITORIO> superset-project
cd superset-project
```

## 2. Configuración de Variables de Entorno

Copia el archivo de ejemplo y genera una clave de seguridad automáticamente:

```bash
cp .env.example .env
# Generar e insertar una clave secreta para SECRET_KEY en el .env
sed -i "s|SECRET_KEY=.*|SECRET_KEY=$(openssl rand -base64 42)|" .env
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

Una vez configurado, construye e inicia el stack.

> [!IMPORTANT]
> El paso de construcción es **obligatorio** para habilitar la funcionalidad de **Reportes y Alertas** (instala Playwright y Chromium).
> Si este paso falla con errores de red, ve directamente a la **Sección 7: Solución de Problemas de Red**.

```bash
# 1. Construir imágenes personalizadas (Obligatorio para Reportes)
docker compose build
```

# 2. Levantar el stack

docker compose up -d

# 3. Inicializar Superset (Solo la primera vez)

# Migrar la base de datos

docker compose exec superset superset db upgrade

# Crear usuario admin

docker compose exec superset superset fab create-admin --username admin --password admin --firstname Superset --lastname Admin --email <admin@example.com>

# Inicializar roles y permisos

docker compose exec superset superset init

```

## 5. Exploración y Modelado (Playground)

Si has conectado fuentes externas y quieres explorarlas sin escribir código manualmente:

1. **Accede al Playground**: Ve a `http://localhost:4000` en tu navegador.
2. **Introspección**: En la pestaña **"Data Model"**, selecciona la base de datos (ej: `ventas_pro`) para ver todas sus tablas y columnas.
3. **Generación de Código**: Selecciona las tablas que necesites y usa el botón **"Generate Schema"**. Esto creará los archivos `.yml` o `.js` automáticamente en la carpeta `cube_schema/`.
4. **Validación**: Usa la pestaña **"Build"** para ejecutar consultas rápidas y verificar que los datos fluyen correctamente desde la fuente externa.

## 6. Monitoreo y Depuración (Entorno)

Si prefieres explorar el estado de Cube.js directamente desde la terminal del servidor:

1. **Verificar Conexión y Errores**: Visualiza los logs en tiempo real para confirmar que las fuentes de datos se conectan correctamente:

   ```bash
   docker compose logs -f cube
   ```

1. **Confirmar Carga de Esquemas**: Busca mensajes tipo `Compiling schema` o `Schema compiled` para asegurar que tus archivos en `cube_schema/` no tienen errores de sintaxis.
2. **Modo Desarrollo**: Asegúrate de que `CUBEJS_DEV_MODE=true` esté activo en el `docker-compose.yml` para habilitar el Playground y el refresco automático de esquemas al editar archivos.

## 7. Solución de Problemas de Red (Build Error)

Si obtienes errores de tipo `Network is unreachable` o `Failed to establish a new connection` durante el `docker compose build`:

1. **Configurar DNS y MTU**: Crea o edita el archivo `/etc/docker/daemon.json`:

   ```bash
   sudo nano /etc/docker/daemon.json
   ```

2. **Agregar Configuración**: Pega el siguiente contenido (ajusta el MTU si es necesario, ej: 1460 para GCP o 1500 estándar):

   ```json
   {
     "dns": ["8.8.8.8", "8.8.4.4"],
     "mtu": 1460
   }
   ```

3. **Reiniciar Docker**:

   ```bash
   sudo systemctl restart docker
   ```

4. **Reintentar**: Ejecuta `docker compose build` nuevamente.
