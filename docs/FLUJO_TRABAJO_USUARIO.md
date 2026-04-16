# Guía de Flujo de Trabajo: Del Origen a Superset
# Rol: Analista de Datos / Usuario Superset
# Versión: Aura v8.3

Esta guía explica el camino que recorren tus datos desde que están en tu base de datos externa hasta que los visualizas en un dashboard de Superset.

---

## El Camino del Dato (Arquitectura de Tríada)

Aura utiliza una arquitectura de alto rendimiento para asegurar que Superset nunca sea lento. El flujo es:
**Origen** → **PeerDB** (Réplica en tiempo real) → **ClickHouse** (Motor Analítico) → **Cube.js** (Capa Semántica) → **Superset** (Visualización).

---

## Fase 1: Sincronización (PeerDB)
*Solicita a tu administrador que realice este paso.*
1. Se crea un **Mirror** en PeerDB que escucha los cambios en tu base de datos de origen.
2. Los datos se copian automáticamente a la base de datos `aura_raw` en ClickHouse.
3. Cualquier cambio en el origen se refleja en Clickhouse en menos de 5 segundos.

---

## Fase 2: Modelado (dbt - Opcional)
Si tus datos necesitan limpieza, joins complejos o transformaciones (ej. pasar de Bronze a Gold), se utiliza **dbt**.
- El equipo de ingeniería de datos creará modelos en la capa `aura_gold`.
- Esto asegura que los datos estén pre-procesados y listos para ser consumidos.

---

## Fase 3: Capa Semántica (Cube.js)
**Paso Obligatorio:** Antes de ir a Superset, tus tablas deben estar definidas en **Cube.js**.
1. Se crea un archivo `.yaml` o `.js` en el esquema de Cube.
2. Aquí se definen las **Métricas** (ej. `Suma de Ventas`, `Promedio de Edad`) y **Dimensiones** (ej. `Fecha`, `Categoría`).
3. El beneficio: Tus métricas siempre darán el mismo resultado, sin importar quién las consulte, y cargarán instantáneamente gracias a la caché de Valkey.

---

## Fase 4: Visualización en Superset
Una vez que el Cubo está listo:
1. Entra a **Superset**.
2. Ve a **Settings** -> **Database Connections**. Tu administrador habrá conectado ya el origen `Cube SQL API`.
3. Crea un **Dataset** apuntando a tu Cubo (ej. `SalesCube`).
4. ¡Empieza a crear tus gráficos!

---

## Resumen de Reglas de Oro
1. **No conectar Superset a fuentes externas:** Siempre usamos ClickHouse como puente.
2. **Todo pasa por Cube:** Si no está en Cube, no se visualiza en Superset. Esto garantiza que el sistema sea siempre rápido.
3. **Validación de Datos:** Si ves una discrepancia, revisa primero el `replication_lag` en el dashboard de Monitoreo de Aura.
