"""
Colgate-Palmolive Colombia — Agente Conversacional
Módulo 2: Agente con memoria, enrutamiento y herramientas especializadas.
"""

# ─── Importaciones ────────────────────────────────────────────────────────────

import os
import json
import uuid
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import gradio as gr
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# ─── Configuración ────────────────────────────────────────────────────────────

KNOWLEDGE_BASE_PATH = Path("data/knowledge_base.txt")
DATOS_PATH          = Path("data/datos_estructurados.json")
MODEL_NAME          = "mistral-small-latest"

# ─── Carga de recursos ────────────────────────────────────────────────────────

def load_knowledge_base() -> str:
    if not KNOWLEDGE_BASE_PATH.exists():
        return ""
    return KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")[:80_000]

def get_logo_base64() -> str:
    path = Path("assets/logo.png")
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return ""

KNOWLEDGE = load_knowledge_base()
LOGO_B64  = get_logo_base64()

# ─── LLM y Memoria ────────────────────────────────────────────────────────────

llm = ChatMistralAI(
    model=MODEL_NAME,
    temperature=0.3,
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

memory = MemorySaver()

# ─── Herramientas ─────────────────────────────────────────────────────────────

@tool
def consultar_datos_estructurados(consulta: str) -> str:
    """Recupera datos concretos de Colgate-Palmolive Colombia desde un archivo JSON.

    USAR para:
    - Números de teléfono o líneas de atención
    - WhatsApp de contacto
    - Horarios de atención al cliente
    - Dirección o sede principal
    - NIT, nombre legal, matrícula mercantil
    - Lista de marcas comerciales en Colombia

    NO USAR para historia, productos en detalle, sostenibilidad
    o cualquier tema que requiera explicación extensa.
    """
    with open(DATOS_PATH, encoding="utf-8") as f:
        datos = json.load(f)

    q = consulta.lower()

    if any(w in q for w in ["teléfono", "telefono", "línea", "linea", "llamar", "whatsapp", "contacto", "contactar"]):
        c = datos["contacto"]
        return (
            f"Línea consumidor: {c['linea_consumidor']}\n"
            f"Línea odontólogo: {c['linea_odontologo']}\n"
            f"WhatsApp: {c['whatsapp']}\n"
            f"Sitio web: {c['sitio_web']}"
        )

    if any(w in q for w in ["horario", "hora", "atención", "atencion", "abierto", "disponible"]):
        return f"Horario de atención: {datos['horarios_atencion']['general']}"

    if any(w in q for w in ["sede", "dirección", "direccion", "ubicación", "ubicacion", "dónde", "donde", "oficina"]):
        return f"Sede principal: {datos['informacion_corporativa']['direccion']}"

    if any(w in q for w in ["nit", "nombre legal", "razón social", "razon social", "matrícula", "matricula", "registro"]):
        corp = datos["informacion_corporativa"]
        return (
            f"Nombre legal: {corp['nombre_legal']}\n"
            f"NIT: {corp['nit']}\n"
            f"Matrícula: {corp['numero_matricula']}\n"
            f"Cámara de Comercio: {corp['camara_de_comercio']}\n"
            f"Estado: {corp['estado']}"
        )

    if any(w in q for w in ["marca", "marcas", "producto", "productos", "líneas", "lineas"]):
        return "Marcas en Colombia:\n" + "\n".join(f"• {m}" for m in datos["marcas_colombia"])

    return "No encontré datos estructurados para esa consulta. Intenta preguntar por teléfono, horario, sede, NIT o marcas."


@tool
def consultar_base_conocimiento(pregunta: str) -> str:
    """Responde preguntas sobre Colgate-Palmolive usando la base documental.

    USAR para:
    - Historia y fundación de la empresa
    - Evolución de productos y marcas
    - Expansión internacional
    - Fusiones y adquisiciones
    - Programas sociales y fundación
    - Sostenibilidad y compromisos ambientales
    - Valores y cultura corporativa

    NO USAR para datos puntuales como teléfonos, horarios, NIT o direcciones.
    """
    response = llm.invoke([
        SystemMessage(content=(
            "Responde ÚNICAMENTE con información del siguiente contexto documental. "
            "Si la respuesta no está en el contexto, indícalo claramente. "
            "Responde en español formal, máximo 3 párrafos.\n\n"
            f"### CONTEXTO ###\n{KNOWLEDGE}\n### FIN DEL CONTEXTO ###"
        )),
        HumanMessage(content=pregunta),
    ])
    return response.content

# ─── Agente ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
### ROL ###
Eres el Asistente Virtual oficial de Colgate-Palmolive Colombia.
Respondes ÚNICAMENTE sobre Colgate-Palmolive Colombia.

### HERRAMIENTAS ###
Dispones de DOS herramientas. Debes elegir EXACTAMENTE UNA por turno.

1. consultar_datos_estructurados
   Para datos puntuales: teléfonos, horarios, sede, NIT, marcas.

2. consultar_base_conocimiento
   Para explicaciones: historia, productos, expansión, sostenibilidad.

### PROCESO OBLIGATORIO ###
Paso 1: Lee la pregunta.
Paso 2: Elige UNA herramienta. Solo una. Nunca ambas.
Paso 3: Ejecuta esa herramienta.
Paso 4: Redacta la respuesta con el resultado.
Paso 5: Termina. No ejecutes más herramientas.

### REGLAS ###
- Responde SIEMPRE en español formal.
- Si la pregunta es de seguimiento con contexto en el historial, responde DIRECTAMENTE sin herramientas.
- NUNCA inventes información. Si no encuentras la respuesta en las herramientas, di claramente: "No tengo información sobre ese tema en mi base de conocimiento."
- NUNCA uses ambas herramientas en el mismo turno.
- Si la pregunta no corresponde a ninguna herramienta, responde directamente sin usar ninguna.

### EJEMPLOS ###
"¿Cuál es el teléfono?" → consultar_datos_estructurados → responder → FIN
"Háblame de la historia" → consultar_base_conocimiento → responder → FIN
"¿Y el horario?" (con contexto previo) → consultar_datos_estructurados → responder → FIN
"""

tools = [consultar_datos_estructurados, consultar_base_conocimiento]

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
    checkpointer=memory,
)

# ─── Lógica del chat ──────────────────────────────────────────────────────────

def chat(mensaje: str, historial: list, thread_id: str) -> tuple[list, list]:
    if not mensaje.strip():
        return historial, historial

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 10,
    }

    try:
        resultado = agent.invoke(
            {"messages": [HumanMessage(content=mensaje)]},
            config=config,
        )

        respuesta = resultado["messages"][-1].content

        # Detectar solo la primera herramienta usada
        herramienta_usada = None
        for msg in resultado["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                herramienta_usada = msg.tool_calls[0]["name"]
                break

        if herramienta_usada:
            respuesta += f"\n\n---\n⚙ Fuente: `{herramienta_usada}`"
        else:
            respuesta += f"\n\n---\n💬 Respuesta desde historial"

    except Exception as e:
        respuesta = f"Error al procesar la consulta: {str(e)}"

    historial.append({"role": "user",      "content": mensaje})
    historial.append({"role": "assistant", "content": respuesta})
    return historial, historial


def nueva_conversacion():
    return [], [], str(uuid.uuid4())


# ─── Resumen ──────────────────────────────────────────────────────────────────

def generar_resumen(tema: str) -> str:
    if not tema.strip():
        return "Por favor escribe un tema para resumir."
    response = llm.invoke([
        SystemMessage(content=(
            "Eres un asistente experto en Colgate-Palmolive Colombia. "
            "Genera un resumen ejecutivo estructurado con: descripción general, "
            "puntos clave (máximo 5) y conclusión. Responde en español formal.\n\n"
            f"### CONTEXTO ###\n{KNOWLEDGE}\n### FIN DEL CONTEXTO ###"
        )),
        HumanMessage(content=f"Genera un resumen ejecutivo sobre: {tema}"),
    ])
    return response.content

# ─── Estilos ──────────────────────────────────────────────────────────────────

COLGATE_BLUE      = "#003DA5"
COLGATE_DARK_BLUE = "#001A4D"
COLGATE_LIGHT     = "#F0F4FF"

css = f"""
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

body, .gradio-container {{
    font-family: 'DM Sans', sans-serif !important;
    background: {COLGATE_LIGHT} !important;
}}

.gradio-container {{
    margin-left: 240px !important;
    max-width: calc(100% - 240px) !important;
}}

.sidebar {{
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 240px;
    background: {COLGATE_DARK_BLUE};
    padding: 28px 20px;
    display: flex;
    flex-direction: column;
    z-index: 1000;
    border-right: 3px solid {COLGATE_BLUE};
}}

.sidebar-title {{
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    color: #fff;
    line-height: 1.2;
    margin-bottom: 4px;
}}

.sidebar-title span {{ color: #7EB3FF; }}

.sidebar-sub {{
    font-size: 9px;
    color: rgba(255,255,255,0.35);
    letter-spacing: 3px;
    text-transform: uppercase;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 20px;
}}

.sidebar-row {{
    display: flex;
    justify-content: space-between;
    padding: 9px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}}

.sidebar-label {{
    font-size: 10px;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.sidebar-value {{
    font-size: 11px;
    color: #fff;
    font-weight: 500;
}}

.sidebar-footer {{
    margin-top: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    color: rgba(255,255,255,0.4);
}}

.dot {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 5px #22c55e;
    animation: blink 2s infinite;
}}

@keyframes blink {{
    0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }}
}}

footer {{ display: none !important; }}
"""

# ─── Sidebar HTML ─────────────────────────────────────────────────────────────

logo_tag = (
    f'<img src="data:image/png;base64,{LOGO_B64}" style="width:120px;margin-bottom:10px;">'
    if LOGO_B64 else
    '<div class="sidebar-title">Colgate-<span>Palmolive</span></div>'
)

sidebar_html = f"""
<div class="sidebar">
    {logo_tag}
    <div class="sidebar-sub">Asistente Virtual · Colombia</div>
    <div class="sidebar-row">
        <span class="sidebar-label">Modelo</span>
        <span class="sidebar-value">{MODEL_NAME}</span>
    </div>
    <div class="sidebar-row">
        <span class="sidebar-label">Módulo</span>
        <span class="sidebar-value">Taller 02 · 2026</span>
    </div>
    <div class="sidebar-row">
        <span class="sidebar-label">Contexto</span>
        <span class="sidebar-value">{len(KNOWLEDGE):,} chars</span>
    </div>
    <div class="sidebar-row">
        <span class="sidebar-label">Herramientas</span>
        <span class="sidebar-value">2 activas</span>
    </div>
    <div class="sidebar-row">
        <span class="sidebar-label">Memoria</span>
        <span class="sidebar-value">MemorySaver</span>
    </div>
    <div class="sidebar-footer">
        <div class="dot"></div> Sistema operativo
    </div>
</div>
"""

# ─── Interfaz Gradio ──────────────────────────────────────────────────────────

with gr.Blocks(title="Colgate-Palmolive · Asistente Virtual") as demo:

    gr.HTML(sidebar_html)

    with gr.Tabs():

        with gr.Tab("Chat"):
            gr.Markdown("### Agente conversacional")
            gr.Markdown("Memoria activa · Enrutamiento inteligente entre base documental y datos estructurados")

            chatbot   = gr.Chatbot(label=None, height=420)
            estado    = gr.State([])
            thread_id = gr.State(str(uuid.uuid4()))

            with gr.Row():
                inp = gr.Textbox(
                    placeholder="Escribe tu pregunta aquí...",
                    show_label=False,
                    scale=6,
                )
                btn_enviar  = gr.Button("Enviar",       variant="primary",   scale=1, min_width=90)
                btn_limpiar = gr.Button("Nueva conv.",  variant="secondary", scale=1, min_width=110)

            gr.Examples(
                examples=[
                    "¿Cuál es el teléfono de servicio al cliente?",
                    "Cuéntame la historia de Colgate-Palmolive",
                    "¿Cuáles son los horarios de atención?",
                    "¿Cuáles son las marcas en Colombia?",
                    "¿Cuál es el NIT de la empresa?",
                    "¿Dónde está la sede principal?",
                ],
                inputs=inp,
                label="Preguntas de ejemplo",
            )

            btn_enviar.click(
                chat,
                inputs=[inp, estado, thread_id],
                outputs=[chatbot, estado],
            ).then(lambda: "", outputs=inp)

            inp.submit(
                chat,
                inputs=[inp, estado, thread_id],
                outputs=[chatbot, estado],
            ).then(lambda: "", outputs=inp)

            btn_limpiar.click(
                nueva_conversacion,
                outputs=[chatbot, estado, thread_id],
            )

        with gr.Tab("Resumen"):
            gr.Markdown("### Generador de resúmenes ejecutivos")
            gr.Markdown("Escribe un tema y el asistente generará un resumen basado en la base de conocimiento.")
            inp_resumen = gr.Textbox(
                label="Tema",
                placeholder="Ej: sostenibilidad, historia, productos...",
                lines=2,
            )
            btn_resumen = gr.Button("Generar resumen", variant="primary")
            out_resumen = gr.Markdown()
            btn_resumen.click(generar_resumen, inputs=inp_resumen, outputs=out_resumen)

# ─── Lanzamiento ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"📚 Knowledge base : {len(KNOWLEDGE):,} caracteres")
    print(f"🤖 Modelo         : {MODEL_NAME}")
    print(f"🔧 Herramientas   : {[t.name for t in tools]}")
    print(f"🧠 Memoria        : MemorySaver")
    print(f"🚀 Iniciando...")
    demo.launch(
        share=True,
        css=css,
    )
