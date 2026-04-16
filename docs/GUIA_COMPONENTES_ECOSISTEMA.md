# Guía de Componentes del Ecosistema Aura
# Versión: Aura v8.3
# Fecha: 2026-04-16

Este documento clasifica y explica cómo interactuar con cada componente del Aura Intelligence Suite.

---

## 1. Clasificación General

| Nivel | Manipulación | Componentes |
|-------|--------------|-------------|
| **Capa de Usuario** | **Alta** | Superset, Grafana, Flowise, Vanna AI |
| **Capa de Ingeniería**| **Media** | PeerDB, Cube.js, dbt, Prefect |
| **Capa de Infraestructura**| **Baja (No Tocar)**| Valkey, Postgres, Temporal, OpenSearch |

---

## 2. Capa de Usuario (Interfaces de Negocio)

### A. Apache Superset (Exploración Visual)
- **Función:** Principal herramienta de visualización y Dashboards.
- **Cómo manipular:** Crear "Datasets" (apuntando a Cube SQL API), construir "Charts" y armar "Dashboards".
- **Ejemplo:** Crear un gráfico de barras que muestre las ventas por categoría en tiempo real.

### B. Vanna AI (IA Text-to-SQL)
- **Función:** Permite hacer preguntas en lenguaje natural y genera SQL automáticamente.
- **Cómo manipular:** Entrenar con "Golden Sets" (ejemplos de preguntas/respuestas) para mejorar la precisión.
- **Ejemplo:** Preguntar "¿Cuánto vendimos ayer en México?" y recibir el gráfico instantáneamente.

### C. Flowise (Chatbots Avanzados)
- **Función:** Orquestación de flujos de IA (RAG) utilizando LLMs.
- **Cómo manipular:** Diseñar flujos en la UI visual uniendo nodos (Chat Model, Vector DB, Prompt).
- **Ejemplo:** Un chatbot integrado que consulta el manual de usuario para responder dudas técnicas.

### D. Grafana (Monitoreo Técnico)
- **Función:** Supervisión de la salud del hardware y del stack.
- **Cómo manipular:** Solo para consulta de Dashboards de salud (CPU, RAM, Lag de Replicación).
- **Ejemplo:** Revisar si el "Replication Lag" de PeerDB supera los 30 segundos.

---

## 3. Capa de Ingeniería (Ingestión y Modelado)

### A. PeerDB (Capa CDC)
- **Función:** Replicación en tiempo real desde Postgres hacia ClickHouse.
- **Cómo manipular:** Crear "Peers" (conexiones) y "Mirrors" (reglas de réplica).
- **Recomendación:** Solo manipular si se añade una nueva fuente de datos externa.

### B. Cube.js (Capa Semántica)
- **Función:** Centraliza la lógica de negocio (métricas) y acelera consultas.
- **Cómo manipular:** Editar archivos `.js` o `.yaml` en `cube_schema/`.
- **Ejemplo:** Definir que el "Margen de Utilidad" es `(Ventas - Costos) / Ventas`.

### C. dbt (Transformación)
- **Función:** Limpieza y transformación de datos en ClickHouse (Bronze → Silver → Gold).
- **Cómo manipular:** Editar modelos SQL en la carpeta `dbt_aura/`.
- **Recomendación:** Usar para procesos batch complejos que el CDC no cubra.

---

## 4. Capa de Infraestructura (Manos Fuera)

Estos componentes son motores internos. **No se recomienda modificarlos** a menos que haya una falla crítica:

- **Valkey:** Caché ultrarrápida para Superset y Cube.
- **Postgres (Metadata):** Almacena usuarios, permisos y flujos. No borrar.
- **Temporal:** Orquestador interno para los procesos de réplica de PeerDB.
- **OpenSearch:** Motor de búsqueda para metadatos de OpenMetadata.

---

## 5. Regla de Oro del Ecosistema
**"El cambio fluye hacia adelante":** Si necesitas una nueva métrica, agrégala en **Cube.js**, no en Superset. Si necesitas un nuevo dato, regístralo en **PeerDB**, no conectes Superset al origen.
