# Guía de Modelado Semántico (Cube.js)
# Rol: Data Engineer / Analista BI
# Versión: Aura v8.3

Esta guía explica cómo cumplir con la **Regla de Semántica de Aura**: centralizar métricas en Cube.js en lugar de Superset.

---

## 1. Estructura de un Cubo
Los archivos de esquema se encuentran habitualmente en la carpeta `cube_schema/`.

Ejemplo de un cubo básico para la tabla `fct_sales` (ClickHouse):

```javascript
cube(`Sales`, {
  sql: `SELECT * FROM aura_gold.fct_sales`,

  measures: {
    count: {
      type: `count`,
      drillMembers: [id, order_date]
    },
    totalAmount: {
      sql: `amount`,
      type: `sum`,
      format: `currency`
    }
  },

  dimensions: {
    id: {
      sql: `id`,
      type: `number`,
      primaryKey: true
    },
    category: {
      sql: `category`,
      type: `string`
    },
    orderDate: {
      sql: `order_date`,
      type: `time`
    }
  }
});
```

---

## 2. Configuración de Pre-agregaciones (Rollups)
Para que los tableros carguen en milisegundos, definimos pre-agregaciones que se guardan en **Valkey**.

```javascript
preAggregations: {
  main: {
    measures: [Sales.totalAmount],
    dimensions: [Sales.category],
    timeDimension: Sales.orderDate,
    granularity: `day`
  }
}
```

---

## 3. Flujo de Trabajo
1.  **Crear archivo:** Crea un archivo `.js` o `.yml` en `cube_schema/`.
2.  **Validar:** Cube.js recarga automáticamente. Revisa los logs: `docker compose logs -f cube`.
3.  **Probar:** Entra al Playground de Cube (`http://<IP>:4000`) para verificar que las métricas calculen bien.
4.  **Consumir:** En Superset, el Cubo aparecerá como una tabla dentro de la conexión `Cube SQL API`.

---

## 4. Mejores Prácticas
- **Nombres Claros:** Usa nombres de métricas que los usuarios de negocio entiendan (ej. `Ingresos Totales` en lugar de `suma_amount`).
- **No lógica en Superset:** Si necesitas un cálculo (ej. `Margen = (Venta - Costo) / Venta`), defínelo en Cube, no en las columnas calculadas de Superset.
- **Seguridad:** Usa `queryRewrite` en Cube si necesitas aplicar filtros de seguridad (RLS) basados en el usuario.
