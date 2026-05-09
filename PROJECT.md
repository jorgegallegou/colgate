# PROJECT.md — Diagnóstico del Asistente Virtual Colgate-Palmolive

> Fecha: 2026-05-09  
> Repositorio: `D:\tecnicas_IA\colgate`  
> App activa: `app_v2.py` (Streamlit) — `app.py` (Gradio, versión anterior)

---

## Resumen ejecutivo

El proyecto tiene un backend funcional (agente LangGraph + RAG FAISS + herramientas) pero la interfaz web (`app_v2.py`) perdió toda la identidad visual que tenía la versión anterior (`app.py`). El resultado era una pantalla genérica de Streamlit sin colores corporativos, sin logo, sin jerarquía visual y con información de debug expuesta al usuario final. Todos los issues de Prioridad 1 y 2 han sido corregidos.

---

## Issues por archivo

### 1. `app_v2.py` — Interfaz principal

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| UI-01 | Alta | ✅ Corregido | **Sin identidad de marca**: no había logo ni colores Colgate. → CSS corporativo inyectado con `#E31837` y `#091D30`; logo cargado desde `assets/logo.png`. |
| UI-02 | Alta | ✅ Corregido | **Sin mensaje de bienvenida**: el chat arrancaba vacío. → Mensaje de bienvenida mostrado automáticamente cuando `mensajes` está vacío. |
| UI-03 | Alta | ✅ Corregido | **Sidebar con información de debug**: textos técnicos internos expuestos al usuario. → Reemplazado por guía de uso ("¿Qué puedo preguntar?"). |
| UI-04 | Media | ✅ Corregido | **Demasiados `st.divider()`**: 4 divisores en un sidebar con poco contenido. → Reducido a 2. |
| UI-05 | Media | ✅ Corregido | **ID de sesión expuesto**: UUID truncado sin utilidad para el usuario. → Eliminado. |
| UI-06 | Media | Pendiente | **Sin avatar personalizado**: los avatares de `st.chat_message` usan los genéricos de Streamlit. |
| UI-07 | Baja | ✅ Corregido | **Descripción de herramientas plana**: el sidebar no orientaba al usuario sobre qué preguntar. → Reemplazado por lista de temas consultables. |
| BUG-01 | Media | ✅ Corregido | **Detección de error frágil**: matching de strings sobre el mensaje de excepción. → Mejorado con manejo tipado y `str().lower()`. |
| BUG-02 | Baja | ✅ Corregido | **Línea en blanco con espacios en línea 1**: causaba warnings en linters. → Eliminada en reescritura del archivo. |

---

### 2. `.streamlit/config.toml` — Configuración del tema

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| CFG-01 | Alta | ✅ Corregido | **Sin sección `[theme]`**: Streamlit usaba el tema gris por defecto. → Agregada sección `[theme]` con `primaryColor = "#E31837"`, `backgroundColor`, `secondaryBackgroundColor` y `textColor`. |
| CFG-02 | Baja | ✅ Corregido | `fastRerenderEnabled = false` ralentizaba la UI. → Opción eliminada (fue removida de Streamlit en versiones recientes; su presencia causaba un warning de config inválida al arrancar). |

---

### 3. `agent.py` — Lógica del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| AGT-01 | Media | ✅ Corregido | **`SYSTEM_PROMPT` duplicado**: `agent.py` lo definía inline ignorando `prompts.py`. → Ahora importa `SYSTEM_PROMPT` desde `prompts.py`. |
| AGT-02 | Baja | ✅ Corregido | **Excepción técnica expuesta al usuario**: `str(e)` podía filtrar API keys o stack traces. → Errores logueados con `logging.error(..., exc_info=True)`; usuario recibe mensaje genérico. |

---

### 4. `prompts.py` — Plantilla del prompt

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| PRM-01 | Alta | ✅ Corregido | **Código muerto**: `AGENT_PROMPT_TEMPLATE` y `AGENT_PROMPT` nunca se importaban. → Archivo refactorizado: exporta solo `SYSTEM_PROMPT` como string puro. |
| PRM-02 | Media | ✅ Corregido | **Variables incompatibles con LangGraph**: `{history}`, `{tools}`, `{agent_scratchpad}` son del patrón `initialize_agent` clásico, incompatibles con `create_react_agent`. → Eliminadas; LangGraph gestiona el historial y el scratchpad internamente. |

---

### 5. `tools.py` — Herramientas del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| TLS-01 | Media | ✅ Corregido | **Matching de palabras clave frágil**: listas hardcodeadas con variantes acentuadas y sin acentuar duplicadas. → Reemplazado por función `_normalizar()` con `unicodedata` que elimina tildes antes del matching; listas de keywords depuradas y ampliadas. |
| TLS-02 | Baja | Pendiente | **Sin fallback semántico**: si el matching falla, no intenta búsqueda semántica. |
| TLS-03 | Baja | Pendiente | **`_cache` fallback silencioso** en ejecución CLI sin Streamlit. |
| **BUG-NEW-01** | **Alta** | ✅ Corregido | **`UnicodeEncodeError` en consola Windows**: los `print()` con emojis (`🔧`, `✓`) dentro de `_cargar_recursos()` causaban un crash al iniciar la app en Windows (codificación cp1252). La excepción ocurría dentro del decorador `@st.cache_resource`, impidiendo cargar el vectorstore y bloqueando el arranque completo. → Emojis eliminados de los `print()`. |

---

### 6. `pyproject.toml` — Dependencias

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| DEP-01 | Media | Pendiente | **Dependencias no utilizadas por la app**: `gradio`, `selenium`, `trafilatura`, `webdriver-manager`, `yt-dlp`. Nota: se mantienen porque los scripts de scraping (`scraper.py`, `scraper_youtube.py`) las requieren para reconstruir la knowledge base. |
| DEP-02 | Baja | ✅ Corregido | `requires-python = ">=3.14"` demasiado restrictivo (Python 3.14 en prerelease). → Corregido a `>=3.11`. |

---

### 7. `app.py` vs `app_v2.py` — Regresión visual

La versión `app.py` (Gradio) tenía: logo embebido, sidebar con CSS corporativo, tipografía Sora, FAQ con tarjetas, panel de resumen y footer oculto.

La versión `app_v2.py` (Streamlit) eliminó todo lo anterior. El salto a Streamlit fue correcto (mejor soporte para chat con historial), pero se perdió la identidad visual. **Issue resuelto en commit `d7df437`.**

---

## Historial de cambios

| Commit | Descripción |
|--------|-------------|
| `d7df437` | feat: rediseño visual corporativo y mejoras de código |
| `32850b3` | fix: corregir UnicodeEncodeError en consola Windows y config obsoleta |

---

## Issues pendientes

| # | Severidad | Descripción |
|---|-----------|-------------|
| UI-06 | Media | Avatar personalizado en burbujas de chat |
| TLS-02 | Baja | Fallback semántico en `buscar_en_datos_estructurados` |
| TLS-03 | Baja | `_cache` fallback silencioso en ejecución CLI |
| DEP-01 | Media | Evaluar si separar dependencias de scraping en un grupo opcional |

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `app_v2.py` | Interfaz Streamlit (activa) |
| `agent.py` | Agente LangGraph con memoria |
| `tools.py` | RAG FAISS + datos estructurados |
| `prompts.py` | System prompt del agente |
| `build_vectorstore.py` | Script de construcción del índice FAISS |
| `.streamlit/config.toml` | Configuración del tema de Streamlit |
| `data/` | Vectorstore FAISS + JSON de datos estructurados |
| `app.py` | Versión anterior con Gradio (referencia de estilo) |
