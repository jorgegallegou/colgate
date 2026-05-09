import logging
import os
import uuid
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from prompts import SYSTEM_PROMPT
from tools import TOOLS

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────────────
MODEL_NAME  = "mistral-small-latest"
TEMPERATURE = 0.3

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatMistralAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

# ── Checkpointer (memoria persistente por sesión) ──────────────────────────────
checkpointer = MemorySaver()

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

# ── Función pública ────────────────────────────────────────────────────────────
def preguntar(pregunta: str, thread_id: str) -> str:
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


def nueva_sesion() -> str:
    """Genera un nuevo UUID para iniciar una sesión limpia."""
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
