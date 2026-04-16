# Guía de Configuración: Bases de Datos Externas (PostgreSQL)
# Rol: Administrador de Datos / DevOps
# Versión: Aura v8.3

Esta guía detalla los pasos necesarios para preparar una base de datos PostgreSQL externa para ser integrada en Aura via PeerDB.

---

## 1. Requisitos de Red
- La base de datos externa debe ser alcanzable por el contenedor `peerdb`.
- Si está en el mismo host: usar la IP de la interfaz `docker0` o el nombre del contenedor si comparten red.
- Si está en un servidor externo: asegurar que el Firewall permita tráfico al puerto `5432` desde la IP del servidor Aura.

---

## 2. Configuración en la Base de Origen (PostgreSQL)

Para que el CDC (Change Data Capture) funcione, es obligatorio habilitar la replicación lógica.

### A. Editar `postgresql.conf`
Asegúrate de tener los siguientes parámetros configurados y reiniciar la base de datos:
```ini
wal_level = logical
max_replication_slots = 5  # Mínimo 1 por cada mirror de PeerDB
max_wal_senders = 5        # Mínimo 1 por cada mirror de PeerDB
```

### B. Editar `pg_hba.conf`
Permite la conexión desde el servidor Aura:
```conf
# Reemplazar <AURA_IP> por la IP del servidor de Aura Suite
host    all             all             <AURA_IP>/32            md5
host    replication     all             <AURA_IP>/32            md5
```

---

## 3. Preparación del Usuario y Publicación

Ejecuta lo siguiente como superusuario en la base de datos que deseas replicar:

```sql
-- 1. Crear usuario para PeerDB
CREATE USER aura_peerdb WITH PASSWORD 'tu_password_seguro' REPLICATION;

-- 2. Dar permisos de lectura en el esquema
GRANT USAGE ON SCHEMA public TO aura_peerdb;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO aura_peerdb;

-- 3. Crear Publicación para CDC (obligatorio para PeerDB)
-- Puedes incluir todas las tablas o solo algunas específicas
CREATE PUBLICATION aura_external_publication FOR ALL TABLES;
```

---

## 4. Registro en PeerDB (Aura Console)

1. Accede a la consola de PeerDB: `http://<TU_IP>/peerdb/`
2. Ve a **PEERS** -> **CREATE PEER**.
3. Selecciona **Postgres**.
4. Completa los datos:
   - **Host:** IP de tu base de datos externa.
   - **User:** `aura_peerdb`
   - **Password:** `tu_password_seguro`
   - **Database:** nombre_de_tu_db
5. Haz clic en **Validate & Create**.

---

## 5. Troubleshooting Común
- **Error "Logical encoding not supported":** El `wal_level` no es `logical`.
- **Error "Connection Refused":** Revisa el Firewall y la directiva `listen_addresses` en `postgresql.conf` (debe ser `*` o la IP correcta).
- **Lag alto:** Revisa la latencia de red entre el origen y el servidor Aura.
