#!/usr/bin/env python3
"""
brain_index.py — Agente Residente Aura: Indexación de Memoria Interna (v8.0 LITE)

Versión simplificada sin dependencias pesadas (ChromaDB optional):
- Indexación de archivos en JSON (local filesystem)
- Búsqueda usando regex + similitud de strings
- Serialización simple con pickle/json

Propósito:
  Indexar dinámicamente archivos de configuración, modelos dbt, y golden sets
  para que el agente pueda comparar resultados de extracción.

Flujo:
  1. Leer archivos de configuración (superset_config.py, cube schemas)
  2. Leer modelos dbt (YAML + SQL)
  3. Leer ejemplos de golden sets (JSON)
  4. Indexar en storage local (JSON)
  5. Exponer API REST para queries semánticas

Uso:
  python3 .agent/brain_index.py --index    # Indexar todo
  python3 .agent/brain_index.py --query "..." # Query
  python3 .agent/brain_index.py --daemon   # Cron cada 6h
  python3 .agent/brain_index.py --stats    # Ver estadísticas
"""

import os
import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime, timedelta
import logging
from difflib import SequenceMatcher

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
AGENT_DIR = Path(__file__).parent
VECTORDB_DIR = AGENT_DIR / "vectordb"
GOLDEN_SETS_DIR = AGENT_DIR / "golden_sets"
SUPERSET_CONFIG = Path(__file__).parent.parent / "superset_config.py"
CUBE_SCHEMAS = Path(__file__).parent.parent / "cube_schema"
DBT_PROJECT = Path(__file__).parent.parent / "dbt_aura"
INDEX_FILE = VECTORDB_DIR / "index.json"

VECTORDB_DIR.mkdir(exist_ok=True)


