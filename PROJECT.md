# PROJECT.md — Diagnóstico del Asistente Virtual Colgate-Palmolive

> Fecha: 2026-05-09  
> Repositorio: `D:\tecnicas_IA\colgate`  
> App activa: `app_v2.py` (Streamlit) — `app.py` (Gradio, versión anterior)

---

## Resumen ejecutivo

El proyecto tiene un backend funcional (agente LangGraph + RAG FAISS + herramientas) pero la interfaz web (`app_v2.py`) perdió toda la identidad visual que tenía la versión anterior (`app.py`). El resultado es una pantalla genérica de Streamlit sin colores corporativos, sin logo, sin jerarquía visual y con información de debug expuesta al usuario final.

---

## Issues por archivo

### 1. `app_v2.py` — Interfaz principal

| # | Severidad | Problema |
|---|-----------|----------|
| UI-01 | Alta | **Sin identidad de marca**: no hay logo, no hay colores Colgate (rojo `#E31837`, azul `#003DA5`). La app usa el tema gris por defecto de Streamlit. |
| UI-02 | Alta | **Sin mensaje de bienvenida**: el chat arranca vacío, sin contexto ni instrucciones para el usuario. |
| UI-03 | Alta | **Sidebar con información de debug**: los textos "Modelo: mistral-small-latest", "Memoria: LangGraph MemorySaver", "RAG: FAISS + HuggingFace" son detalles técnicos internos que no aportan valor al usuario final y se ven como logs de desarrollo. |
| UI-04 | Media | **Demasiados `st.divider()`**: se usan 4 veces en el sidebar, lo que fragmenta visualmente un panel que tiene poco contenido. |
| UI-05 | Media | **ID de sesión expuesto**: mostrar el UUID de sesión (truncado con `...`) no tiene utilidad para el usuario. |
| UI-06 | Media | **Sin icono/avatar personalizado en los mensajes**: los avatares de `st.chat_message` usan los genéricos de Streamlit ("user" y "assistant") sin personalización. |
| UI-07 | Baja | **Descripción de herramientas plana**: los íconos 📄 y 🗂️ están bien, pero el texto no orienta al usuario sobre qué preguntas puede hacer. |
| BUG-01 | Media | **Detección de error frágil**: `if "429" in respuesta or "capacity exceeded" in respuesta` hace matching de strings sobre el mensaje de excepción. Si el LLM cambia el formato del error o devuelve el código en otro idioma, la condición nunca se cumple. |
| BUG-02 | Baja | **Línea en blanco con espacios en línea 1**: el archivo comienza con una línea vacía que contiene un espacio (`    \n`), lo que puede causar warnings en algunos linters. |

---

### 2. `.streamlit/config.toml` — Configuración del tema

| # | Severidad | Problema |
|---|-----------|----------|
| CFG-01 | Alta | **Sin sección `[theme]`**: el archivo solo tiene `[runner]` y `[logger]`. Streamlit usa el tema predeterminado (gris claro/oscuro), que es lo que hace que la interfaz se vea genérica. Aquí deberían definirse `primaryColor`, `backgroundColor`, `font`, etc. |
| CFG-02 | Baja | `fastRerenderEnabled = false` ralentiza la respuesta visual de la UI al usuario. |

---

### 3. `agent.py` — Lógica del agente

| # | Severidad | Problema |
|---|-----------|----------|
| AGT-01 | Media | **`SYSTEM_PROMPT` duplicado**: `agent.py` define su propio `SYSTEM_PROMPT` hardcodeado. El archivo `prompts.py` existe precisamente para centralizar el prompt pero **nunca se importa**. |
| AGT-02 | Baja | **Excepción genérica expuesta al usuario**: `return f"Error al procesar la pregunta: {str(e)}"` puede filtrar mensajes de error técnicos (stack traces, URLs de API, API keys en variables de entorno). Debería logearse internamente y retornar un mensaje genérico al usuario. |

---

### 4. `prompts.py` — Plantilla del prompt

