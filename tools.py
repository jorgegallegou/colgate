import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import Tool

# ── Configuración ──────────────────────────────────────────────────────────────
VECTORSTORE_PATH    = Path("data/vectorstore")
STRUCTURED_PATH     = Path("data/datos_estructurados.json")
EMBEDDING_MODEL     = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RAG_TOP_K           = 4  # número de chunks a recuperar del vectorstore

# ── Carga de recursos (una sola vez al importar el módulo) ─────────────────────
print("🔧 Cargando herramientas del agente...")

_embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

_vectorstore = FAISS.load_local(
    str(VECTORSTORE_PATH),
    _embeddings,
    allow_dangerous_deserialization=True,
)

_datos_estructurados: dict = json.loads(STRUCTURED_PATH.read_text(encoding="utf-8"))

print("✓ Herramientas cargadas")

# ── Tool 1: RAG ────────────────────────────────────────────────────────────────
def buscar_en_base_documental(pregunta: str) -> str:
    """
    Busca en el vectorstore FAISS los chunks más relevantes para la pregunta.
    Devuelve el texto concatenado con su fuente, listo para que el LLM lo use.
    """
    resultados = _vectorstore.similarity_search(pregunta, k=RAG_TOP_K)

    if not resultados:
        return "No se encontró información relevante en la base documental."

    partes = []
    for r in resultados:
        titulo = r.metadata.get("titulo", "desconocido")
        url    = r.metadata.get("url", "")
        partes.append(f"[Fuente: {titulo} | {url}]\n{r.page_content}")

    return "\n\n".join(partes)


# ── Tool 2: Datos estructurados ────────────────────────────────────────────────
def buscar_en_datos_estructurados(pregunta: str) -> str:
    """
    Busca en datos_estructurados.json la respuesta a preguntas concretas.
    Usa coincidencia de palabras clave — NO usa el vectorstore.
    Devuelve la respuesta exacta preescrita o los datos crudos relevantes.
    """
    pregunta_lower = pregunta.lower()

    # 1. Buscar primero en FAQs por coincidencia de palabras clave
    faqs = _datos_estructurados.get("preguntas_frecuentes", [])
    mejor_faq = None
    mejor_score = 0

    for faq in faqs:
        palabras_pregunta = set(pregunta_lower.split())
        palabras_faq      = set(faq["pregunta"].lower().split())
        score = len(palabras_pregunta & palabras_faq)
        if score > mejor_score:
            mejor_score = score
            mejor_faq = faq

    if mejor_faq and mejor_score >= 2:
        return mejor_faq["respuesta"]

    # 2. Si no hay FAQ con suficiente score, devolver datos crudos por categoría
    if any(p in pregunta_lower for p in ["teléfono", "telefono", "llamar", "línea", "linea", "número", "numero"]):
        c = _datos_estructurados["contacto"]
        return f"Línea gratuita: {c['linea_gratuita']} | WhatsApp: {c['whatsapp']}"

    if any(p in pregunta_lower for p in ["horario", "hora", "atienden", "atención", "atencion", "abierto"]):
        h = _datos_estructurados["horarios_atencion"]
        return (
            f"Línea telefónica: {h['linea_telefonica']}\n"
            f"WhatsApp: {h['whatsapp']}\n"
            f"Chat web: {h['chat_web']}"
        )

    if any(p in pregunta_lower for p in ["nit", "registro", "matrícula", "matricula", "legal", "razón social", "razon social"]):
        ci = _datos_estructurados["informacion_corporativa"]
        return f"Nombre legal: {ci['nombre_legal']} | NIT: {ci['nit']}"

    if any(p in pregunta_lower for p in ["sede", "oficina", "dirección", "direccion", "ubicación", "ubicacion", "planta", "ciudad"]):
        sedes = _datos_estructurados["sedes_colombia"]
        return "\n".join(
            f"- {s['ciudad']}: {s['tipo']} ({s['direccion']})" for s in sedes
        )

    if any(p in pregunta_lower for p in ["marca", "producto", "línea", "linea", "vende", "comercializa"]):
        marcas = _datos_estructurados["marcas_principales_colombia"]
        return "Marcas en Colombia: " + ", ".join(marcas)

    if any(p in pregunta_lower for p in ["fundación", "fundacion", "social", "programa", "sonrisa", "parque"]):
        ps = _datos_estructurados["programas_sociales"]
        return (
            f"{ps['fundacion']} (fundada en {ps['año_creacion_fundacion']}). "
            f"{ps['programa_sonrisas_brillantes']}. "
            f"Ha donado {ps['parques_donados']}."
        )

    if any(p in pregunta_lower for p in ["sostenibilidad", "ambiente", "ambiental", "reciclable", "carbono", "verde"]):
        s = _datos_estructurados["sostenibilidad"]
        return f"{s['meta_empaques']}. {s['compromiso_ambiental']}."

    if any(p in pregunta_lower for p in ["web", "sitio", "página", "pagina", "url", "instagram", "facebook", "red social"]):
        c = _datos_estructurados["contacto"]
        rs = c["redes_sociales"]
        return (
            f"Sitio web: {c['sitio_web']}\n"
            f"Facebook: {rs['facebook']}\n"
            f"Instagram: {rs['instagram']}"
        )

    return "No encontré un dato estructurado específico para esa pregunta."


# ── Definición formal de las tools para LangChain ─────────────────────────────
tool_rag = Tool(
    name="base_documental",
    func=buscar_en_base_documental,
    description=(
        "Usa esta herramienta para responder preguntas abiertas sobre Colgate-Palmolive: "
        "su historia, valores corporativos, productos, operaciones globales, sostenibilidad, "
        "programas sociales, noticias o cualquier tema que requiera contexto narrativo. "
        "Input: la pregunta del usuario tal como fue formulada."
    ),
)

tool_estructurada = Tool(
    name="datos_estructurados",
    func=buscar_en_datos_estructurados,
    description=(
        "Usa esta herramienta para responder preguntas específicas que requieren datos concretos: "
        "número de teléfono, horarios de atención, NIT, dirección, sedes en Colombia, "
        "marcas disponibles, sitio web, redes sociales o información de contacto. "
        "NO uses esta herramienta para preguntas narrativas o de contexto general. "
        "Input: la pregunta del usuario tal como fue formulada."
    ),
)

# Lista de tools lista para pasar al AgentExecutor
TOOLS = [tool_rag, tool_estructurada]
