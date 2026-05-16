import json
import logging
import os
import unicodedata
import warnings

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
warnings.filterwarnings("ignore", message=".*Accessing.*__path__.*")

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.tools import tool

from config import EMBEDDING_MODEL, VECTORSTORE_PATH, RAG_TOP_K, STRUCTURED_DATA_PATH

logging.getLogger("transformers").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

try:
    import streamlit as st
    _cache = st.cache_resource
except ImportError:
    def _cache(fn):
        return fn

# ── Utilidades ─────────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    """Elimina tildes y pasa a minúsculas para matching robusto."""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()

_STOPWORDS = frozenset({
    "cual", "es", "el", "la", "de", "en", "un", "una", "los", "las",
    "del", "al", "y", "o", "que", "con", "por", "su", "se", "cuales",
})

# ── Carga de recursos con caché de Streamlit ───────────────────────────────────

@_cache
def _cargar_recursos():
    """Carga embeddings, vectorstore FAISS y JSON estructurado una sola vez."""
    logger.info("Cargando recursos del agente...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_PATH),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    datos = json.loads(STRUCTURED_DATA_PATH.read_text(encoding="utf-8"))
    logger.info("Recursos cargados: %d vectores en el índice FAISS", vectorstore.index.ntotal)
    return embeddings, vectorstore, datos


_embeddings, _vectorstore, _datos_estructurados = _cargar_recursos()


# ── Tool 1: RAG Chain de 2 pasos ───────────────────────────────────────────────

@tool(response_format="content_and_artifact")
def retrieve_context(pregunta: str):
    """Usa esta herramienta para responder preguntas abiertas sobre Colgate-Palmolive:
    su historia, valores corporativos, productos, operaciones globales, sostenibilidad,
    programas sociales, noticias o cualquier tema que requiera contexto narrativo.

    Implementa RAG Chain de 2 pasos:
    - Paso 1 (Retrieve): busca en FAISS los chunks más similares semánticamente.
    - Paso 2 (Generate): formatea Source + Content para que el modelo genere la respuesta.

    Input: la pregunta del usuario tal como fue formulada.
    """
    retrieved_docs = _vectorstore.similarity_search(pregunta, k=RAG_TOP_K)
    if not retrieved_docs:
        return "No se encontró información relevante en la base documental.", []

    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


# ── Tool 2: Datos estructurados ────────────────────────────────────────────────

def buscar_en_datos_estructurados(pregunta: str) -> str:
    """Lógica pura de búsqueda estructurada (sin decorador @tool, testeable de forma aislada).

    Estrategia por capas:
    1. Detección de intención por palabras clave (mayor precisión).
    2. Solapamiento de palabras con FAQs como fallback.
    3. Mensaje de no encontrado.
    """
    q = _normalizar(pregunta)

    if any(p in q for p in ["horario", "hora", "atienden", "abierto", "cuando abren"]):
        h = _datos_estructurados["horarios_atencion"]
        return (
            f"Línea telefónica: {h['linea_telefonica']}\n"
            f"WhatsApp: {h['whatsapp']}\n"
            f"Chat web: {h['chat_web']}"
        )

    if any(p in q for p in ["nit", "registro", "razon social", "nombre legal"]):
        ci = _datos_estructurados["informacion_corporativa"]
        return f"Nombre legal: {ci['nombre_legal']} | NIT: {ci['nit']}"

    if any(p in q for p in ["sede", "oficina", "direccion", "ubicacion", "planta", "ciudad"]):
        sedes = _datos_estructurados["sedes_colombia"]
        return "\n".join(
            f"- {s['ciudad']}: {s['tipo']} ({s['direccion']})" for s in sedes
        )

    if any(p in q for p in ["marca", "producto", "vende", "comercializa", "catalogo"]):
        marcas = _datos_estructurados["marcas_principales_colombia"]
        return "Marcas en Colombia: " + ", ".join(marcas)

    if any(p in q for p in ["fundacion", "programa social", "sonrisa", "parque", "comunidad"]):
        ps = _datos_estructurados["programas_sociales"]
        return (
            f"{ps['fundacion']} (fundada en {ps['año_creacion_fundacion']}). "
            f"{ps['programa_sonrisas_brillantes']}. "
            f"Ha donado {ps['parques_donados']}."
        )

    if any(p in q for p in ["sostenibilidad", "ambiente", "ambiental", "reciclable", "carbono", "ecologico"]):
        s = _datos_estructurados["sostenibilidad"]
        return f"{s['meta_empaques']}. {s['compromiso_ambiental']}."

    if any(p in q for p in ["web", "sitio", "pagina", "instagram", "facebook", "red social", "redes sociales", "internet"]):
        c = _datos_estructurados["contacto"]
        rs = c["redes_sociales"]
        return (
            f"Sitio web: {c['sitio_web']}\n"
            f"Facebook: {rs['facebook']}\n"
            f"Instagram: {rs['instagram']}"
        )

    if any(p in q for p in ["correo", "email", "mail"]):
        c = _datos_estructurados["contacto"]
        return f"Correo electrónico: {c['correo_consumidor']}"

    if any(p in q for p in ["telefono", "llamar", "linea", "numero", "contacto", "comunicar", "atencion"]):
        c = _datos_estructurados["contacto"]
        return f"Línea gratuita: {c['linea_gratuita']} | WhatsApp: {c['whatsapp']}"

    # Fallback: solapamiento con FAQs
    faqs = _datos_estructurados.get("preguntas_frecuentes", [])
    mejor_faq = None
    mejor_score = 0
    for faq in faqs:
        palabras_q = set(_normalizar(pregunta).split()) - _STOPWORDS
        palabras_faq = set(_normalizar(faq["pregunta"]).split()) - _STOPWORDS
        score = len(palabras_q & palabras_faq)
        if score > mejor_score:
            mejor_score = score
            mejor_faq = faq
    if mejor_faq and mejor_score >= 2:
        return mejor_faq["respuesta"]

    return "No encontré un dato estructurado específico para esa pregunta."


@tool
def datos_estructurados(pregunta: str) -> str:
    """Usa esta herramienta para responder preguntas específicas que requieren datos concretos:
    número de teléfono, horarios de atención, NIT, dirección, sedes en Colombia,
    marcas disponibles, sitio web, redes sociales o información de contacto.

    No usa vectorstore: la recuperación es determinista y siempre precisa.
    NO uses esta herramienta para preguntas narrativas o de contexto general.

    Input: la pregunta del usuario tal como fue formulada.
    """
    return buscar_en_datos_estructurados(pregunta)


# ── Lista de herramientas para el agente ───────────────────────────────────────
TOOLS = [retrieve_context, datos_estructurados]
