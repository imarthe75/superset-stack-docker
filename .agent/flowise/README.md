# Workflows Flowise — Aura MDS

Para interactuar con la capa semántica y la base RAG (ChromaDB), importe la siguiente topología directamente desde la interfaz gráfica de Flowise (http://localhost:3001).

## Pipeline Sugerido de Agentes

1. **Webhook / API Trigger**: Punto de entrada para el usuario de negocio.
2. **Retrieve from ChromaDB**: Nodo vector store apuntando a `/app/golden_sets` (se deben enlazar las dependencias de Embeddings locales de MiniLM).
3. **LLM Chain (Cube SQL API)**: Nodo LLM conectado a Cube.js (`http://cube:15432`) que procesa la pregunta semántica usando los ejemplos estructurados extraídos de ChromaDB.
4. **Formatter JSON**: Respuesta del agente emitiéndose estructurada.

> *Nota: Al inicializar el contenedor Docker, el sistema asume que la red `aura_internal` comunicará a Flowise directamente con Cube y Postgres.*
