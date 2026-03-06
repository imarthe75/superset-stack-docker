# 🧠 Guía de Integración de Inteligencia Artificial

Este stack incluye una capa avanzada de IA para interactuar con tus datos mediante lenguaje natural.

## 🚀 Componentes de IA

| Componente | Propósito | URL |
| :--- | :--- | :--- |
| **Flowise AI** | Orquestación visual de agentes y flujos de RAG. | `http://TU_IP/flowise/` |
| **Vanna AI** | Agente especializado en generación de SQL y "Chat with Data". | `http://TU_IP/vanna/` |
| **Superset MCP** | Permite que Claude u otros agentes externos controlen Superset. | `http://TU_IP/mcp/` |

## 🚀 Starter Kit: Demo con Datos Reales

El proyecto incluye una base de datos de prueba (`sales_data`) precargada con usuarios, productos y pedidos para que puedas probar todo el stack de inmediato.

### 1. Activar la Demo
Después de levantar el stack con `docker compose up -d`, ejecuta:

```bash
# Conectar Superset a la base de datos de pruebas
python3 scripts/bootstrap_demo.py

# Entrenar a Vanna AI con el esquema de ventas
python3 vanna-ai/train_demo.py
```

### 2. Qué puedes probar:
- **Superset**: Verás una nueva base de datos "Sales Demo Database" lista para crear charts.
- **Vanna AI**: Ve a `http://localhost/vanna/ask` y pregunta: *"¿Cuál es el producto más vendido?"*.
- **Flowise**: Crea un agente que use el endpoint `/vanna/ask` para responder sobre las ventas.
- **Grafana**: Visualiza métricas de rendimiento de las consultas sobre PostgreSQL.

## 🛠️ Flujo de Trabajo Recomendado

1. **Configuración de LLM**: Asegúrate de tener una `OPENAI_API_KEY` o configurar **Ollama** en el stack para IA local.
2. **Entrenamiento de Vanna**: Envía un POST a `/vanna/train/schema` para que la IA aprenda tu estructura de base de datos.
3. **Diseño en Flowise**: Crea un flujo que utilice el nodo de **Custom Tool** para llamar a la API de Vanna o al MCP de Superset.
4. **Interacción Final**: Usa la interfaz de chat de Flowise o conecta Claude vía el MCP.

---

### Detalles Técnicos

- [Guía de Flowise](./FLOWISE.md)
- [Guía de Vanna AI](./VANNA.md)
- [Uso del MCP con Claude](../claude_setup.md)
