#!/usr/bin/env python3
"""
bootstrap.py — Script de Arranque del Agente Residente v0.8
=============================================================
Proyecto: Aura Intelligence Suite (superset-stack-docker)
Ubicación: .agent/BRAIN/bootstrap.py

PROPÓSITO:
    Indexa el código fuente del repositorio en ChromaDB (VectorDB local).
    El agente ejecuta este script al iniciar una sesión para cargar el
    índice semántico del proyecto completo en memoria.

FLUJO:
    1. Escanea el repo (filtra binarios, node_modules, .git, chroma_db)
    2. Divide archivos en chunks semánticos (por función/clase/bloque)
    3. Genera embeddings con OpenAI o modelo local (fallback: sentence-transformers)
    4. Almacena en ChromaDB persistente en .agent/BRAIN/chroma_db/
    5. Crea el índice de búsqueda semántica

USO:
    python .agent/BRAIN/bootstrap.py [--rebuild] [--query "como se conecta dbt"]

REQUISITOS:
    pip install langchain-community langchain-openai chromadb sentence-transformers
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# ── Dependencias ────────────────────────────────────────────────────────────
try:
    import chromadb
    from chromadb.config import Settings
    from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
    from langchain_community.document_loaders import TextLoader
    from langchain_community.vectorstores import Chroma
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Definir clase dummy para evitar NameError
    class Language:
        PYTHON = "python"
        SQL = "sql"
        MARKDOWN = "markdown"

    print("⚠️  LangChain/ChromaDB no instalados. Ejecutar: pip install -r .agent/BRAIN/requirements.txt")


try:
    from langchain_openai import OpenAIEmbeddings
    HAS_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    HAS_ST = True
except ImportError:
    HAS_ST = False

# ── Configuración ────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent  # superset/
BRAIN_DIR = Path(__file__).parent                 # .agent/BRAIN/
CHROMA_DIR = BRAIN_DIR / "chroma_db"
COLLECTION_NAME = "aura_codebase_v8"
MANIFEST_FILE = BRAIN_DIR / "index_manifest.json"

# Extensiones a indexar (código fuente únicamente)
INDEXABLE_EXTENSIONS = {
    ".py", ".sql", ".yml", ".yaml", ".json", ".md",
    ".sh", ".conf", ".xml", ".js", ".ts", ".env.example",
    ".toml", ".ini", ".dockerfile", ""
}

# Directorios a excluir
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "chroma_db", "target", "dbt_packages", "venv", ".venv",
    "postgres_data", "valkey_data", "grafana_data", "prometheus_data",
    "prefect_data", "clickhouse_data", "clickhouse_logs",
}

# Archivos a excluir
EXCLUDE_FILES = {
    ".env",  # NUNCA indexar credenciales reales
    ".DS_Store", "Thumbs.db",
}

# Archivos de agente (siempre indexar con prioridad alta)
AGENT_FILES_PRIORITY = [
    ".agent/RULES.md",
    ".agent/MAP.md",
    ".agent/AGENT.md",
    ".agent/CONTEXT.md",
    ".agent/STATE.md",
]

# Configuración de chunking por tipo de archivo
CHUNK_CONFIG: dict[str, dict[str, Any]] = {
    ".py":   {"chunk_size": 1500, "chunk_overlap": 200, "language": Language.PYTHON},
    ".sql":  {"chunk_size": 1000, "chunk_overlap": 150, "language": Language.SQL},
    ".md":   {"chunk_size": 1200, "chunk_overlap": 100, "language": Language.MARKDOWN},
    ".yml":  {"chunk_size": 800,  "chunk_overlap": 80},
    ".yaml": {"chunk_size": 800,  "chunk_overlap": 80},
    ".sh":   {"chunk_size": 800,  "chunk_overlap": 100},
    "default": {"chunk_size": 600, "chunk_overlap": 50},
}


def get_embedding_function() -> Any:
    """Selecciona la función de embeddings disponible (OpenAI > SentenceTransformers)."""
    if HAS_OPENAI:
        print("🔑 Usando OpenAI text-embedding-3-small")
        return OpenAIEmbeddings(model="text-embedding-3-small")
    elif HAS_ST:
        print("🤗 Usando SentenceTransformers (all-MiniLM-L6-v2) — modo offline")
        return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    else:
        raise RuntimeError(
            "No hay función de embeddings disponible.\n"
            "Instalar: pip install langchain-openai  (requiere OPENAI_API_KEY)\n"
            "    o:    pip install sentence-transformers"
        )


def collect_files(repo_root: Path) -> list[Path]:
    """Recolecta todos los archivos indexables del repositorio."""
    files: list[Path] = []

    for path in repo_root.rglob("*"):
        # Excluir directorios
        if any(excl in path.parts for excl in EXCLUDE_DIRS):
            continue
        # Solo archivos
        if not path.is_file():
            continue
        # Excluir por nombre
        if path.name in EXCLUDE_FILES:
            continue
        # Solo extensiones indexables
        if path.suffix.lower() not in INDEXABLE_EXTENSIONS:
            continue
        # Excluir archivo .mcp/server-config.json si tiene tokens reales
        # (verificar si contiene la palabra "token" con valor real)
        files.append(path)

    return sorted(files)


def file_hash(path: Path) -> str:
    """Hash MD5 del archivo para detección de cambios."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_manifest() -> dict[str, str]:
    """Carga el manifesto de archivos indexados (path → hash)."""
    if MANIFEST_FILE.exists():
        return json.loads(MANIFEST_FILE.read_text())
    return {}


