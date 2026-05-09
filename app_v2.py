import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import streamlit as st
from agent import preguntar, nueva_sesion

# ── Configuración de la página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Colgate-Palmolive AI",
    page_icon="🦷",
    layout="centered",
)

# ── Estilos ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .st-emotion-cache-1c7y2kl { background-color: #003DA5; }
    header { background-color: #003DA5 !important; }
    .block-container { max-width: 800px; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 🦷 Asistente Colgate-Palmolive Colombia")
st.markdown("Agente conversacional con memoria · RAG + Datos estructurados")
st.divider()

# ── Estado de sesión ───────────────────────────────────────────────────────────
# Streamlit recarga el script en cada interacción.
# st.session_state persiste los datos entre recargas dentro de la misma sesión.

if "thread_id" not in st.session_state:
    # Generar UUID único para esta sesión — identifica la memoria en LangGraph
    st.session_state.thread_id = nueva_sesion()

if "mensajes" not in st.session_state:
    # Historial de mensajes para mostrar en la interfaz
    st.session_state.mensajes = []

# ── Sidebar con info de sesión ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Sesión activa")
    st.code(st.session_state.thread_id[:8] + "...", language=None)
    st.caption("ID único de conversación")
    st.divider()

    st.markdown("### Herramientas disponibles")
    st.markdown("📄 **base_documental** — Historia, valores, productos, operaciones")
    st.markdown("🗂️ **datos_estructurados** — Teléfono, horarios, NIT, sedes, marcas")
    st.divider()

    if st.button("🗑️ Nueva conversación", use_container_width=True):
        st.session_state.thread_id = nueva_sesion()
        st.session_state.mensajes = []
        st.rerun()

    st.caption(f"Modelo: mistral-small-latest")
    st.caption(f"Memoria: LangGraph MemorySaver")

# ── Historial de chat ──────────────────────────────────────────────────────────
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# ── Input del usuario ──────────────────────────────────────────────────────────
if pregunta := st.chat_input("Escribe tu pregunta sobre Colgate-Palmolive..."):

    # Mostrar pregunta del usuario
    with st.chat_message("user"):
        st.markdown(pregunta)
    st.session_state.mensajes.append({"role": "user", "content": pregunta})

    # Obtener respuesta del agente
    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            respuesta = preguntar(pregunta, st.session_state.thread_id)
        st.markdown(respuesta)
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
