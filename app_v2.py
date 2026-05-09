import base64
from pathlib import Path

import streamlit as st

from agent import preguntar, nueva_sesion

# ── Helpers ────────────────────────────────────────────────────────────────────
def _logo_b64() -> str:
    p = Path("assets/logo.png")
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return ""

LOGO_B64 = _logo_b64()

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
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
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

# ── Estado de sesión ───────────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = nueva_sesion()
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
    with st.chat_message("assistant"):
        st.markdown(BIENVENIDA)

for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input ──────────────────────────────────────────────────────────────────────
if pregunta := st.chat_input("Escribe tu pregunta sobre Colgate-Palmolive..."):
    with st.chat_message("user"):
        st.markdown(pregunta)
    st.session_state.mensajes.append({"role": "user", "content": pregunta})

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            respuesta = preguntar(pregunta, st.session_state.thread_id)

        try:
            status = int(str(respuesta).split()[0]) if str(respuesta)[0].isdigit() else 0
        except (ValueError, IndexError):
            status = 0

        if "429" in str(respuesta) or "capacity exceeded" in str(respuesta).lower() or status == 429:
            msg_usuario = "El servicio está temporalmente saturado. Espera unos segundos e intenta de nuevo."
            st.warning(msg_usuario)
            respuesta = f"⏱️ {msg_usuario}"
        else:
            st.markdown(respuesta)

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