def save_manifest(manifest: dict[str, str]) -> None:
    """Guarda el manifesto actualizado."""
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))


def get_text_splitter(ext: str) -> RecursiveCharacterTextSplitter:
    """Obtiene el splitter adecuado para el tipo de archivo."""
    config = CHUNK_CONFIG.get(ext, CHUNK_CONFIG["default"])
    language = config.get("language")

    if language:
        return RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
        )
    return RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
    )


def index_repository(rebuild: bool = False) -> chromadb.Collection:
    """
    Indexa el repositorio en ChromaDB.

    Args:
        rebuild: Si True, borra el índice existente y reconstruye desde cero.

    Returns:
        Colección ChromaDB con el índice actualizado.
    """
    if not HAS_LANGCHAIN:
        raise RuntimeError("Instalar dependencias: pip install -r .agent/BRAIN/requirements.txt")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Cliente ChromaDB persistente
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    if rebuild:
        print("🗑️  Reconstruyendo índice desde cero...")
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Aura codebase semantic index v0.8"},
    )

    embedding_fn = get_embedding_function()
    manifest = {} if rebuild else load_manifest()
    files = collect_files(REPO_ROOT)

    print(f"📁 Archivos encontrados: {len(files)}")
    indexed = 0
    skipped = 0
    errors = 0

    for file_path in files:
        rel_path = str(file_path.relative_to(REPO_ROOT))
        current_hash = file_hash(file_path)

        # Skip si no cambió (modo incremental)
        if not rebuild and manifest.get(rel_path) == current_hash:
            skipped += 1
            continue

        try:
            # Leer contenido
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue

            # Dividir en chunks
            splitter = get_text_splitter(file_path.suffix.lower())
            chunks = splitter.split_text(content)

            # Preparar documentos para ChromaDB
            doc_ids = [f"{rel_path}::chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": rel_path,
                    "file_type": file_path.suffix or "no_ext",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "is_agent_file": rel_path.startswith(".agent/"),
                }
                for i in range(len(chunks))
            ]

            # Eliminar IDs anteriores del archivo (para actualización incremental)
            existing_ids = [id for id in collection.get(where={"source": rel_path})["ids"]]
            if existing_ids:
                collection.delete(ids=existing_ids)

            # Upsert en ChromaDB
            embeddings = embedding_fn.embed_documents(chunks)
            collection.add(
                ids=doc_ids,
                documents=chunks,
                metadatas=metadatas,
                embeddings=embeddings,
            )

            manifest[rel_path] = current_hash
            indexed += 1

            if indexed % 10 == 0:
                print(f"  ✅ Indexados {indexed} archivos...")

        except Exception as e:
            print(f"  ❌ Error indexando {rel_path}: {e}")
            errors += 1

    save_manifest(manifest)

    print(f"\n📊 Resumen:")
    print(f"   Indexados: {indexed} archivos nuevos/modificados")
    print(f"   Sin cambios: {skipped} archivos")
    print(f"   Errores: {errors}")
    print(f"   Total en colección: {collection.count()} chunks")

    return collection


def query_codebase(question: str, n_results: int = 5) -> list[dict[str, Any]]:
    """
    Consulta semántica sobre el código fuente indexado.

    Args:
        question: La pregunta o contexto a buscar.
        n_results: Número de resultados a retornar.

    Returns:
        Lista de documentos relevantes con metadata.
    """
    if not CHROMA_DIR.exists():
        raise RuntimeError(
            "El índice no existe. Ejecutar: python bootstrap.py"
        )

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(COLLECTION_NAME)
    embedding_fn = get_embedding_function()

    query_embedding = embedding_fn.embed_query(question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "content": doc,
            "source": results["metadatas"][0][i]["source"],
            "relevance_score": 1 - results["distances"][0][i],
        })

    return output


def print_stats() -> None:
    """Muestra estadísticas del índice actual."""
    if not CHROMA_DIR.exists():
        print("❌ Índice no existe. Ejecutar: python bootstrap.py")
        return

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    try:
        collection = client.get_collection(COLLECTION_NAME)
        manifest = load_manifest()
        print(f"📊 Estado del índice BRAIN:")
        print(f"   Colección: {COLLECTION_NAME}")
        print(f"   Chunks total: {collection.count()}")
        print(f"   Archivos indexados: {len(manifest)}")
        print(f"   Directorio: {CHROMA_DIR}")
    except Exception:
        print("❌ No se pudo conectar a ChromaDB. El índice puede estar corrupto.")


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aura Agent BRAIN — Indexación semántica del código fuente"
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Reconstruir índice desde cero (ignora caché)"
    )
    parser.add_argument(
        "--query", type=str, default=None,
        help="Consulta semántica sobre el código indexado"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Mostrar estadísticas del índice actual"
    )
    args = parser.parse_args()

    if args.stats:
        print_stats()
    elif args.query:
        print(f"🔍 Buscando: '{args.query}'\n")
        results = query_codebase(args.query)
        for i, r in enumerate(results, 1):
            print(f"--- Resultado {i} [{r['source']}] (score: {r['relevance_score']:.3f}) ---")
            print(r["content"][:500])
            print()
    else:
        print("🚀 Iniciando indexación del repositorio Aura v0.8...")
        start = time.time()
        index_repository(rebuild=args.rebuild)
        elapsed = time.time() - start
        print(f"\n✅ Indexación completada en {elapsed:.1f}s")
        print(f"   Usar: python bootstrap.py --query 'como conectar superset a clickhouse'")
