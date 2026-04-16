# Guía de Gestión de Identidad (Keycloak)
# Rol: Administrador de Seguridad / IT
# Versión: Aura v8.3

Aura v8.3 utiliza Keycloak como el único proveedor de identidad (IdP) para Superset, Grafana y otras herramientas mediante el protocolo OIDC (OpenID Connect).

---

## 1. Acceso a la Consola
- **URL:** `http://<IP>/auth/admin/`
- **Realm:** `superset` (o el nombre configurado en `.env`)

---

## 2. Gestión de Usuarios

### Crear un Usuario
1. Ve a **Users** -> **Add user**.
2. Define `Username`, `Email`, `First Name` y `Last Name`.
3. En la pestaña **Credentials**, define una contraseña inicial y desactiva "Temporary" si no quieres que la cambien al primer login.

---

## 3. Mapeo de Roles (RBAC)
Aura está configurado para que los roles de Keycloak se sincronicen con Superset.

| Rol en Keycloak | Rol en Superset | Permisos |
|-----------------|-----------------|----------|
| `admin`         | `Admin`         | Acceso total al stack |
| `alpha`         | `Alpha`         | Puede crear queries y dashboards |
| `gamma`         | `Gamma`         | Solo lectura de dashboards compartidos |

**Para asignar un rol:**
1. Ve al usuario -> **Role Mapping**.
2. Asigna el rol correspondiente del Realm.

---

## 4. Troubleshooting de Acceso
- **Invalid Parameter: redirect_uri:** La URL en el browser no coincide con las URLs permitidas en el Client de Keycloak. Verifica que el `SERVER_IP` en `.env` sea correcto.
- **Usuario no ve datos:** Revisa si el usuario tiene los roles adecuados y si existe RLS (Row Level Security) configurado en Superset o ClickHouse.
- **Login fallido (Internal Server Error):** Suele ser un problema de comunicación interna entre Superset y Keycloak. Verifica que Superset pueda llegar a `http://keycloak:8080`.
