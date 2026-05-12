# PROJECT.md — Diagnóstico del Asistente Virtual Colgate-Palmolive

> Fecha: 2026-05-12  
> Repositorio: `C:\colgate`  
> App activa: `app_v2.py` (Streamlit) — `app.py` (Gradio, versión anterior)

---

## Resumen ejecutivo

El proyecto tiene un backend funcional (agente LangGraph + RAG FAISS + herramientas). Todos los issues de interfaz, código y comportamiento del agente detectados durante las sesiones de desarrollo han sido corregidos. El sistema supera las 4 pruebas de validación requeridas por el taller. La memoria conversacional es ahora persistente en disco mediante PostgreSQL corriendo en Docker, sobreviviendo reinicios del servidor y recargas del navegador.

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
| UI-06 | Media | ✅ Corregido | **Sin avatar personalizado**: los avatares de `st.chat_message` usaban los genéricos de Streamlit. → Logo corporativo (`assets/logo.png`) como avatar del asistente; emoji `👤` para el usuario. CSS actualizado para cubrir el selector `stChatMessageAvatarImage`. |
| UI-07 | Baja | ✅ Corregido | **Descripción de herramientas plana**: el sidebar no orientaba al usuario sobre qué preguntar. → Reemplazado por lista de temas consultables. |
| UI-08 | Alta | ✅ Corregido | **Razonamiento ReAct no visible en UI**: los pasos Thought/Action/Observation ocurrían internamente sin visibilidad. → Nueva función `preguntar_con_pasos()` en `agent.py` (con `_extraer_pasos()`) devuelve los pasos del turno actual; `app_v2.py` los muestra en `st.expander("🧠 Ver razonamiento del agente")`. |
| UI-09 | Media | ✅ Corregido | **Pantalla en blanco durante la primera carga**: la primera visita al browser mostraba pantalla vacía ~10 s mientras el modelo de embeddings cargaba, sin feedback al usuario. → Import de `agent` movido a `@st.cache_resource` con carga lazy; spinner visible durante la espera. |
| **UI-10** | **Alta** | ✅ Corregido | **`thread_id` volátil entre recargas**: `st.session_state` se resetea al recargar el navegador, generando un `thread_id` nuevo y perdiendo el historial de la sesión. → `thread_id` guardado en cookie del navegador con duración de 30 días (`max-age=2592000`). Al recargar, la app lee la cookie y recupera el historial desde PostgreSQL. |
| BUG-01 | Media | ✅ Corregido | **Detección de error frágil**: matching de strings sobre el mensaje de excepción. → Reemplazado por centinelas tipados (`ERROR_GENERICO`, `ERROR_RATE_LIMIT`). |
| BUG-02 | Baja | ✅ Corregido | **Línea en blanco con espacios en línea 1**: causaba warnings en linters. → Eliminada en reescritura del archivo. |
| BUG-NEW-02 | Alta | ✅ Corregido | **Respuestas acumuladas por estado corrupto en MemorySaver**: cuando `agente.invoke()` fallaba a mitad de ejecución, LangGraph persistía el mensaje del usuario en el checkpointer sin respuesta del asistente. → Al detectar un error, `app_v2.py` resetea `thread_id` inmediatamente. |

---

### 2. `.streamlit/config.toml` — Configuración del tema

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| CFG-01 | Alta | ✅ Corregido | **Sin sección `[theme]`**: Streamlit usaba el tema gris por defecto. → Agregada sección `[theme]` con `primaryColor = "#E31837"`. |
| CFG-02 | Baja | ✅ Corregido | `fastRerenderEnabled` era una opción eliminada en versiones recientes de Streamlit. → Opción eliminada. |

---

### 3. `agent.py` — Lógica del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| AGT-01 | Media | ✅ Corregido | **`SYSTEM_PROMPT` duplicado**: `agent.py` lo definía inline ignorando `prompts.py`. → Ahora importa `SYSTEM_PROMPT` desde `prompts.py`. |
| AGT-02 | Baja | ✅ Corregido | **Excepción técnica expuesta al usuario**: `str(e)` podía filtrar API keys o stack traces. → Errores logueados con `logging.error(..., exc_info=True)`; función retorna centinelas tipados. |
| AGT-03 | Baja | ✅ Corregido | **Sin docstrings en funciones**. → Docstrings añadidos a todas las funciones públicas y privadas. |
| **AGT-04** | **Alta** | ✅ Corregido | **Memoria volátil con `MemorySaver`**: el historial se guardaba en RAM y se perdía al reiniciar la app. → Reemplazado por `PostgresSaver` de `langgraph-checkpoint-postgres`, conectado a PostgreSQL vía `psycopg`. El historial persiste en disco y sobrevive reinicios completos del servidor. `checkpointer.setup()` crea las tablas automáticamente en la primera ejecución. |
| **AGT-05** | **Media** | ✅ Corregido | **Import duplicado de `os`**: aparecía en línea 3 y línea 6. → Eliminado el duplicado. |

