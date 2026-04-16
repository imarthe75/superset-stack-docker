# ADR-006: Implementación de Redpanda para Streaming de Datos y CDC

## Estado
Propuesto (Abril 2026)

## Contexto
El Proyecto Aura requiere una capa de streaming de datos robusta, eficiente y simple para manejar el volumen creciente de eventos y la captura de cambios (CDC) desde PostgreSQL hacia ClickHouse. Anteriormente se utilizaba PeerDB, pero se ha decidido migrar a un stack basado en Redpanda y Debezium para optimizar el rendimiento y la mantenibilidad.

## Decisión
Sustituir PeerDB por Redpanda como Broker de mensajería y Debezium como motor de CDC. El flujo de datos seguirá el esquema lineal:
**PostgreSQL (WAL) -> Debezium Connector -> Redpanda (Broker) -> ClickPanda/ClickHouse Sink -> ClickHouse.**

### Puntos Clave de la Decisión:

1.  **Eficiencia (Consumo de RAM):** 
    - Redpanda está escrito en C++, lo que permite una gestión de memoria mucho más eficiente que Kafka (Java). 
    - Esto reduce drásticamente el "overhead" de la JVM y el consumo de RAM, permitiendo operar con latencias menores en hardware similar.
    
2.  **Simplicidad (Zero Zookeeper):**
    - Redpanda elimina la dependencia de Apache Zookeeper al utilizar una implementación nativa de Raft para el consenso.
    - Esto simplifica la infraestructura de Docker Compose, eliminando contenedores adicionales y reduciendo la complejidad operativa.

3.  **Rendimiento:**
    - Redpanda ofrece una latencia determinista y un alto throughput, ideal para el volumen de datos de Aura que requiere procesamiento en tiempo real para análisis en ClickHouse.
    - El uso de almacenamiento por capas (tiering) facilita la retención a largo plazo si fuera necesario.

4.  **Monitoreo y Conectividad:**
    - Se establece el uso del puerto **9092** para comunicación interna y **19092** para externa.
    - El monitoreo de salud se realizará a través de la **Admin API** en el puerto **9644**.

## Consecuencias

### Positivas:
- Reducción del uso de memoria en el stack total (permitiendo más recursos para ClickHouse).
- Menor complejidad en el despliegue (menos servicios base).
- Mejor escalabilidad y predictibilidad en la latencia.
- Compatibilidad total con el ecosistema Kafka (API compatible).

### Negativas/Riesgos:
- Curva de aprendizaje inicial para la configuración de conectores de Debezium sobre Redpanda.
- Necesidad de reconfigurar los flujos de observabilidad para monitorear los nuevos componentes.

## Notas Técnicas
- El límite de memoria para Redpanda se establece en **1GB** en el entorno de desarrollo/staging para asegurar que ClickHouse tenga prioridad de hardware.
- Es obligatorio validar que los conectores de Debezium estén en estado `RUNNING` antes de depurar inconsistencias en ClickHouse.
