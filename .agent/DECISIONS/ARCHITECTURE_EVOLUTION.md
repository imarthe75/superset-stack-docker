# 📈 EVOLUCIÓN ARQUITECTÓNICA: v7.5 → v8.0

## Timeline

### v7.0 (2025-Q3): Monolith
- Postgres only
- Superset queries: 30-60s
- No real-time

### v7.5 (2025-Q4 - ACTUAL): Modern Data Stack
- ✅ ClickHouse added
- ✅ redpanda CDC for ingesta
- ✅ dbt Silver/Gold layers
- ✅ Cube.js semantic
- ✅ Valkey cache
- Query latency: 0.3s median

### v8.0 (2026-Q1 - CURRENT): AI-Augmented BI
- ✅ Vanna AI (Text-to-SQL)
- ✅ Flowise (LLM workflows)
- ✅ ChromaDB internal knowledge base
- ✅ MCP server for agent autonomy
- ✅ Golden sets para model training

## Cambios en v8.0

### Adiciones
1. **ChromaDB** para indexar configuraciones
2. **brain_index.py** para indexación periódica
3. **MCP Server** para automatización
4. **STATE.md** tracking de versiones

### No Changes (stable)
- ClickHouse architecture (proven)
- redpanda CDC (working well)
- Cube.js semantic layer (cache optimized)

## Roadmap 2026

| Trimestre | Feature | Impact |
|-----------|---------|--------|
| Q2 | Kafka real-time streams | -98% latency (redpanda 30s → Kafka <1s) |
| Q2 | Sharding ClickHouse | +10x capacity |
| Q3 | Vertex AI integration | AutoML predictions |
| Q3 | dbt Cloud sync | centralized lineage |
| Q4 | Materialize view refreshes | probabilistic |

---
**Maintainer**: Data Engineering Team  
**Last update**: 2026-04-15
