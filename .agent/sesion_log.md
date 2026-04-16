# 📝 Log de Sesión: Re-Arquitectura Aura Data Pipeline (v0.8-stable)
**Fecha:** 2026-04-16  
**Agente:** Antigravity (Anticipatory Resident Agent)  
**Estado:** ✅ Migración técnica completada y sincronizada en Git.

---

## 🚀 Resumen de Cambios

Se ha ejecutado una de las decisiones de arquitectura más críticas para el **Proyecto Aura**: la sustitución de **PeerDB/Temporal** por un stack productivo de alto rendimiento basado en **Redpanda** (C++) y **Debezium**.

### 1. Re-Arquitectura del Data Pipeline
- **Abandono de PeerDB**: Se eliminaron los servicios `peerdb`, `peerdb-ui`, `peerdb-worker` y `temporal`.
- **Implementación de Redpanda**: Integrado como broker de mensajes ultra-rápido (< 1GB RAM) ocupando los puertos `9092` (interno), `19092` (externo) y `9644` (Admin).
- **Implementación de Debezium**: Añadido como motor de Kafka Connect para la captura de cambios (CDC) desde PostgreSQL.

### 2. Configuración de Conectores (Connectors-as-Code)
- **Directorio `connectors/`**: Creado para centralizar las configuraciones JSON de los pipelines.
- **Postgres Source**: Configurado para capturar cambios de `sales_data` usando `pgoutput`.
- **ClickHouse Sink**: Configurado con el plugin oficial de ClickHouse y transformaciones `Debezium Unwrap` para aplanar registros en tiempo real.

### 3. Infraestructura y Operaciones
- **Build Automático**: Se creó un `Dockerfile` especializado para `debezium-connector` que pre-instala el plugin de ClickHouse.
- **Visualización**: Se introdujo **Redpanda Console** (`/redpanda/`) para la inspección visual de tópicos y estado de conectores.
- **Auto-Configuración**: Nuevo servicio `init-connectors` que inyecta las configuraciones vía API REST al levantar el stack.

### 4. Gobernanza y Documentación (.agent/)
- **ADR-006**: Documentación formal de la decisión técnica y trade-offs.
- **MAP.md**: Actualizada la topología de red y flujo de datos lineal.
- **AGENT.md**: Nuevas reglas de observabilidad para Redpanda y Debezium.
- **RULES.md**: Actualizadas reglas innegociables (MDS-05, SEC-07, etc.).
- **STATE.md**: Sincronizado el estado v0.8 y log de sesiones.

---

## 📈 Impacto en el Proyecto
- **Reducción de RAM**: Se estima un ahorro de ~1.5GB de RAM al eliminar Temporal y PeerDB.
- **Simplicidad**: El stack ahora es "Zookeeperless", facilitando su mantenimiento.
- **Observabilidad**: Integración nativa con Prometheus para todas las métricas de streaming.

---

## 📋 Próximos Pasos (Pendientes)
1. **Validación en Vivo**: Ejecutar `docker compose up -d --build` para validar el pull de imágenes y construcción del conector.
2. **Prueba de Ingesta**: Validar que los datos de Postgres lleguen a `aura_raw` en ClickHouse con latencia sub-segundo.
3. **Optimización dbt**: Ajustar los modelos de `aura_silver` si es necesario (aunque el unwrap de Debezium mantiene compatibilidad con el esquema previo).

---
*Este documento es parte de la memoria histórica del Agente Residente Aura.*