| # | Severidad | Problema |
|---|-----------|----------|
| PRM-01 | Alta | **Código muerto**: `AGENT_PROMPT_TEMPLATE` y `AGENT_PROMPT` están definidos y documentados, pero **no se importan en ningún archivo**. El archivo es completamente ignorado en tiempo de ejecución. |
| PRM-02 | Media | **Variables incompatibles con LangGraph**: el template usa `{history}`, `{tools}`, `{tool_names}`, `{agent_scratchpad}` — variables propias del patrón `initialize_agent` de LangChain clásico. `create_react_agent` de LangGraph maneja el scratchpad y el historial internamente; esas variables generarían un error si se usara el template. |

---

### 5. `tools.py` — Herramientas del agente

| # | Severidad | Problema |
|---|-----------|----------|
| TLS-01 | Media | **Matching de palabras clave frágil**: `buscar_en_datos_estructurados` usa listas de strings hardcodeadas para detectar la intención (`"teléfono"`, `"horario"`, etc.). Variaciones semánticas como "¿me dan un número de contacto?" o "¿cuándo abren?" no se detectan. |
| TLS-02 | Baja | **Sin fallback semántico**: cuando el matching de keywords falla, retorna "No encontré un dato estructurado..." pero no intenta una búsqueda semántica en los datos. El agente podría quedarse sin respuesta en casos simples. |
| TLS-03 | Baja | **`_cache` fallback silencioso**: si Streamlit no está disponible (ejecución desde CLI), el decorador `_cache` se reemplaza por una función que no hace nada. Cada llamada a `_cargar_recursos()` recargaría el modelo de embeddings. En la práctica esto no ocurre porque el módulo se carga una vez, pero podría volverse un bug si se refactorizara. |

---

### 6. `pyproject.toml` — Dependencias

| # | Severidad | Problema |
|---|-----------|----------|
| DEP-01 | Media | **Dependencias no utilizadas**: `gradio`, `selenium`, `trafilatura`, `webdriver-manager` y `yt-dlp` están en el lock file pero `app_v2.py` no los usa. Son vestigios del taller anterior. Aumentan el tiempo de instalación y el tamaño del entorno. |
| DEP-02 | Baja | `requires-python = ">=3.14"` es Python 3.14 (en prerelease a mayo 2026). Si se despliega en un servidor con 3.11 o 3.12, el install fallará. Debería ser `>=3.11`. |

---

### 7. `app.py` vs `app_v2.py` — Regresión visual

La versión `app.py` (Gradio) tenía:
- Logo de Colgate en base64 embebido
- Sidebar con CSS personalizado y colores corporativos (#091D30 de fondo, #003DA5 como acento)
- Tipografía Sora importada desde Google Fonts
- FAQ con tarjetas estilizadas
- Panel de resumen ejecutivo
- Footer oculto

La versión `app_v2.py` (Streamlit) elimina **todo** lo anterior y no lo reemplaza por ningún estilo equivalente. El salto a Streamlit fue correcto (mejor soporte para chat con historial), pero se perdió completamente la identidad visual.

---

## Plan de mejoras recomendado

### Prioridad 1 — Identidad visual (impacto inmediato)
1. Agregar sección `[theme]` en `.streamlit/config.toml` con colores Colgate
2. Inyectar logo y CSS corporativo vía `st.markdown(..., unsafe_allow_html=True)` o `st.image()`
3. Eliminar info de debug del sidebar; reemplazar por guía de uso para el usuario
4. Agregar mensaje de bienvenida al inicio del chat

### Prioridad 2 — Bugs y lógica
5. Reemplazar detección de errores por manejo tipado de excepciones
6. Importar y usar `prompts.py` en `agent.py`, o eliminar el archivo muerto
7. Separar logging de errores internos del mensaje que ve el usuario

### Prioridad 3 — Mantenimiento
8. Remover dependencias no utilizadas de `pyproject.toml`
9. Corregir `requires-python` a `>=3.11`
10. Mejorar `buscar_en_datos_estructurados` con embeddings semánticos en lugar de keywords

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `app_v2.py` | Interfaz Streamlit (activa) |
| `agent.py` | Agente LangGraph con memoria |
| `tools.py` | RAG FAISS + datos estructurados |
| `prompts.py` | Plantilla de prompt (actualmente sin uso) |
| `build_vectorstore.py` | Script de construcción del índice FAISS |
| `.streamlit/config.toml` | Configuración del tema de Streamlit |
| `data/` | Vectorstore FAISS + JSON de datos estructurados |
| `app.py` | Versión anterior con Gradio (referencia de estilo) |
