import os
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

KNOWLEDGE_BASE_PATH = Path("data/knowledge_base.txt")
MODEL_NAME = "mistral-small-latest"

def load_knowledge_base() -> str:
    if not KNOWLEDGE_BASE_PATH.exists():
        return ""
    text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    return text[:50_000]

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

llm = ChatMistralAI(
    model=MODEL_NAME,
    temperature=0.3,
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

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

FAQ_ESTATICO = [
    {
        "pregunta": "¿Cuándo fue fundada Colgate-Palmolive?",
        "respuesta": "La empresa fue fundada en 1806 por William Colgate en Nueva York como William Colgate & Co., dedicada a la fabricación de almidón, jabones y velas."
    },
    {
        "pregunta": "¿Quién fue el fundador de Colgate-Palmolive?",
        "respuesta": "William Colgate fue el fundador. Tras su muerte en 1857, su hijo Samuel Colgate asumió la dirección y reorganizó la empresa como Colgate & Company."
    },
    {
        "pregunta": "¿En cuántos países opera Colgate-Palmolive?",
        "respuesta": "Colgate-Palmolive opera en más de 200 países y demarcaciones territoriales, siendo una de las empresas de consumo más presentes a nivel global."
    },
    {
        "pregunta": "¿Qué productos ofrece Colgate-Palmolive en Colombia?",
        "respuesta": "Ofrece productos de higiene bucal (crema dental, cepillos, hilo dental, enjuague bucal), cuidado personal (jabones, desodorantes, champús) y limpieza del hogar (Fabuloso, Suavitel, Vel Rosita)."
    },
    {
        "pregunta": "¿Cuáles son los valores corporativos de Colgate-Palmolive?",
        "respuesta": "Sus valores son: empatía, respeto y gratitud; integridad; generosidad; confianza; pertenencia e inclusión; innovación y audacia; y compromiso con la diversidad, equidad e inclusión."
    },
    {
        "pregunta": "¿Qué programas sociales tiene Colgate-Palmolive en Colombia?",
        "respuesta": "A través de la Fundación Colgate-Palmolive (creada en 1977) ha entregado 6 parques recreacionales en Cali, Popayán, Medellín, Bogotá y Cartagena, donado viviendas tras desastres naturales y establecido centros médicos y odontológicos en varias ciudades."
    },
    {
        "pregunta": "¿Cuándo llegó Colgate-Palmolive a Colombia?",
        "respuesta": "Colgate-Palmolive inició su expansión en América Latina en 1925. La Fundación Colgate-Palmolive Colombia fue creada en 1977, evidenciando una presencia consolidada en el país desde mediados del siglo XX."
    },
    {
        "pregunta": "¿Cómo puede contactar a Colgate-Palmolive en Colombia?",
        "respuesta": "A través del sitio web https://www.colgatepalmolive.com.co/contact-us, la línea gratuita 018000520800 o WhatsApp al +57 317 6405757."
    },
    {
        "pregunta": "¿Qué es la Fundación Colgate-Palmolive?",
        "respuesta": "Es una fundación creada en 1977 con misión de impulsar el desarrollo social de la comunidad colombiana, con énfasis en la niñez. Ha construido parques recreacionales, donado viviendas y establecido centros médicos y odontológicos en varias ciudades del país."
    },
    {
        "pregunta": "¿Cuál es el compromiso de Colgate-Palmolive con la sostenibilidad?",
        "respuesta": "La empresa está comprometida con preservar el medio ambiente, ha sido reconocida como una de las Compañías más Éticas del Mundo y obtuvo 100 puntos en el Índice de Equidad Corporativa. También busca que el 100% de sus empaques plásticos sean reciclables."
    },
]

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
.gradio-container { max-width: 820px; min-width: 820px; margin: auto; }
.tab-nav { justify-content: center !important; display: flex !important; }
.tab-nav button { text-transform: uppercase; letter-spacing: 1.5px; font-size: 13px; }
.tab-nav button.selected { border-bottom: 2px solid white; }
.label-wrap span { background: transparent !important; color: #888 !important; font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
footer { display: none !important; }
.block { min-width: 100% !important; }
.tabitem { min-height: 600px !important; }
"""

with gr.Blocks(title="Sistema Q&A Colgate Palmolive") as demo:

    gr.Markdown(f"""
# Sistema Q&A Colgate Palmolive
**Universidad Autónoma de Occidente · Taller 1 · Técnicas avanzadas de IA**  
Modelo: `{MODEL_NAME}`  
Vía Mistral AI · Base de conocimiento local
    """)

    if not KNOWLEDGE:
        gr.Markdown("⚠ **`knowledge_base.txt` no encontrado.** Ejecuta primero `chunking.py`.")

    with gr.Tabs():

        with gr.Tab("RESUMEN"):
            gr.Markdown("Genera un resumen ejecutivo sobre cualquier aspecto de Colgate-Palmolive.")
            inp_resumen = gr.Textbox(
                label="Tema",
                placeholder="Ej: estrategia de sostenibilidad, productos de higiene bucal...",
                lines=2
            )
            btn_resumen = gr.Button("Generar resumen", variant="primary")
            out_resumen = gr.Textbox(label="Resultado", lines=12)
            btn_resumen.click(tarea_resumen, inputs=inp_resumen, outputs=out_resumen)

        with gr.Tab("FAQ"):
            gr.Markdown("Preguntas frecuentes sobre Colgate-Palmolive Colombia.")
            for item in FAQ_ESTATICO:
                gr.Markdown(f"**{item['pregunta']}**")
                gr.Markdown(f"{item['respuesta']}")
                gr.Markdown("---")

        with gr.Tab("Q&A"):
            gr.Markdown("Conversación directa con el asistente sobre Colgate-Palmolive.")
            chatbot = gr.Chatbot(label=None, height=420)
            estado = gr.State([])
            with gr.Row():
                inp_qa = gr.Textbox(
                    label=None,
                    placeholder="Escribe tu pregunta aquí...",
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

    gr.Markdown("""
---
*Proyecto académico · Los datos provienen de fuentes públicas de Colgate-Palmolive.*

*Autores: Natalia Arias · Jorge Castaño · Jhonathan Clavijo · Jorge Gallego*
    """)

if __name__ == "__main__":
    print(f"Knowledge base: {len(KNOWLEDGE):,} caracteres cargados")
    print(f"Modelo: {MODEL_NAME}")
    demo.launch(
        share=True,
        theme=gr.themes.Base(
            primary_hue="blue",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("DM Sans"),
            font_mono=gr.themes.GoogleFont("DM Mono"),
        ),
        css=css
    )