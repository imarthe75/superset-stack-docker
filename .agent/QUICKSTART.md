# 🌌 AGENTE RESIDENTE AURA v0.8 — GUÍA DE INICIO RÁPIDO

## ¿Qué es Aura v0.8?

**Aura Intelligence** es un agente residente autorregulado que mantiene la salud operacional de tu Modern Data Stack:

```
┌─────────────────────────────────────────────────────┐
│         Agente Residente Aura (v0.8)                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  COGNITIVO:      RULES.md + MAP.md + DECISIONS/    │
│  MEMORIA:        ChromaDB + brain_index.py (RAG)   │
│  ACCIÓN:         MCP Server (docker-compose ops)   │
│  VALIDACIÓN:     Golden Sets + Great Expectations  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ 5 Minutos: Setup Inicial

### Paso 1: Instalar Dependencias
```bash
cd /home/casmartsuperset/superset

# Instalar ChromaDB + LangChain + embeddings
pip install -r .agent/requirements.txt
```

**Esperado:**
```
Collecting chromadb==0.5.3
Collecting langchain==0.1.15
Collecting sentence-transformers==2.2.2
...
Successfully installed chromadb langchain sentence-transformers
```

### Paso 2: Indexar Base de Conocimiento
```bash
# Primera indexación (2-3 min)
python .agent/brain_index.py --index

# Esperado:
# ✅ Indexed 24 chunks from superset_config.py
# ✅ Indexed 12 chunks from Cube schemas
# ✅ Indexed 156 chunks from dbt models
# ✅ Indexed 8 chunks from golden sets
# ✅ Indexation complete! Total chunks: 200
```

### Paso 3: Validar Memoria
```bash
# Test query
python .agent/brain_index.py --query "¿cómo se calcula lifetime_value?"

# Esperado:
# 🔍 Querying: ¿cómo se calcula lifetime_value?
# [1] dbt_model/marts/dim_customer.sql (dbt_model)
#     Content: SELECT customer_id, SUM(amount) as lifetime_value FROM...
```

✅ **Agente listo**

---

## 🎯 Operaciones Diarias

### 1. Revisar Estado del Stack
```bash
# Ver estado de Redpanda (Broker Health)
curl "http://localhost:9644/v1/status/ready"
# Esperado: 200 OK

# Ver estado de conectores Debezium
curl "http://localhost:8083/connectors?expand=status" | jq '.'
# Esperado: connectors in state "RUNNING"
```

### 2. Ejecutar Transformaciones
```bash
# Vía Prefect UI: http://localhost:4200
# O manual:
docker exec dbt-runner dbt run --select fct_sales

# Ejecutar tests de integridad
docker exec dbt-runner dbt test --select fct_sales
```

### 3. Indexación Periódica
```bash
# Ejecutar daemon (re-indexar cada 6h)
python .agent/brain_index.py --daemon

# O programar con cron:
0 */6 * * * cd /home/casmartsuperset/superset && \
            python .agent/brain_index.py --index >> .agent/logs/index.log
```

---

## 📖 Estructura de Carpetas

```
.agent/
├── 📄 RULES.md
│   └─ Innegociables de operación (SLA < 1s, OIDC, 99% precisión)
│
├── 📄 MAP.md
│   └─ Arquitectura completa: OLTP → OLAP → BI → AI
│
├── 📄 CONTEXT.md
│   └─ Campos críticos por dominio (Sales, Customer, Product)
│       + Validaciones + Golden sets
│
├── 📄 STATE.md
│   └─ Estado actual v0.8 + log de sesiones + deudas técnicas
│
├── 📄 README_v8.md
│   └─ Entregables completados + checklist + KPIs
│
├── 🐍 brain_index.py
│   └─ Indexador automático (ChromaDB + LangChain)
│       Uso: python brain_index.py --index/--query/--daemon
│
├── 📋 requirements.txt
│   └─ Dependencias: chromadb, langchain, sentence-transformers
│
├── 📁 DECISIONS/
│   ├─ WHY_CLICKHOUSE.md (ClickHouse vs PostgreSQL trade-offs)
│   ├─ ARCHITECTURE_EVOLUTION.md (v0.7 → v0.8 timeline)
│   └─ ... (decisiones futuras)
│
├── 📁 MCP/
│   └─ CONFIG.md (Model Context Protocol configuration)
│      - docker_compose_up/down/restart
│      - validate_clickhouse_health
│      - validate_redpanda_status
│      - validate_debezium_connectors
│      - query_prometheus_metrics
│
├── 📁 golden_sets/
│   └─ Ejemplos validados de extracción (JSON)
│      Uso: ChromaDB para few-shot prompting de Vanna AI
│
├── 📁 dspy_config/
│   └─ Prompts programados (DSPy) por tipo de documento
│      * sales_metric_prompt.py
│      * customer_segment_prompt.py
│
├── 📁 vectordb/
│   └─ Almacenamiento ChromaDB (generado en primera indexación)
│      * collections/
│      * index/
│
└── 📁 workflows/
    └─ Prefect flows para auto-remediation
       * healthcheck_and_repair.py
       * validate_quality_gates.py
