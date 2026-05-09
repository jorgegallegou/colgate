import streamlit as st
from agent import preguntar, nueva_sesion

st.set_page_config(
    page_title="Colgate-Palmolive · Asistente Virtual",
    page_icon="🦷",
    layout="wide",
)

# ── Estado de sesión ───────────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = nueva_sesion()
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🦷 Colgate-Palmolive")
    st.caption("Asistente Virtual Colombia")
    st.divider()

    st.markdown("**Sesión activa**")
    st.code(st.session_state.thread_id[:8] + "...", language=None)
    st.caption("ID único de conversación")
    st.divider()

    st.markdown("**Herramientas**")
    st.markdown("📄 **base_documental** — Historia, valores, productos")
    st.markdown("🗂️ **datos_estructurados** — Teléfono, NIT, sedes, horarios")
    st.divider()

    if st.button("🔄 Nueva conversación", use_container_width=True):
        st.session_state.thread_id = nueva_sesion()
        st.session_state.mensajes = []
        st.rerun()

    st.divider()
    st.caption("Modelo: mistral-small-latest")
    st.caption("Memoria: LangGraph MemorySaver")
    st.caption("RAG: FAISS + HuggingFace")
    st.caption("UAO · Técnicas Avanzadas IA · 2026")

# ── Título principal ───────────────────────────────────────────────────────────
st.title("🦷 Asistente Virtual Colgate-Palmolive Colombia")
st.caption("Agente conversacional con memoria · RAG + Datos estructurados")
st.divider()

# ── Historial ──────────────────────────────────────────────────────────────────
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
        if "429" in respuesta or "capacity exceeded" in respuesta:
            st.warning("El servicio está temporalmente saturado. Espera unos segundos e intenta de nuevo.")
            respuesta = "⏱️ Servicio temporalmente saturado. Intenta de nuevo en unos segundos."
        else:
            st.markdown(respuesta)
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
