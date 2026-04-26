import os
import gradio as gr
from pathlib import Path
#from langchain_ollama import ChatOllama
#Alternativa de solución temporal mientras se resuelve el problema de compatibilidad con la versión más reciente de langchain
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

KNOWLEDGE_BASE_PATH = Path("data/knowledge_base.txt")
# MODEL_NAME = "gemma3:4b"
MODEL_NAME = "llama-3.3-70b-versatile"
def load_knowledge_base() -> str:
    if not KNOWLEDGE_BASE_PATH.exists():
        return ""
    text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    return text[:8_000]

KNOWLEDGE = load_knowledge_base()

SYSTEM_BASE = f"""### Rol ###
Eres un asistente virtual experto en Colgate-Palmolive Colombia.
Tu única fuente de información es el contexto que se te proporciona a continuación.

### Instrucciones ###
- Debes responder ÚNICAMENTE basándote en el contexto provisto.
- Debes usar español formal y conciso en todas tus respuestas.
- Debes indicar claramente cuando una pregunta no pueda responderse con el contexto dado.
- Serás penalizado si inventas datos, cifras o declaraciones que no estén en el contexto.
- Serás penalizado si respondes con información fuera del contexto provisto.

### Contexto de conocimiento ###
{KNOWLEDGE}

### Fin del contexto ###
"""

#llm = ChatOllama(model=MODEL_NAME, temperature=0.3)

llm = ChatGroq(model=MODEL_NAME, temperature=0.3, api_key=os.environ.get("GROQ_API_KEY"))

def invoke_llm(system_prompt: str, user_prompt: str) -> str:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return response.content

def tarea_resumen(tema: str) -> str:
    if not tema.strip():
        return "⚠ Por favor escribe un tema o área para resumir."
    prompt = f"""Con base ÚNICAMENTE en el contexto de conocimiento provisto, genera un resumen ejecutivo sobre:

TEMA: {tema}

El resumen debe incluir:
1. Descripción general
2. Puntos clave (máximo 5)
3. Conclusión breve

Si el contexto no contiene información sobre el tema, indícalo claramente."""
    return invoke_llm(SYSTEM_BASE, prompt)

def tarea_faq(area: str) -> str:
    if not area.strip():
        return "⚠ Por favor escribe un área o categoría."
    prompt = f"""Con base ÚNICAMENTE en el contexto de conocimiento provisto, genera 5 preguntas frecuentes con sus respuestas sobre:

ÁREA: {area}

Formato:
P: [pregunta]
R: [respuesta basada en el contexto]

Si el contexto no contiene información sobre el área, indícalo claramente."""
    return invoke_llm(SYSTEM_BASE, prompt)

def tarea_qa(pregunta: str, historial: list) -> tuple[list, list]:
    if not pregunta.strip():
        return historial, historial

    historial_texto = ""
    for turno in historial[-8:]:
        if turno["role"] == "user":
            historial_texto += f"Usuario: {turno['content']}\n"
        else:
            historial_texto += f"Asistente: {turno['content']}\n\n"

    prompt = f"""{historial_texto}Usuario: {pregunta}

Con base ÚNICAMENTE en el contexto provisto, responde de forma directa y precisa."""

    respuesta = invoke_llm(SYSTEM_BASE, prompt)
    historial.append({"role": "user", "content": pregunta})
    historial.append({"role": "assistant", "content": respuesta})
    return historial, historial

css = """
.gradio-container { max-width: 900px; margin: auto; }
.tab-nav button { font-weight: 600; }
"""

with gr.Blocks(title="Q&A Colgate Palmolive") as demo:

    gr.Markdown(f"""
    # Sistema Q&A — Colgate-Palmolive
    **Universidad Autónoma de Occidente · Taller 1 · Técnicas avanzadas de IA**  
    Modelo: `{MODEL_NAME}` vía Ollama · Base de conocimiento local
    """)

    if not KNOWLEDGE:
        gr.Markdown("⚠ **`knowledge_base.txt` no encontrado.** Ejecuta primero `chunking.py`.")

    with gr.Tabs():

        with gr.Tab("Resumen"):
            gr.Markdown("Genera un resumen ejecutivo sobre cualquier aspecto de Colgate-Palmolive.")
            inp_resumen = gr.Textbox(
                label="Tema",
                placeholder="Ej: estrategia de sostenibilidad, productos de higiene bucal...",
                lines=2
            )
            btn_resumen = gr.Button("Generar resumen", variant="primary")
            out_resumen = gr.Textbox(label="Resumen", lines=12)
            btn_resumen.click(tarea_resumen, inputs=inp_resumen, outputs=out_resumen)

        with gr.Tab("FAQ"):
            gr.Markdown("Genera preguntas frecuentes con respuestas sobre un área específica.")
            inp_faq = gr.Textbox(
                label="Área o categoría",
                placeholder="Ej: medio ambiente, historia de la empresa, productos para el hogar...",
                lines=2
            )
            btn_faq = gr.Button("Generar FAQ", variant="primary")
            out_faq = gr.Textbox(label="FAQ generado", lines=15)
            btn_faq.click(tarea_faq, inputs=inp_faq, outputs=out_faq)

        with gr.Tab("Q&A"):
            gr.Markdown("Conversación directa con el asistente sobre Colgate-Palmolive.")
            chatbot = gr.Chatbot(label="Conversación", height=420)
            estado = gr.State([])
            with gr.Row():
                inp_qa = gr.Textbox(
                    label="Tu pregunta",
                    placeholder="¿Cuáles son los valores corporativos de Colgate-Palmolive?",
                    scale=5
                )
                btn_qa = gr.Button("Enviar", variant="primary", scale=1)
            btn_limpiar = gr.Button("🗑 Limpiar conversación", size="sm")

            btn_qa.click(
                tarea_qa,
                inputs=[inp_qa, estado],
                outputs=[chatbot, estado]
            ).then(lambda: "", outputs=inp_qa)

            inp_qa.submit(
                tarea_qa,
                inputs=[inp_qa, estado],
                outputs=[chatbot, estado]
            ).then(lambda: "", outputs=inp_qa)

            btn_limpiar.click(lambda: ([], []), outputs=[chatbot, estado])

    gr.Markdown("---\n*Proyecto académico · Los datos provienen de fuentes públicas de Colgate-Palmolive.*")

if __name__ == "__main__":
    print(f"Knowledge base: {len(KNOWLEDGE):,} caracteres cargados")
    print(f"Modelo: {MODEL_NAME}")
    demo.launch(share=True, theme=gr.themes.Soft(primary_hue="blue"), css=css)