```

---

## 🔍 Comandos Útiles

```bash
# === Brain Index ===
python .agent/brain_index.py --index          # Indexación completa
python .agent/brain_index.py --query "..."    # Busca semántica
python .agent/brain_index.py --stats          # Ver estadísticas
python .agent/brain_index.py --daemon         # Modo automático (6h)

# === Docker Compose ===
docker-compose up -d clickhouse-server redpanda debezium-connector  # Levantar streaming stack
docker-compose logs -f redpanda                                     # Ver logs Redpanda
docker-compose ps                                                  # Ver status

# === ClickHouse ===
docker exec clickhouse-server clickhouse-client \
  --query "SELECT count() FROM aura_bronze.sales"

# === Prometheus ===
curl "http://localhost:9090/api/v1/query?query=up" | jq '.'

# === Grafana ===
# UI: http://localhost:3000 (admin/admin)

# === dbt ===
docker exec dbt-runner dbt dags               # Ver lineage DAG
docker exec dbt-runner dbt test               # Ejecutar tests
```

---

## 📊 Métricas de Salud

**El agente monitorea automáticamente:**

| Métrica | SLA | Check via |
|---------|-----|----------|
| Query latency (p95) | < 1s | Grafana → Cube.js panel |
| Cache hit rate | ≥ 95% | MCP → `validate_cube_cache` |
| CDC lag | < 5s | Redpanda Console → Consumer Group lag |
| ClickHouse health | OK | MCP → `validate_clickhouse_health` |
| Debezium Connectors | RUNNING | Admin UI → Redpanda Console |
| dbt test success | 100% | Prefect → dbt test results |

---

## 🚨 Troubleshooting

### ❌ ChromaDB connection error
```bash
# Verificar ChromaDB está accesible
python -c "import chromadb; print(chromadb.__version__)"
# Si falla: pip install --upgrade chromadb
```

### ❌ ClickHouse query slow
```bash
# Check indexación
docker exec clickhouse-server clickhouse-client \
  --query "SELECT * FROM system.tables WHERE database = 'aura_bronze' FORMAT JSON" | jq '.data | length'

# Force merge (slow pero limpia fragmentos)
docker exec clickhouse-server clickhouse-client \
  --query "OPTIMIZE TABLE aura_bronze.sales FINAL"
```

### ❌ Redpanda Admin connection error
```bash
# Verificar puerto 9644 expuesto
curl http://localhost:9644/v1/status/ready
# Si falla: docker logs redpanda y verificar SMP/Memory settings
```

### ❌ Debezium connector failed
```bash
# Check status via API
curl http://localhost:8083/connectors/aura-postgres-source/status | jq '.'
# Remediar restart: 
curl -X POST http://localhost:8083/connectors/aura-postgres-source/restart
```

### ❌ Valkey memory full
```bash
# Check memoria
docker exec valkey valkey-cli INFO memory

# Limpiar keys antiguas manually
docker exec valkey valkey-cli FLUSHDB

# O pre-configurado: MAXMEMORY-POLICY allkeys-lru
```

---

## 🎓 Próximos Pasos

### Semana 1
- [x] Setup v0.8 cognitivo (RULES, MAP, CONTEXT)
- [x] Implementar brain_index.py
- [ ] ← **TÚ ESTÁS AQUÍ**

### Semana 2
- [ ] Crear golden_sets/ con ejemplos validados
- [ ] Configurar MCP RBAC + audit logging
- [ ] Integrar ChromaDB en Vanna AI

### Semana 3
- [ ] DSPy prompts per document type
- [ ] Prefect workflows auto-remediation
- [ ] ClickHouse performance tuning

### Roadmap 2026
- Redpanda streaming (Q2): CDC lag sub-segundo (COMPLETADO ANTICIPADAMENTE)
- Sharding ClickHouse (Q2): 10x capacity
- Vertex AI predictions (Q3): AutoML

---

## 📞 Soporte

**Documentación:**
- `.agent/RULES.md` — Innegociables
- `.agent/MAP.md` — Arquitectura
- `.agent/CONTEXT.md` — Campos + validaciones
- `.agent/DECISIONS/` — Justificaciones arquitectónicas

**Debugging:**
- Logs: `docker-compose logs <service>`
- Prometheus: http://localhost:9090
- Grafana dashboards: http://localhost:3000
- Prefect UI: http://localhost:4200

**Contacto:**
- Data Engineering Team
- Slack: #data-platform
- GitHub Issues: superset-stack-docker/issues

---

**¡Agente Residente Aura v0.8 está listo para operar! 🚀**

*Última actualización: 2026-04-15*
