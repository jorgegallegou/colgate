# PROJECT.md — Diagnóstico del Asistente Virtual Colgate-Palmolive

> Fecha: 2026-05-09  
> Repositorio: `D:\tecnicas_IA\colgate`  
> App activa: `app_v2.py` (Streamlit) — `app.py` (Gradio, versión anterior)

---

## Resumen ejecutivo

El proyecto tiene un backend funcional (agente LangGraph + RAG FAISS + herramientas). Todos los issues de interfaz, código y comportamiento del agente detectados durante las sesiones de desarrollo han sido corregidos. El sistema supera las 4 pruebas de validación requeridas por el taller.

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
| BUG-01 | Media | ✅ Corregido | **Detección de error frágil**: matching de strings sobre el mensaje de excepción. → Reemplazado por centinelas tipados (`ERROR_GENERICO`, `ERROR_RATE_LIMIT`). |
| BUG-02 | Baja | ✅ Corregido | **Línea en blanco con espacios en línea 1**: causaba warnings en linters. → Eliminada en reescritura del archivo. |
| **BUG-NEW-02** | **Alta** | ✅ Corregido | **Respuestas acumuladas por estado corrupto en MemorySaver**: cuando `agente.invoke()` fallaba a mitad de ejecución, LangGraph persistía el mensaje del usuario en el checkpointer sin respuesta del asistente. En el siguiente turno exitoso, el agente veía todos los mensajes acumulados sin responder y los contestaba juntos, generando alucinaciones. → Al detectar un error, `app_v2.py` resetea `thread_id` inmediatamente, abandonando el estado corrupto antes del siguiente turno. |

---

### 2. `.streamlit/config.toml` — Configuración del tema

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| CFG-01 | Alta | ✅ Corregido | **Sin sección `[theme]`**: Streamlit usaba el tema gris por defecto. → Agregada sección `[theme]` con `primaryColor = "#E31837"`, `backgroundColor`, `secondaryBackgroundColor` y `textColor`. |
| CFG-02 | Baja | ✅ Corregido | `fastRerenderEnabled` era una opción eliminada en versiones recientes de Streamlit y causaba un warning de config inválida al arrancar. → Opción eliminada. |

---

### 3. `agent.py` — Lógica del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| AGT-01 | Media | ✅ Corregido | **`SYSTEM_PROMPT` duplicado**: `agent.py` lo definía inline ignorando `prompts.py`. → Ahora importa `SYSTEM_PROMPT` desde `prompts.py`. |
| AGT-02 | Baja | ✅ Corregido | **Excepción técnica expuesta al usuario**: `str(e)` podía filtrar API keys o stack traces. → Errores logueados con `logging.error(..., exc_info=True)`; función retorna centinelas tipados en lugar de strings de error. |

---

### 4. `prompts.py` — System prompt del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| PRM-01 | Alta | ✅ Corregido | **Código muerto**: `AGENT_PROMPT_TEMPLATE` y `AGENT_PROMPT` (PromptTemplate) nunca se importaban. → Archivo refactorizado: exporta solo `SYSTEM_PROMPT` como string puro compatible con LangGraph. |
| PRM-02 | Media | ✅ Corregido | **Variables incompatibles con LangGraph**: `{history}`, `{tools}`, `{agent_scratchpad}` son del patrón `initialize_agent` clásico. → Eliminadas; LangGraph gestiona el historial y el scratchpad internamente. |
| **BUG-NEW-03** | **Alta** | ✅ Corregido | **Agente reportaba "no hay información" sobre sostenibilidad**: el agente usaba solo `base_documental` (RAG) y, al no recuperar chunks relevantes de sostenibilidad ambiental, concluía que no existía información — ignorando que `datos_estructurados.json` sí contiene esos datos. → Agregada instrucción de fallback: "Si la primera herramienta no devuelve información suficiente, prueba con la otra antes de concluir que no hay información." |

---

### 5. `tools.py` — Herramientas del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| TLS-01 | Media | ✅ Corregido | **Matching de palabras clave frágil**: listas hardcodeadas con variantes acentuadas y sin acentuar duplicadas. → Función `_normalizar()` con `unicodedata` elimina tildes antes del matching; listas depuradas y ampliadas. |
| TLS-02 | Baja | Pendiente | **Sin fallback semántico en datos_estructurados**: si el keyword matching falla, no intenta búsqueda semántica sobre el JSON. Mitigado parcialmente por BUG-NEW-03. |
| TLS-03 | Baja | Pendiente | **`_cache` fallback silencioso** en ejecución CLI sin Streamlit. |
| **BUG-NEW-01** | **Alta** | ✅ Corregido | **`UnicodeEncodeError` en consola Windows**: los `print()` con emojis (`🔧`, `✓`) dentro de `_cargar_recursos()` causaban crash al iniciar la app (codificación cp1252). La excepción dentro de `@st.cache_resource` impedía cargar el vectorstore y bloqueaba el arranque completo. → Emojis eliminados de los `print()`. |

---

### 6. `pyproject.toml` — Dependencias

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| DEP-01 | Media | Pendiente | **Dependencias de scraping en el mismo grupo que la app**: `gradio`, `selenium`, `trafilatura`, `webdriver-manager`, `yt-dlp` no las usa `app_v2.py` pero sí los scrapers. Se mantienen para no romper el flujo de reconstrucción del knowledge base. |
| DEP-02 | Baja | ✅ Corregido | `requires-python = ">=3.14"` demasiado restrictivo. → Corregido a `>=3.11`. |

---

### 7. `app.py` vs `app_v2.py` — Regresión visual (resuelta)

La versión `app.py` (Gradio) tenía logo, sidebar con CSS corporativo, tipografía Sora y FAQ con tarjetas. `app_v2.py` eliminó todo eso al migrar a Streamlit. Resuelto en commit `d7df437` con branding completo y CSS corporativo.

---

## Historial de cambios

| Commit | Descripción |
|--------|-------------|
| `d7df437` | feat: rediseño visual corporativo y mejoras de código |
| `32850b3` | fix: UnicodeEncodeError en consola Windows y config obsoleta |
| `3f3b15f` | docs: PROJECT.md con estado de issues y bugs corregidos |
| `1b3c724` | docs: documentación completa del Módulo 2 en README |
| `80bf39f` | fix: resetear thread_id en error para evitar respuestas acumuladas |
| `3d7de1c` | fix: fallback entre herramientas en system prompt |

---

## Issues pendientes

| # | Severidad | Descripción |
|---|-----------|-------------|
| UI-06 | Media | Avatar personalizado en burbujas de chat |
| TLS-02 | Baja | Fallback semántico en `buscar_en_datos_estructurados` |
| TLS-03 | Baja | `_cache` fallback silencioso en ejecución CLI |
| DEP-01 | Media | Evaluar separar dependencias de scraping en grupo opcional de `pyproject.toml` |

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `app_v2.py` | Interfaz Streamlit (activa) |
| `agent.py` | Agente LangGraph con memoria y centinelas de error |
| `tools.py` | RAG FAISS + datos estructurados con normalización unicode |
| `prompts.py` | System prompt del agente con criterio de fallback |
| `build_vectorstore.py` | Script de construcción del índice FAISS |
| `.streamlit/config.toml` | Tema corporativo Streamlit |
| `data/vectorstore/` | Índice FAISS (137 chunks) |
| `data/datos_estructurados.json` | Datos de contacto, horarios, sedes, marcas, etc. |
| `app.py` | Versión anterior con Gradio (referencia de estilo) |
