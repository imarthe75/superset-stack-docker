# Ejemplos de Uso: Componentes de Inteligencia Artificial
# Ecosistema: Aura v8.3

Esta guía proporciona ejemplos prácticos para manipular los componentes de IA del proyecto.

---

## 1. Vanna AI (Text-to-SQL)

**Funcionalidad:** Traduce preguntas humanas a consultas SQL que Cube.js entiende.

### Cómo manipular (Entrenamiento):
Para que Vanna sea preciso, debes alimentarlo con ejemplos de "verdad conocida" (Golden Sets).
1. Accede a `http://<IP>/vanna/` (si hay UI habilitada) o usa el endpoint de entrenamiento.
2. Ejemplo de comando para entrenar via API (interno):
   ```bash
   curl -X POST http://vanna-ai:8011/train \
        -d '{"question": "¿Cuál es el producto más vendido este mes?", "sql": "SELECT product_name, sum(amount) FROM Sales GROUP BY 1 ORDER BY 2 DESC LIMIT 1"}'
   ```

### Ejemplo de uso:
- **Usuario pregunta:** "¿Qué categorías de productos tienen un margen mayor al 20%?"
- **Resultado:** Vanna genera el SQL, consulta a Cube y devuelve una tabla/gráfico en Superset.

---

## 2. Flowise (AI Orchestration)

**Funcionalidad:** Permite crear flujos complejos combinando LLMs, bases de datos vectoriales y herramientas.

### Cómo manipular:
1. Accede a `http://<IP>/flowise/`.
2. **Crear un "Chatflow":** Arrastra un nodo de "ChatOpenAI", conéctalo a un "Buffer Memory" y a una "Vector Database" (ChromaDB).

### Ejemplo Útil: "Asistente de Gobernanza"
- **Configuración:** Conecta Flowise a la API de **OpenMetadata**.
- **Acción:** El usuario pregunta "¿Quién es el dueño de la tabla `fct_sales`?".
- **Resultado:** El chatbot consulta el catálogo y responde: "El dueño es el equipo de Data Engineering (@data_team)".

---

## 3. Superset MCP (Agentic Bio)

**Funcionalidad:** Permite que agentes externos (como yo, o Claude/GPT) realicen acciones en el stack.

### Cómo manipular:
- No se recomienda manipular el código de `superset-mcp` a menos que se quiera añadir una nueva "Tool".
- Las herramientas están en `superset-mcp/main.py`.

### Ejemplo de funcionalidad:
- Un agente puede ejecutar `list_dashboards` o `get_database_schema` para entender el contexto antes de proponer un cambio.

---

## 4. Recomendaciones de "No Tocar"

- **Temporal Server:** No manipular. Gestión automática de flujos de trabajo de larga duración para el CDC.
- **OpenSearch:** No manipular índices manualmente. OpenMetadata los sincroniza automáticamente.
- **Valkey (Data):** No manipular las llaves directamente. Se usa como buffer temporal de alta velocidad.