class AuraBrainIndexLite:
    """Indexador de memoria simplificado para Agente Residente Aura (sin ChromaDB)"""

    def __init__(self):
        """Inicializar storage local"""
        self.index: Dict[str, List[Dict[str, Any]]] = {
            "documents": [],
            "metadata": {
                "version": "8.0-lite",
                "indexed_at": "",
                "total_chunks": 0
            }
        }
        self.load_index()
        logger.info("✅ AuraBrainIndexLite initialized")

    def load_index(self):
        """Cargar índice desde JSON si existe"""
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, 'r') as f:
                    self.index = json.load(f)
                logger.info(f"📖 Loaded index: {self.index['metadata']['total_chunks']} chunks")
            except Exception as e:
                logger.warning(f"⚠️ Could not load index: {e}, starting fresh")
                self.index = {"documents": [], "metadata": {"version": "8.0-lite", "indexed_at": "", "total_chunks": 0}}

    def save_index(self):
        """Guardar índice a JSON"""
        self.index['metadata']['indexed_at'] = datetime.now().isoformat()
        self.index['metadata']['total_chunks'] = len(self.index['documents'])
        
        with open(INDEX_FILE, 'w') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Index saved: {len(self.index['documents'])} chunks")

    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Dividir texto en chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    def index_file(self, file_path: Path, source_type: str) -> int:
        """Indexar archivo individual"""
        if not file_path.exists():
            logger.warning(f"⚠️ {file_path} does not exist, skipping")
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"❌ Error reading {file_path}: {e}")
            return 0

        chunks = self.split_text(content)
        for i, chunk in enumerate(chunks):
            doc = {
                "id": f"{source_type}_{file_path.stem}_{i:03d}",
                "content": chunk,
                "source": str(file_path.relative_to(AGENT_DIR.parent)),
                "type": source_type,
                "chunk_index": i,
                "hash": hashlib.md5(chunk.encode()).hexdigest()[:8]
            }
            self.index["documents"].append(doc)

        logger.info(f"✅ Indexed {len(chunks)} chunks from {file_path.name}")
        return len(chunks)

    def index_superset_config(self) -> int:
        """Indexar superset_config.py"""
        return self.index_file(SUPERSET_CONFIG, "superset_config")

    def index_cube_schemas(self) -> int:
        """Indexar esquemas de Cube.js"""
        total = 0
        if CUBE_SCHEMAS.exists():
            for schema_file in CUBE_SCHEMAS.glob("*.js"):
                total += self.index_file(schema_file, "cube_schema")
        return total

    def index_dbt_models(self) -> int:
        """Indexar modelos dbt (SQL + YAML)"""
        total = 0
        if not DBT_PROJECT.exists():
            logger.warning(f"⚠️ {DBT_PROJECT} no existe, skipping")
            return total

        # SQL models
        for sql_file in DBT_PROJECT.glob("models/**/*.sql"):
            total += self.index_file(sql_file, "dbt_model")

        # YAML models
        for yaml_file in DBT_PROJECT.glob("models/**/*.yml"):
            total += self.index_file(yaml_file, "dbt_config")

        return total

    def index_golden_sets(self) -> int:
        """Indexar golden sets"""
        total = 0
        if GOLDEN_SETS_DIR.exists():
            for json_file in GOLDEN_SETS_DIR.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        golden_set = json.load(f)
                    text_content = json.dumps(golden_set, indent=2, ensure_ascii=False)
                    chunks = self.split_text(text_content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "id": f"golden_{json_file.stem}_{i:03d}",
                            "content": chunk,
                            "source": f"golden_sets/{json_file.name}",
                            "type": "golden_set",
                            "chunk_index": i,
                            "hash": hashlib.md5(chunk.encode()).hexdigest()[:8]
                        }
                        self.index["documents"].append(doc)
                    
                    logger.info(f"✅ Indexed {len(chunks)} chunks from golden set: {json_file.name}")
                    total += len(chunks)
                except Exception as e:
                    logger.error(f"❌ Error indexing golden set {json_file}: {e}")

        return total

    def full_index(self) -> Dict[str, int]:
        """Ejecutar indexación completa"""
        logger.info("🚀 Starting full indexation...")
        
        # Limpiar índice anterior
        self.index["documents"] = []
        
        counts = {
            "superset_config": self.index_superset_config(),
            "cube_schemas": self.index_cube_schemas(),
            "dbt_models": self.index_dbt_models(),
            "golden_sets": self.index_golden_sets(),
        }

        total = sum(counts.values())
        self.save_index()
        
        logger.info(f"✅ Indexation complete! Total chunks: {total}")
        logger.info(f"   - Superset config: {counts['superset_config']}")
        logger.info(f"   - Cube schemas: {counts['cube_schemas']}")
        logger.info(f"   - dbt models: {counts['dbt_models']}")
        logger.info(f"   - Golden sets: {counts['golden_sets']}")

        return counts

    def similarity_score(self, text1: str, text2: str) -> float:
        """Calcular similitud entre dos textos"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def query(self, question: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Buscar documentos similares a la pregunta"""
        if not self.index["documents"]:
            logger.warning("⚠️ Index is empty, run --index first")
            return []

        # Calcular similitud con cada documento
        scored_docs = []
        for doc in self.index["documents"]:
            score = self.similarity_score(question, doc['content'][:200])
            scored_docs.append((score, doc))

        # Ordenar y retornar top N
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for i, (score, doc) in enumerate(scored_docs[:n_results]):
            results.append({
                "rank": i + 1,
                "content": doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content'],
                "source": doc['source'],
                "type": doc['type'],
                "similarity": round(score, 3),
                "id": doc['id']
            })

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Agente Residente Aura — Brain Index Manager (Lite)"
    )
    parser.add_argument('--index', action='store_true', help='Run full indexation')
    parser.add_argument('--query', type=str, help='Semantic query')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon: re-index every 6 hours')
    parser.add_argument('--stats', action='store_true', help='Show collection statistics')

    args = parser.parse_args()

    brain = AuraBrainIndexLite()

    if args.index:
        brain.full_index()

    elif args.query:
        logger.info(f"🔍 Querying: {args.query}")
        results = brain.query(args.query)
        if results:
            for result in results:
                print(f"\n[{result['rank']}] {result['source']} ({result['type']}) — Similitud: {result['similarity']}")
                print(f"    Content: {result['content']}")
        else:
            print("❌ No results found")

    elif args.daemon:
        import time
        interval_seconds = 6 * 3600  # 6 hours
        logger.info(f"🔁 Running daemon mode (re-index every {interval_seconds // 3600}h)")
        try:
            while True:
                brain.full_index()
                logger.info(f"⏰ Next index in {interval_seconds // 3600}h...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("🛑 Daemon stopped")

    elif args.stats:
        count = len(brain.index.get("documents", []))
        logger.info(f"📊 Collection stats:")
        logger.info(f"   - Total documents: {count}")
        logger.info(f"   - Indexed at: {brain.index['metadata'].get('indexed_at', 'never')}")
        logger.info(f"   - Version: {brain.index['metadata'].get('version', 'unknown')}")
        logger.info(f"   - Storage: {INDEX_FILE}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()


# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
AGENT_DIR = Path(__file__).parent
VECTORDB_DIR = AGENT_DIR / "vectordb"
GOLDEN_SETS_DIR = AGENT_DIR / "golden_sets"
SUPERSET_CONFIG = Path(__file__).parent.parent / "superset_config.py"
CUBE_SCHEMAS = Path(__file__).parent.parent / "cube_schema"
DBT_PROJECT = Path(__file__).parent.parent / "dbt_aura"

VECTORDB_DIR.mkdir(exist_ok=True)


class AuraBrainIndex:
    """Indexador de memoria para Agente Residente Aura"""

    def __init__(self):
        """Inicializar ChromaDB y embedding model"""
        # ChromaDB client (persistent)
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(VECTORDB_DIR),
            anonymized_telemetry=False,
        )
        self.client = chromadb.Client(settings)
        
        # Embedding model (HuggingFace, local, sin API key)
        # Modelo ligero: sentence-transformers/all-MiniLM-L6-v2 (22MB)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Collection (crear si no existe)
        self.collection = self.client.get_or_create_collection(
            name="aura_config_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
        logger.info("✅ AuraBrainIndex initialized")

    def index_superset_config(self) -> int:
        """Indexar superset_config.py"""
        if not SUPERSET_CONFIG.exists():
            logger.warning(f"⚠️ {SUPERSET_CONFIG} no existe, skipping")
            return 0
        
        with open(SUPERSET_CONFIG, 'r') as f:
            content = f.read()
        
        chunks = self.splitter.split_text(content)
        metadatas = [
            {
                "source": "superset_config.py",
                "type": "config",
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        ids = [
            f"superset_config_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
            for chunk in chunks
        ]
        
        self.collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas
        )
        logger.info(f"✅ Indexed {len(chunks)} chunks from superset_config.py")
        return len(chunks)

    def index_cube_schemas(self) -> int:
        """Indexar esquemas de Cube.js"""
        if not CUBE_SCHEMAS.exists():
            logger.warning(f"⚠️ {CUBE_SCHEMAS} no existe, skipping")
            return 0
        
        total = 0
        for schema_file in CUBE_SCHEMAS.glob("*.js"):
            with open(schema_file, 'r') as f:
                content = f.read()
            
            chunks = self.splitter.split_text(content)
            metadatas = [
                {
                    "source": f"cube_schema/{schema_file.name}",
                    "type": "cube_schema",
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            ids = [
                f"cube_{schema_file.stem}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                for chunk in chunks
            ]
            
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            total += len(chunks)
        
        logger.info(f"✅ Indexed {total} chunks from Cube schemas")
        return total

    def index_dbt_models(self) -> int:
        """Indexar modelos dbt (SQL + YAML)"""
        if not DBT_PROJECT.exists():
            logger.warning(f"⚠️ {DBT_PROJECT} no existe, skipping")
            return 0
        
        total = 0
        
        # SQL models
        for sql_file in DBT_PROJECT.glob("models/**/*.sql"):
            with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            chunks = self.splitter.split_text(content)
            rel_path = sql_file.relative_to(DBT_PROJECT)
            
            metadatas = [
                {
                    "source": f"dbt_model/{rel_path}",
                    "type": "dbt_model",
                    "layer": str(rel_path).split('/')[1],  # staging, marts, etc
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            ids = [
                f"dbt_{sql_file.stem}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                for chunk in chunks
            ]
            
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            total += len(chunks)
        
        # YAML (sources, properties)
        for yaml_file in DBT_PROJECT.glob("models/**/*.yml"):
            with open(yaml_file, 'r') as f:
                content = f.read()
            
            chunks = self.splitter.split_text(content)
            rel_path = yaml_file.relative_to(DBT_PROJECT)
            
            metadatas = [
                {
                    "source": f"dbt_config/{rel_path}",
                    "type": "dbt_config",
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            ids = [
                f"dbt_yaml_{yaml_file.stem}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                for chunk in chunks
            ]
            
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            total += len(chunks)
        
        logger.info(f"✅ Indexed {total} chunks from dbt models")
        return total

    def index_golden_sets(self) -> int:
        """Indexar golden sets para validación de extracciones"""
        if not GOLDEN_SETS_DIR.exists():
            logger.warning(f"⚠️ {GOLDEN_SETS_DIR} no existe, skipping")
            return 0
        
        total = 0
        for json_file in GOLDEN_SETS_DIR.glob("*.json"):
            with open(json_file, 'r') as f:
                golden_set = json.load(f)
            
            # Convertir a texto para embedding
            text_content = json.dumps(golden_set, indent=2, ensure_ascii=False)
            chunks = self.splitter.split_text(text_content)
            
            metadatas = [
                {
                    "source": f"golden_set/{json_file.name}",
                    "type": "golden_set",
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            ids = [
                f"golden_{json_file.stem}_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
                for chunk in chunks
            ]
            
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            total += len(chunks)
        
        logger.info(f"✅ Indexed {total} chunks from golden sets")
        return total

    def full_index(self) -> Dict[str, int]:
        """Ejecutar indexación completa"""
        logger.info("🚀 Starting full indexation...")
        
        counts = {
            "superset_config": self.index_superset_config(),
            "cube_schemas": self.index_cube_schemas(),
            "dbt_models": self.index_dbt_models(),
            "golden_sets": self.index_golden_sets(),
        }
        
        total = sum(counts.values())
        logger.info(f"✅ Indexation complete! Total chunks: {total}")
        logger.info(f"   - Superset config: {counts['superset_config']}")
        logger.info(f"   - Cube schemas: {counts['cube_schemas']}")
        logger.info(f"   - dbt models: {counts['dbt_models']}")
        logger.info(f"   - Golden sets: {counts['golden_sets']}")
        
        return counts

    def query(self, question: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Buscar semánticamente en la base de conocimiento"""
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        
        if not results['documents']:
            return []
        
        # Formatear resultados
        formatted = []
        for i, doc in enumerate(results['documents'][0]):
            formatted.append({
                "rank": i + 1,
                "content": doc,
                "source": results['metadatas'][0][i]['source'],
                "type": results['metadatas'][0][i]['type'],
                "distance": results['distances'][0][i]  # cosine distance
            })
        
        return formatted


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Agente Residente Aura — Brain Index Manager"
    )
    parser.add_argument(
        '--index',
        action='store_true',
        help='Run full indexation'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Semantic query (example: "¿qué tabla contiene ventas?")'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon: re-index every 6 hours'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show collection statistics'
    )
    
    args = parser.parse_args()
    
    brain = AuraBrainIndex()
    
    if args.index:
        brain.full_index()
    
    elif args.query:
        logger.info(f"🔍 Querying: {args.query}")
        results = brain.query(args.query)
        if results:
            for result in results:
                print(f"\n[{result['rank']}] {result['source']} ({result['type']})")
                print(f"    Content: {result['content'][:200]}...")
        else:
            print("❌ No results found")
    
    elif args.daemon:
        import time
        interval_seconds = 6 * 3600  # 6 hours
        logger.info(f"🔁 Running daemon mode (re-index every {interval_seconds // 3600}h)")
        try:
            while True:
                brain.full_index()
                logger.info(f"⏰ Next index in {interval_seconds // 3600}h...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("🛑 Daemon stopped")
    
    elif args.stats:
        count = brain.collection.count()
        logger.info(f"📊 Collection stats:")
        logger.info(f"   - Total documents: {count}")
        logger.info(f"   - Embedding model: all-MiniLM-L6-v2")
        logger.info(f"   - Distance metric: cosine")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
