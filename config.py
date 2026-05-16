import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Rutas absolutas (robustas sin importar el directorio de trabajo) ───────────
_ROOT = Path(__file__).parent
DATA_DIR = _ROOT / "data"
VECTORSTORE_PATH = DATA_DIR / "vectorstore"
STRUCTURED_DATA_PATH = DATA_DIR / "datos_estructurados.json"
KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge_base.txt"
KNOWLEDGE_BASE_CLEAN_PATH = DATA_DIR / "knowledge_base_clean.txt"

# ── Embeddings y recuperación ──────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RAG_TOP_K = 4

# ── Modelo de lenguaje ─────────────────────────────────────────────────────────
MODEL_NAME = "mistral-small-latest"
TEMPERATURE = 0.3

# ── Persistencia (PostgreSQL) ──────────────────────────────────────────────────
POSTGRES_URI: str = os.getenv("POSTGRES_URI", "")
POOL_SIZE = 5

# ── Sesión de usuario ──────────────────────────────────────────────────────────
COOKIE_MAX_AGE = 2_592_000  # 30 días en segundos

# ── Centinelas de error compartidos entre agent.py y app_v2.py ────────────────
ERROR_GENERICO = "__ERROR__"
ERROR_RATE_LIMIT = "__RATE_LIMIT__"
