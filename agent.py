import os
import uuid
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from tools import TOOLS

load_dotenv()

# ── Configuración ──────────────────────────────────────────────────────────────
MODEL_NAME   = "mistral-small-latest"
TEMPERATURE  = 0.3

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatMistralAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

# ── Checkpointer (memoria persistente por sesión) ──────────────────────────────
# MemorySaver guarda el estado de cada conversación en RAM indexado por thread_id.
# Cada sesión de usuario tiene su propio UUID — las memorias no se mezclan.
checkpointer = MemorySaver()

# ── System prompt del agente ───────────────────────────────────────────────────
SYSTEM_PROMPT = """### ROL ###
Eres un asistente virtual experto en Colgate-Palmolive Colombia.
Tu tarea es responder preguntas sobre la empresa usando exclusivamente la información que obtengas de tus herramientas.

### HERRAMIENTAS DISPONIBLES ###
Tienes acceso a dos herramientas:
- "base_documental": para preguntas narrativas o abiertas sobre historia, valores, productos, operaciones, sostenibilidad o programas sociales.
- "datos_estructurados": para preguntas que requieren datos concretos: teléfono, horario, NIT, dirección, sede, marca, sitio web o red social.

### CRITERIO DE SELECCIÓN ###
- Ante la duda entre las dos herramientas, prefiere "base_documental".
- Usa el historial de la conversación para responder preguntas de seguimiento.

### RESTRICCIONES ###
- Responde ÚNICAMENTE con información obtenida de tus herramientas.
- Usa siempre español formal y conciso.
- Indica claramente cuando ninguna herramienta entregue información suficiente.
- Serás penalizado si inventas datos, cifras o declaraciones.
- Serás penalizado si respondes con información fuera de lo que devuelvan las herramientas.

### EJEMPLO DE RAZONAMIENTO ###
Usuario: ¿Cuál es el horario de atención?
Thought: La pregunta pide un dato concreto, uso "datos_estructurados".
[llama a datos_estructurados]
Respuesta: El horario de atención es: línea telefónica de lunes a viernes de 8:00 AM a 6:00 PM y sábados de 8:00 AM a 1:00 PM."""

# ── Agente LangGraph ───────────────────────────────────────────────────────────
# create_react_agent de LangGraph construye un agente ReAct con:
#   - memoria persistente por sesión via checkpointer
#   - identificación de sesión via thread_id (UUID)
agente = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

# ── Función pública ────────────────────────────────────────────────────────────
def preguntar(pregunta: str, thread_id: str) -> str:
    """
    Recibe una pregunta y el UUID de la sesión.
    La memoria se gestiona automáticamente por thread_id.

    Args:
        pregunta:  texto de la pregunta del usuario
        thread_id: UUID único de la sesión (generado en app.py)

    Returns:
        respuesta final del agente como string
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        resultado = agente.invoke(
            {"messages": [{"role": "user", "content": pregunta}]},
            config=config,
        )
        # El último mensaje de la lista es la respuesta del agente
        return resultado["messages"][-1].content
    except Exception as e:
        return f"Error al procesar la pregunta: {str(e)}"


def nueva_sesion() -> str:
    """Genera un nuevo UUID para iniciar una sesión limpia."""
    return str(uuid.uuid4())


# ── Prueba rápida ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DEL AGENTE CONVERSACIONAL - LangGraph")
    print("=" * 60)

    # Una sola sesión para probar memoria entre preguntas
    session_id = nueva_sesion()
    print(f"Session ID: {session_id}\n")

    pruebas = [
        # Prueba 1: herramienta estructurada
        "¿Cuál es el número de teléfono de servicio al cliente?",
        # Prueba 2: RAG
        "¿Cuál es la historia de Colgate-Palmolive en Colombia?",
        # Prueba 3: memoria — depende de la respuesta anterior
        "¿Y cuándo llegaron al país exactamente?",
        # Prueba 4: enrutamiento — dato concreto
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
