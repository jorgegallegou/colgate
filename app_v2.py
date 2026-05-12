import base64
import uuid
from pathlib import Path

import streamlit as st

# ── Helpers (sin importar agent al arranque) ───────────────────────────────────
def _logo_b64() -> str:
    p = Path("assets/logo.png")
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return ""

LOGO_B64    = _logo_b64()
AVATAR_BOT  = "🦷"
AVATAR_USER = "👤"

# Centinelas replicados para no depender del import de agent
ERROR_GENERICO   = "__ERROR__"
ERROR_RATE_LIMIT = "__RATE_LIMIT__"

def nueva_sesion() -> str:
    return str(uuid.uuid4())

BIENVENIDA = (
    "¡Hola! Soy el asistente virtual de **Colgate-Palmolive Colombia**. "
    "Puedo responder preguntas sobre nuestra historia, productos, sedes, "
    "horarios de atención, contacto y más. ¿En qué te puedo ayudar?"
)

CSS = """
<style>
/* Barra superior con color corporativo */
[data-testid="stHeader"] {
    background: #E31837;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #091D30;
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #E31837;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #c01530;
}

/* Título principal */
h1 {
    color: #E31837 !important;
    font-weight: 700 !important;
}

/* Burbuja del asistente */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarImage"]) {
    background: #F4F6FA;
    border-left: 3px solid #E31837;
    border-radius: 0 8px 8px 0;
}

/* Input de chat */
[data-testid="stChatInput"] textarea {
    border: 1.5px solid #E31837 !important;
    border-radius: 8px !important;
}

/* Ocultar footer de Streamlit */
footer { display: none !important; }
</style>
"""

# ── Configuración de la página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Colgate-Palmolive · Asistente Virtual",
    page_icon="🦷",
    layout="wide",
)

st.markdown(CSS, unsafe_allow_html=True)

# ── Carga del agente con spinner (solo la primera vez) ─────────────────────────
@st.cache_resource(show_spinner=False)
def _cargar_agente():
    from agent import preguntar_con_pasos as _fn
    return _fn

with st.spinner("⚙️ Iniciando el asistente virtual, un momento..."):
    preguntar_con_pasos = _cargar_agente()

# ── Estado de sesión ───────────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    thread_id = st.context.cookies.get("thread_id")
    if not thread_id:
        thread_id = nueva_sesion()
        st.components.v1.html(
            f"<script>document.cookie='thread_id={thread_id};path=/;max-age=2592000'</script>",
            height=0,
        )
    st.session_state.thread_id = thread_id
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f'<img src="data:image/png;base64,{LOGO_B64}" '
            f'style="width:160px; margin-bottom:12px; display:block;">',
            unsafe_allow_html=True,
        )
    else:
        st.markdown("### Colgate-Palmolive")

    st.caption("Asistente Virtual · Colombia")
    st.divider()

    st.markdown("**¿Qué puedo preguntar?**")
    st.markdown("- Historia y valores corporativos")
    st.markdown("- Productos y marcas en Colombia")
    st.markdown("- Sedes, teléfono y horarios")
    st.markdown("- Programas sociales y sostenibilidad")
    st.divider()

    if st.button("Nueva conversación", use_container_width=True):
        st.session_state.thread_id = nueva_sesion()
        st.session_state.mensajes = []
        st.rerun()

# ── Cabecera ───────────────────────────────────────────────────────────────────
st.title("Asistente Virtual Colgate-Palmolive")
st.caption("Respuestas basadas en información oficial de Colgate-Palmolive Colombia.")
st.divider()

# ── Historial ──────────────────────────────────────────────────────────────────
if not st.session_state.mensajes:
    with st.chat_message("assistant", avatar=AVATAR_BOT):
        st.markdown(BIENVENIDA)

for msg in st.session_state.mensajes:
    avatar = AVATAR_BOT if msg["role"] == "assistant" else AVATAR_USER
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Input ──────────────────────────────────────────────────────────────────────
if pregunta := st.chat_input("Escribe tu pregunta sobre Colgate-Palmolive..."):
    with st.chat_message("user", avatar=AVATAR_USER):
        st.markdown(pregunta)
    st.session_state.mensajes.append({"role": "user", "content": pregunta})

    with st.chat_message("assistant", avatar=AVATAR_BOT):
        with st.spinner("Consultando..."):
            respuesta, pasos = preguntar_con_pasos(pregunta, st.session_state.thread_id)

        if respuesta == ERROR_RATE_LIMIT:
            msg = "El servicio está temporalmente saturado. Espera unos segundos e intenta de nuevo."
            st.warning(msg)
            respuesta = f"⏱️ {msg}"
            st.session_state.thread_id = nueva_sesion()
        elif respuesta == ERROR_GENERICO:
            msg = "Lo siento, ocurrió un error al procesar tu pregunta. Por favor intenta de nuevo."
            st.error(msg)
            respuesta = msg
            st.session_state.thread_id = nueva_sesion()
        else:
            st.markdown(respuesta.replace("$", r"\$"))
            if pasos:
                with st.expander("🧠 Ver razonamiento del agente"):
                    for j, paso in enumerate(pasos):
                        if paso["tipo"] == "accion":
                            st.markdown(f"**🔧 Herramienta seleccionada:** `{paso['herramienta']}`")
                            st.caption(f"Consulta enviada: {paso['entrada']}")
                        else:
                            st.markdown("**📋 Información recuperada:**")
                            st.code(paso["contenido"], language="text")
                        if j < len(pasos) - 1:
                            st.divider()

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
