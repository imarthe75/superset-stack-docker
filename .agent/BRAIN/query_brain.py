#!/usr/bin/env python3
"""
query_brain.py — Helper de consulta al BRAIN (RAG) del Agente Residente
========================================================================
Uso desde línea de comandos o importado por otros módulos del agente.

    python .agent/BRAIN/query_brain.py "como funciona la replicación peerdb"
    python .agent/BRAIN/query_brain.py "que motor usa clickhouse para orders"
"""
from __future__ import annotations

import sys
from pathlib import Path

# Añadir el directorio padre al path para importar bootstrap
sys.path.insert(0, str(Path(__file__).parent))
from bootstrap import query_codebase, print_stats


def fetch_context(question: str, n_results: int = 5) -> str:
    """
    Busca contexto relevante en el índice ChromaDB del repositorio.

    Uso típico del agente antes de generar código:
        context = fetch_context("como conectar dbt a clickhouse")
        # Usar 'context' para informar la respuesta

    Args:
        question: Pregunta o descripción del contexto necesario.
        n_results: Número máximo de fragmentos relevantes.

    Returns:
        String formateado con los fragmentos más relevantes del código.
    """
    try:
        results = query_codebase(question, n_results=n_results)
        if not results:
            return f"[BRAIN] Sin resultados para: '{question}'"

        parts = [f"[BRAIN CONTEXT — '{question}']\n"]
        for i, r in enumerate(results, 1):
            score = r["relevance_score"]
            if score < 0.4:
                continue  # Ignorar resultados poco relevantes
            parts.append(
                f"## Fragmento {i} ({r['source']}) — relevancia: {score:.2f}\n"
                f"```\n{r['content'][:800]}\n```\n"
            )
        return "\n".join(parts)
    except Exception as e:
        return f"[BRAIN ERROR] {e}. Ejecutar: python bootstrap.py"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_stats()
    else:
        question = " ".join(sys.argv[1:])
        print(fetch_context(question))
