import logging
import os
import uuid
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import create_react_agent
from psycopg_pool import ConnectionPool

from prompts import SYSTEM_PROMPT
from tools import TOOLS

# Pasos del ciclo ReAct que se muestran en la UI
_Paso = dict  # {"tipo": "accion"|"observacion", ...}

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────────────
MODEL_NAME   = "mistral-small-latest"
TEMPERATURE  = 0.3
POSTGRES_URI = os.environ.get("POSTGRES_URI")

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatMistralAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

# ── Checkpointer (memoria persistente en PostgreSQL) ──────────────────────────
# ConnectionPool gestiona reconexiones automáticas si la BD cae y vuelve.
_pool = ConnectionPool(
    POSTGRES_URI,
    max_size=5,
    open=True,
    kwargs={"autocommit": True},
)
checkpointer = PostgresSaver(_pool)
checkpointer.setup()

# ── Agente LangGraph ───────────────────────────────────────────────────────────
agente = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

# Centinelas para que app_v2.py detecte el tipo de error sin acoplar strings
ERROR_GENERICO   = "__ERROR__"
ERROR_RATE_LIMIT = "__RATE_LIMIT__"


# ── Helpers internos ───────────────────────────────────────────────────────────
def _extraer_pasos(messages: list) -> list[_Paso]:
    """Extrae los pasos del ciclo ReAct (tool calls + observations) del turno actual.

    Busca el último HumanMessage y devuelve solo los pasos posteriores a él,
    evitando incluir razonamientos de turnos anteriores almacenados en MemorySaver.
    """
    # Encontrar el índice del último mensaje humano (= pregunta actual)
    last_human = -1
    for i, msg in enumerate(messages):
        if getattr(msg, "type", None) == "human" or type(msg).__name__ == "HumanMessage":
            last_human = i

    if last_human == -1:
        return []

    pasos: list[_Paso] = []
    for msg in messages[last_human + 1:]:
        # AIMessage con tool_calls → acción del agente
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                args = tc.get("args", {})
                entrada = args.get("__arg1") or args.get("input") or str(args)
                pasos.append({
                    "tipo": "accion",
                    "herramienta": tc.get("name", "desconocida"),
                    "entrada": str(entrada)[:400],
                })
        # ToolMessage → observación (resultado de la herramienta)
        elif hasattr(msg, "tool_call_id") and hasattr(msg, "content"):
            pasos.append({
                "tipo": "observacion",
                "contenido": str(msg.content)[:600],
            })
    return pasos


# ── Funciones públicas ─────────────────────────────────────────────────────────
def preguntar(pregunta: str, thread_id: str) -> str:
    """Envía una pregunta al agente y devuelve la respuesta o un centinela de error."""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        resultado = agente.invoke(
            {"messages": [{"role": "user", "content": pregunta}]},
            config=config,
        )
        return resultado["messages"][-1].content
    except Exception as e:
        logger.error("Error en agente [thread=%s]: %s", thread_id, e, exc_info=True)
        err = str(e).lower()
        if any(k in err for k in ("429", "rate", "capacity", "quota", "limit")):
            return ERROR_RATE_LIMIT
        return ERROR_GENERICO


def preguntar_con_pasos(pregunta: str, thread_id: str) -> tuple[str, list[_Paso]]:
    """Igual que preguntar(), pero también devuelve los pasos del razonamiento ReAct.

    Returns:
        (respuesta, pasos) — pasos es una lista vacía si no se usaron herramientas
        (centinela, [])    — ante cualquier error
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        resultado = agente.invoke(
            {"messages": [{"role": "user", "content": pregunta}]},
            config=config,
        )
        pasos = _extraer_pasos(resultado["messages"])
        return resultado["messages"][-1].content, pasos
    except Exception as e:
        logger.error("Error en agente [thread=%s]: %s", thread_id, e, exc_info=True)
        err = str(e).lower()
        if any(k in err for k in ("429", "rate", "capacity", "quota", "limit")):
            return ERROR_RATE_LIMIT, []
        return ERROR_GENERICO, []


def nueva_sesion() -> str:
    """Genera un UUID v4 para iniciar una sesión de conversación independiente."""
    return str(uuid.uuid4())


# ── Prueba rápida ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DEL AGENTE CONVERSACIONAL - LangGraph")
    print("=" * 60)

    session_id = nueva_sesion()
    print(f"Session ID: {session_id}\n")

    pruebas = [
        "¿Cuál es el número de teléfono de servicio al cliente?",
        "¿Cuál es la historia de Colgate-Palmolive en Colombia?",
        "¿Y cuándo llegaron al país exactamente?",
        "¿Cuál es el NIT de la empresa?",
    ]

    for i, pregunta in enumerate(pruebas, 1):
        print(f"\n{'─'*60}")
        print(f"Pregunta {i}: {pregunta}")
        print(f"{'─'*60}")
        respuesta = preguntar(pregunta, session_id)
        print(f"Respuesta: {respuesta}")

    print("\n" + "=" * 60)
    print("Prueba completada.")