---

### 4. `prompts.py` — System prompt del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| PRM-01 | Alta | ✅ Corregido | **Código muerto**: `AGENT_PROMPT_TEMPLATE` y `AGENT_PROMPT` nunca se importaban. → Archivo refactorizado: exporta solo `SYSTEM_PROMPT`. |
| PRM-02 | Media | ✅ Corregido | **Variables incompatibles con LangGraph**: `{history}`, `{tools}`, `{agent_scratchpad}`. → Eliminadas. |
| BUG-NEW-03 | Alta | ✅ Corregido | **Agente reportaba "no hay información" sobre sostenibilidad**. → Agregada instrucción de fallback entre herramientas. |
| PRM-03 | Media | ✅ Corregido | **Criterio de selección ambiguo**. → Criterio reescrito basado en tipo de respuesta esperada. |

---

### 5. `tools.py` — Herramientas del agente

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| TLS-01 | Media | ✅ Corregido | **Matching de palabras clave frágil**. → Función `_normalizar()` con `unicodedata`. |
| TLS-02 | Baja | ✅ Corregido | **Keyword matching devolvía categoría equivocada**. → Categorías específicas con prioridad sobre FAQs. |
| TLS-03 | Baja | Pendiente | **`_cache` fallback silencioso** en ejecución CLI sin Streamlit. |
| TLS-04 | Baja | ✅ Corregido | **Sin docstrings**. → Docstrings añadidos. |
| TLS-05 | Media | ✅ Corregido | **~400 warnings `[transformers] Accessing __path__`**. → Doble supresión con `warnings.filterwarnings` y `logging.setLevel`. |
| BUG-NEW-01 | Alta | ✅ Corregido | **`UnicodeEncodeError` en consola Windows**: emojis en `print()` causaban crash en cp1252. → Emojis eliminados de los `print()`. |

---

### 6. `pyproject.toml` — Dependencias

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| DEP-01 | Media | Pendiente | **Dependencias de scraping mezcladas con la app**. Se mantienen para no romper el flujo de reconstrucción del knowledge base. |
| DEP-02 | Baja | ✅ Corregido | `requires-python = ">=3.14"` demasiado restrictivo. → Corregido a `>=3.12`. |
| **DEP-03** | **Alta** | ✅ Corregido | **Python 3.14 incompatible con `torch`**: `torch` no tiene soporte estable para Python 3.14, causando `KeyboardInterrupt` al cargar el modelo de embeddings HuggingFace. → Entorno virtual recreado con Python 3.12 (`uv venv --python 3.12` + `uv sync`). |
| **DEP-04** | **Alta** | ✅ Corregido | **Sin dependencias de persistencia**: el proyecto no tenía soporte para checkpointer en base de datos. → Agregados `langgraph-checkpoint-postgres==3.0.5`, `psycopg==3.3.4`, `psycopg-pool==3.3.1` y `psycopg-binary==3.3.4` via `uv add`. |

---

### 7. `README.md` — Documentación

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| DOC-01 | Media | ✅ Corregido | **Diagrama de arquitectura en ASCII**. → Reemplazado por diagrama Mermaid. |
| DOC-02 | Baja | ✅ Corregido | **Razonamiento del agente documentado solo en README**. → Ahora visible en tiempo real en la UI. |
| DOC-03 | Baja | ✅ Corregido | **Meta-prompt desactualizado en sección 10.3**. → Actualizado al criterio actual. |
| **DOC-04** | **Alta** | ✅ Corregido | **README no reflejaba arquitectura de persistencia**: sección 8.2, 9, 12, 13 y 14 describían `MemorySaver` y memoria volátil. → Actualizadas para reflejar `PostgresSaver`, Docker, cookie del `thread_id`, nueva variable `POSTGRES_URI` en `.env`, comando de arranque de Docker y limitaciones reales. |

---

### 8. Infraestructura — Docker + PostgreSQL

