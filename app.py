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
    {"pregunta": "¿Cuándo fue fundada Colgate-Palmolive?", "respuesta": "La empresa fue fundada en 1806 por William Colgate en Nueva York como William Colgate & Co., dedicada a la fabricación de almidón, jabones y velas."},
    {"pregunta": "¿Quién fue el fundador de Colgate-Palmolive?", "respuesta": "William Colgate fue el fundador. Tras su muerte en 1857, su hijo Samuel Colgate asumió la dirección y reorganizó la empresa como Colgate & Company."},
    {"pregunta": "¿En cuántos países opera Colgate-Palmolive?", "respuesta": "Colgate-Palmolive opera en más de 200 países y demarcaciones territoriales, siendo una de las empresas de consumo más presentes a nivel global."},
    {"pregunta": "¿Qué productos ofrece Colgate-Palmolive en Colombia?", "respuesta": "Ofrece productos de higiene bucal (crema dental, cepillos, hilo dental, enjuague bucal), cuidado personal (jabones, desodorantes, champús) y limpieza del hogar (Fabuloso, Suavitel, Vel Rosita)."},
    {"pregunta": "¿Cuáles son los valores corporativos de Colgate-Palmolive?", "respuesta": "Sus valores son: empatía, respeto y gratitud; integridad; generosidad; confianza; pertenencia e inclusión; innovación y audacia; y compromiso con la diversidad, equidad e inclusión."},
    {"pregunta": "¿Qué programas sociales tiene Colgate-Palmolive en Colombia?", "respuesta": "A través de la Fundación Colgate-Palmolive (creada en 1977) ha entregado 6 parques recreacionales en Cali, Popayán, Medellín, Bogotá y Cartagena, donado viviendas tras desastres naturales y establecido centros médicos y odontológicos en varias ciudades."},
    {"pregunta": "¿Cuándo llegó Colgate-Palmolive a Colombia?", "respuesta": "Colgate-Palmolive inició su expansión en América Latina en 1925. La Fundación Colgate-Palmolive Colombia fue creada en 1977, evidenciando una presencia consolidada en el país desde mediados del siglo XX."},
    {"pregunta": "¿Cómo puede contactar a Colgate-Palmolive en Colombia?", "respuesta": "A través del sitio web https://www.colgatepalmolive.com.co/contact-us, la línea gratuita 018000520800 o WhatsApp al +57 317 6405757."},
    {"pregunta": "¿Qué es la Fundación Colgate-Palmolive?", "respuesta": "Es una fundación creada en 1977 con misión de impulsar el desarrollo social de la comunidad colombiana, con énfasis en la niñez. Ha construido parques recreacionales, donado viviendas y establecido centros médicos y odontológicos en varias ciudades del país."},
    {"pregunta": "¿Cuál es el compromiso de Colgate-Palmolive con la sostenibilidad?", "respuesta": "La empresa está comprometida con preservar el medio ambiente, ha sido reconocida como una de las Compañías más Éticas del Mundo y obtuvo 100 puntos en el Índice de Equidad Corporativa. También busca que el 100% de sus empaques plásticos sean reciclables."},
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

logo_html = f'<img src="data:image/png;base64,{LOGO_B64}" style="width:150px;">' if LOGO_B64 else "<strong>Colgate-Palmolive</strong>"

sidebar_html = f"""
<div style="
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 220px;
    background: #091D30;
    display: flex;
    flex-direction: column;
    padding: 24px 18px;
    z-index: 1000;
    box-shadow: 2px 0 8px rgba(0,0,0,0.2);
">
    <div style="padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.12); margin-bottom: 16px;">
        {logo_html}
        <div style="font-size:9px; color:rgba(255,255,255,0.5); letter-spacing:2px; text-transform:uppercase; margin-top:8px;">Knowledge Assistant</div>
    </div>
    <div style="margin-top: auto; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.12);">
        <div style="display:flex; justify-content:space-between; font-size:10px; color:rgba(255,255,255,0.45); margin-bottom:6px;">
            <span>Módulo</span><span style="color:#fff; font-weight:600;">TAAML · 2026</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:10px; color:rgba(255,255,255,0.45); margin-bottom:6px;">
            <span>Motor</span><span style="color:#fff; font-weight:600;">{MODEL_NAME}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:10px; color:rgba(255,255,255,0.45);">
            <span>Contexto</span><span style="color:#fff; font-weight:600;">{len(KNOWLEDGE):,} chars</span>
        </div>
    </div>
</div>
"""

css = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&display=swap');
* { font-family: 'Sora', sans-serif !important; }
.gradio-container { margin-left: 220px !important; max-width: calc(100% - 220px) !important; }
.faq-card { background: #fff; border: 1px solid #e2e6f0; border-left: 4px solid #003DA5; border-radius: 6px; padding: 16px 20px; margin-bottom: 10px; }
.faq-q { font-size: 14px; font-weight: 600; color: #001a4d; margin-bottom: 6px; }
.faq-a { font-size: 13px; color: #555; line-height: 1.7; }
.md-out { padding: 20px; }
footer { display: none !important; }
"""

with gr.Blocks(title="Colgate-Palmolive AI", css=css) as demo:

    gr.HTML(sidebar_html)

    with gr.Tabs():

        with gr.Tab("Resumen"):
            gr.Markdown("Genera un resumen ejecutivo sobre cualquier aspecto de Colgate-Palmolive.")
            inp_resumen = gr.Textbox(label="Tema", placeholder="Ej: sostenibilidad, historia de la empresa, productos...", lines=2)
            btn_resumen = gr.Button("Generar resumen", variant="primary")
            out_resumen = gr.Markdown(elem_classes=["md-out"])
            btn_resumen.click(tarea_resumen, inputs=inp_resumen, outputs=out_resumen)

        with gr.Tab("FAQ"):
            gr.Markdown("Preguntas frecuentes sobre Colgate-Palmolive Colombia.")
            for item in FAQ_ESTATICO:
                gr.HTML(f'<div class="faq-card"><div class="faq-q">{item["pregunta"]}</div><div class="faq-a">{item["respuesta"]}</div></div>')

        with gr.Tab("Q&A"):
            gr.Markdown("Conversación directa con el asistente sobre Colgate-Palmolive.")
            chatbot = gr.Chatbot(label=None, height=420)
            estado = gr.State([])
            with gr.Row():
                inp_qa = gr.Textbox(label=None, placeholder="Escribe tu pregunta aquí...", scale=5)
                with gr.Column(scale=1, min_width=110):
                    btn_qa = gr.Button("Enviar", variant="primary")
                    btn_limpiar = gr.Button("Limpiar", variant="secondary")

            btn_qa.click(tarea_qa, inputs=[inp_qa, estado], outputs=[chatbot, estado]).then(lambda: "", outputs=inp_qa)
            inp_qa.submit(tarea_qa, inputs=[inp_qa, estado], outputs=[chatbot, estado]).then(lambda: "", outputs=inp_qa)
            btn_limpiar.click(lambda: ([], []), outputs=[chatbot, estado])

if __name__ == "__main__":
    print(f"📚 Knowledge base: {len(KNOWLEDGE):,} caracteres cargados")
    print(f"🤖 Modelo: {MODEL_NAME}")
    demo.launch(
        share=True,
        theme=gr.themes.Default(),
        css=css
    )