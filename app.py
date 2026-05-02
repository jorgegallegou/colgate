import os
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv
import base64

load_dotenv()

from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

KNOWLEDGE_BASE_PATH = Path("data/knowledge_base.txt")
MODEL_NAME = "mistral-small-latest"

def load_knowledge_base() -> str:
    if not KNOWLEDGE_BASE_PATH.exists():
        return ""
    text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    return text[:80_000]

def get_logo_base64() -> str:
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

KNOWLEDGE = load_knowledge_base()
LOGO_B64 = get_logo_base64()

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

css = f"""
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&display=swap');

* {{ font-family: 'Sora', sans-serif !important; box-sizing: border-box; }}

body, .gradio-container {{
    background: #0a0a0f !important;
    color: #e8e8f0 !important;
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
    min-width: 100% !important;
}}

/* Sidebar */
.sidebar {{
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 260px;
    background: #111118;
    border-right: 1px solid #1e1e2e;
    display: flex;
    flex-direction: column;
    padding: 28px 20px;
    z-index: 100;
}}

.sidebar-logo {{
    margin-bottom: 36px;
    padding-bottom: 24px;
    border-bottom: 1px solid #1e1e2e;
}}

.sidebar-logo img {{
    width: 160px;
}}

.sidebar-label {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    color: #444466;
    text-transform: uppercase;
    margin-bottom: 12px;
}}

.sidebar-meta {{
    margin-top: auto;
    padding-top: 20px;
    border-top: 1px solid #1e1e2e;
}}

.meta-item {{
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #444466;
    margin-bottom: 8px;
}}

.meta-value {{
    color: #6666aa;
    font-weight: 500;
}}

/* Main content */
.main-content {{
    margin-left: 280px;
    padding: 32px 40px;
    min-height: 100vh;
    width: calc(100% - 280px);
    overflow-x: hidden;
}}

/* Tabs */
.tab-nav {{
    background: transparent !important;
    border-bottom: 1px solid #1e1e2e !important;
    margin-bottom: 32px !important;
    display: flex !important;
    gap: 0 !important;
}}

.tab-nav button {{
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #444466 !important;
    padding: 12px 24px !important;
    border: none !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    margin-bottom: -1px !important;
}}

.tab-nav button.selected {{
    color: #e8e8f0 !important;
    border-bottom: 2px solid #4444ff !important;
}}

/* Inputs */
textarea, input {{
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e8e8f0 !important;
    font-size: 14px !important;
    padding: 14px !important;
    width: 100% !important;
}}

textarea:focus, input:focus {{
    border-color: #4444ff !important;
    outline: none !important;
}}

/* Labels */
.label-wrap span {{
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #444466 !important;
    background: transparent !important;
    padding: 0 !important;
    border-radius: 0 !important;
}}

/* Buttons */
button.primary {{
    background: #4444ff !important;
    color: #ffffff !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    cursor: pointer !important;
}}

button.primary:hover {{
    background: #3333ee !important;
}}

button.secondary {{
    background: transparent !important;
    border: 1px solid #1e1e2e !important;
    color: #444466 !important;
    font-size: 11px !important;
    border-radius: 8px !important;
}}

/* Markdown output */
.markdown-output {{
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    padding: 28px 32px !important;
    color: #e8e8f0 !important;
    line-height: 1.8 !important;
}}

.markdown-output h1, .markdown-output h2, .markdown-output h3 {{
    color: #ffffff !important;
    font-weight: 600 !important;
    margin-top: 24px !important;
    margin-bottom: 12px !important;
    padding-bottom: 8px !important;
    border-bottom: 1px solid #1e1e2e !important;
}}

.markdown-output ul, .markdown-output ol {{
    padding-left: 24px !important;
    margin-bottom: 16px !important;
}}

.markdown-output li {{
    margin-bottom: 8px !important;
    color: #c8c8d8 !important;
    line-height: 1.7 !important;
}}

.markdown-output p {{
    margin-bottom: 14px !important;
    color: #c8c8d8 !important;
}}

.markdown-output strong {{
    color: #ffffff !important;
    font-weight: 600 !important;
}}

.markdown-output hr {{
    border: none !important;
    border-top: 1px solid #1e1e2e !important;
    margin: 20px 0 !important;
}}

/* FAQ */
.faq-item {{
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 12px;
}}

.faq-pregunta {{
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 8px;
}}

.faq-respuesta {{
    font-size: 13px;
    color: #8888aa;
    line-height: 1.7;
}}

/* Chatbot */
.chatbot {{
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
}}

footer {{ display: none !important; }}
.tabitem {{ min-height: 600px !important; }}
.block {{ min-width: 100% !important; }}
"""

logo_html = f'<img src="data:image/png;base64,{LOGO_B64}" style="width:160px; margin-bottom:8px;">' if LOGO_B64 else "<strong>Colgate-Palmolive</strong>"

sidebar_html = f"""
<div class="sidebar">
    <div class="sidebar-logo">
        {logo_html}
        <div style="font-size:10px; color:#444466; letter-spacing:2px; text-transform:uppercase; margin-top:8px;">Knowledge Assistant</div>
    </div>
    <div class="sidebar-meta">
        <div class="meta-item">
            <span>Módulo académico</span>
            <span class="meta-value">TAAML · 2026</span>
        </div>
        <div class="meta-item">
            <span>Motor</span>
            <span class="meta-value">{MODEL_NAME}</span>
        </div>
        <div class="meta-item">
            <span>Knowledge base</span>
            <span class="meta-value">{len(KNOWLEDGE):,} chars</span>
        </div>
    </div>
</div>
"""

with gr.Blocks(title="Colgate-Palmolive AI") as demo:

    gr.HTML(sidebar_html)

    with gr.Column(elem_classes=["main-content"]):

        with gr.Tabs():

            with gr.Tab("Resumen"):
                gr.Markdown("Genera un resumen ejecutivo sobre cualquier aspecto de Colgate-Palmolive.")
                inp_resumen = gr.Textbox(
                    label="Tema",
                    placeholder="Ej: sostenibilidad, historia de la empresa, productos...",
                    lines=2
                )
                btn_resumen = gr.Button("Generar resumen", variant="primary")
                out_resumen = gr.Markdown(elem_classes=["markdown-output"])
                btn_resumen.click(tarea_resumen, inputs=inp_resumen, outputs=out_resumen)

            with gr.Tab("FAQ"):
                gr.Markdown("Preguntas frecuentes sobre Colgate-Palmolive Colombia.")
                for item in FAQ_ESTATICO:
                    gr.HTML(f"""
                    <div class="faq-item">
                        <div class="faq-pregunta">{item['pregunta']}</div>
                        <div class="faq-respuesta">{item['respuesta']}</div>
                    </div>
                    """)

            with gr.Tab("Q&A"):
                gr.Markdown("Conversación directa con el asistente sobre Colgate-Palmolive.")
                chatbot = gr.Chatbot(label=None, height=460)
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

if __name__ == "__main__":
    print(f"📚 Knowledge base: {len(KNOWLEDGE):,} caracteres cargados")
    print(f"🤖 Modelo: {MODEL_NAME}")
    demo.launch(
        share=True,
        theme=gr.themes.Base(
            primary_hue="blue",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Sora"),
        ),
        css=css
    )