| # | Severidad | Estado | Problema / Decisión |
|---|-----------|--------|----------|
| **INF-01** | **Alta** | ✅ Implementado | **Memoria volátil requería solución de persistencia**: el profesor confirmó que se requiere persistencia real en disco. → PostgreSQL `postgres:16` desplegado en Docker con contenedor `database` (puerto 5432). URI de conexión en `.env` como `POSTGRES_URI`. `PostgresSaver.setup()` crea las tablas automáticamente. Verificado que el historial sobrevive reinicios completos de la app. |
| **INF-02** | **Media** | ✅ Resuelto | **Docker no arranca automáticamente con Windows**: el contenedor debe levantarse manualmente antes de lanzar la app. → `docker-compose.yml` agregado al repositorio. Comando unificado: `docker compose up -d`. Credenciales leídas desde `.env` via `${POSTGRES_USER}`, `${POSTGRES_DB}`, `${POSTGRES_PASSWORD}`. |
| **INF-03** | **Media** | ✅ Implementado | **Setup manual de contenedor PostgreSQL**: requería `docker run` con flags explícitos en cada instalación nueva. → `docker-compose.yml` añadido con servicio `database` (postgres:16), healthcheck automático y volumen montado en `./db/`. `db/` agregado a `.gitignore` para excluir datos locales del repositorio. |

---

### 9. `app.py` vs `app_v2.py` — Regresión visual (resuelta)

La versión `app.py` (Gradio) tenía logo, sidebar con CSS corporativo, tipografía Sora y FAQ con tarjetas. `app_v2.py` eliminó todo eso al migrar a Streamlit. Resuelto en commit `d7df437` con branding completo y CSS corporativo.

---

## Historial de cambios

| Commit | Descripción |
|--------|-------------|
| `3263bbb` | fix: conexión PostgreSQL con pool, cookie SameSite, tests y fix redes sociales |
| `c371167` | fix: agregar 'redes sociales' como keyword en datos_estructurados |
| `d451eb0` | fix: corregir 7 bugs detectados en revisión del Taller 2 |
| `627236b` | docs: actualizar hashes y limpiar credenciales en PROJECT.md |
| `92e0215` | docs: actualizar hashes y limpiar credenciales en PROJECT.md |
| `ba1d198` | feat: persistencia de memoria con PostgresSaver en Docker + Python 3.12 + docs actualizados |
| `aee66f5` | fix: revertir escape de asteriscos, mantener solo escape de signo dolar |
| `7bc6afd` | fix: escapar caracteres Markdown en respuestas para evitar renderizado incorrecto |
| `c0bc12a` | fix: corregir TLS-02 — keyword matching tiene prioridad sobre FAQ scoring |
| `6add79b` | feat: docstrings, razonamiento ReAct en UI y diagrama Mermaid |
| `8bd5750` | fix: usar emoji como avatar del asistente en lugar de Path object |
| `088a4db` | fix: interfaz limpia sin CSS personalizado |
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
| TLS-03 | Baja | `_cache` fallback silencioso en ejecución CLI sin Streamlit |
| DEP-01 | Media | Evaluar separar dependencias de scraping en grupo opcional de `pyproject.toml` |

---

## Archivos clave

| Archivo | Rol |
|---------|-----|
| `app_v2.py` | Interfaz Streamlit (activa) — cookie de sesión para persistencia del `thread_id` |
| `agent.py` | Agente LangGraph con `PostgresSaver` y centinelas de error |
| `tools.py` | RAG FAISS + datos estructurados con normalización unicode |
| `prompts.py` | System prompt del agente con criterio de selección por tipo de respuesta |
| `build_vectorstore.py` | Script de construcción del índice FAISS |
| `clean_knowledge_base.py` | Limpieza y re-chunking de knowledge_base.txt para FAISS |
| `.streamlit/config.toml` | Tema corporativo Streamlit |
| `data/vectorstore/` | Índice FAISS (137 chunks) |
| `data/datos_estructurados.json` | Datos de contacto, horarios, sedes, marcas, etc. |
| `app.py` | Versión anterior con Gradio (referencia de estilo) |

## Infraestructura

| Componente | Detalle |
|-----------|---------|
| Docker Desktop | Requerido antes de lanzar la app |
| Servicio | `database` — `postgres:16` — puerto 5432 |
| Base de datos | Credenciales en `.env` (`POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`) |
| Arranque | `docker compose up -d` |
| Primera vez | Ver README sección 12 |
