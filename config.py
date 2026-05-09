from pathlib import Path

# ── Configuración compartida ───────────────────────────────────────────────────
# Archivo único de constantes para evitar duplicación entre
# build_vectorstore.py y tools.py. Cualquier cambio de modelo o ruta
# se hace aquí y se propaga automáticamente a ambos módulos.

EMBEDDING_MODEL  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTORSTORE_PATH = Path("data/vectorstore")
RAG_TOP_K        = 4
