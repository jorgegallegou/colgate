# PROJECT.md — Diagnóstico del Asistente Virtual Colgate-Palmolive

> Fecha: 2026-05-16 (última actualización)  
> Repositorio: `D:\tecnicas_IA\colgate`  
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
| **AGT-06** | **Crítica** | ✅ Corregido | **Imports inexistentes que crasheaban el arranque**: usaba `from langgraph.prebuilt import create_react_agent` con parámetro `state_modifier` — ambos eliminados en LangGraph V1.0. → Reemplazado por el API correcto: `from langchain.agents import create_agent` + `from langchain.agents.middleware import dynamic_prompt, ModelRequest`. El middleware recibe `request.messages` (no `request.state["messages"]`) y retorna `str`. |
| AGT-07 | Media | ✅ Corregido | **`MODEL_NAME` y `TEMPERATURE` hardcodeados en `agent.py`**: duplicaban información que debía vivir en `config.py`. → Movidos a `config.py` e importados. |
| AGT-08 | Baja | ✅ Corregido | **Lógica de detección de rate limit duplicada**: las funciones `preguntar()` y `preguntar_con_pasos()` repetían el mismo `any(k in err for k in ...)`. → Extraído al helper privado `_es_rate_limit(exc)`. |
| AGT-09 | Baja | ✅ Corregido | **Detección del tipo de mensaje por string**: `getattr(msg, "type", None) == "human"` y `type(msg).__name__ == "HumanMessage"`. → Reemplazado por `isinstance(msg, HumanMessage)` (tipado correcto). |

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
| TLS-03 | Baja | Pendiente | **`_cache` fallback silencioso** en ejecución CLI sin Streamlit: cuando Streamlit no está disponible, los recursos se recargan en cada llamada sin ninguna advertencia. |
| TLS-04 | Baja | ✅ Corregido | **Sin docstrings**. → Docstrings añadidos. |
| TLS-05 | Media | ✅ Corregido | **~400 warnings `[transformers] Accessing __path__`**. → Doble supresión con `warnings.filterwarnings` y `logging.setLevel`. |
| BUG-NEW-01 | Alta | ✅ Corregido | **`UnicodeEncodeError` en consola Windows**: emojis en `print()` causaban crash en cp1252. → Emojis eliminados de los `print()`. |
| **TLS-06** | **Alta** | ✅ Corregido | **`buscar_en_datos_estructurados` no existía**: los tests la importaban directamente (`from tools import buscar_en_datos_estructurados`) pero la función no estaba definida — todos los tests del agente fallaban. → Lógica extraída de `@tool datos_estructurados` a función pura `buscar_en_datos_estructurados()`; el `@tool` llama a la función pura. |
| TLS-07 | Media | ✅ Corregido | **Acento faltante en mensaje de fallback**: `"No encontre..."` sin acento hacía fallar `test_sin_match_retorna_fallback` que buscaba `"No encontré"`. → Corregido a `"No encontré un dato estructurado específico para esa pregunta."` |
| TLS-08 | Baja | ✅ Corregido | **`print()` en función de carga de recursos**: `_cargar_recursos()` usaba `print()` en lugar de `logger.info()`, mezclando stdout con el sistema de logging. → Reemplazado por `logger.info(...)`. |
| TLS-09 | Baja | ✅ Corregido | **`STRUCTURED_PATH` hardcodeado**: `Path("data/datos_estructurados.json")` relativo al directorio de trabajo. → Reemplazado por `STRUCTURED_DATA_PATH` importada de `config.py` (usa `Path(__file__).parent`). |
| TLS-10 | Baja | ✅ Corregido | **`_STOPWORDS` recreada en cada llamada**: la constante se definía dentro de la función `datos_estructurados()`. → Elevada a constante de módulo `frozenset`. |

---

### 6. `pyproject.toml` — Dependencias

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| DEP-01 | Media | ✅ Corregido | **Dependencias de scraping mezcladas con la app**. → Separadas en grupos opcionales en `pyproject.toml`: `scraping` (selenium, yt-dlp, trafilatura, etc.), `gradio` (Módulo 1) y `dev` (pytest). La app base instala solo con `uv sync`; los scrapers con `uv sync --extra scraping`. |
| DEP-02 | Baja | ✅ Corregido | `requires-python = ">=3.14"` demasiado restrictivo. → Corregido a `>=3.12`. |
| **DEP-03** | **Alta** | ✅ Corregido | **Python 3.14 incompatible con `torch`**: `torch` no tiene soporte estable para Python 3.14, causando `KeyboardInterrupt` al cargar el modelo de embeddings HuggingFace. → Entorno virtual recreado con Python 3.12 (`uv venv --python 3.12` + `uv sync`). |
| **DEP-04** | **Alta** | ✅ Corregido | **Sin dependencias de persistencia**: el proyecto no tenía soporte para checkpointer en base de datos. → Agregados `langgraph-checkpoint-postgres==3.0.5`, `psycopg==3.3.4`, `psycopg-pool==3.3.1` y `psycopg-binary==3.3.4` via `uv add`. |
| DEP-05 | Baja | ✅ Corregido | **Sin configuración de pytest en `pyproject.toml`**: al ejecutar `pytest` sin argumentos no se localizaban los tests automáticamente en algunos entornos. → Añadido bloque `[tool.pytest.ini_options]` con `testpaths`, `python_files`, `python_classes` y `python_functions`. |

---

### 7. `README.md` — Documentación

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| DOC-01 | Media | ✅ Corregido | **Diagrama de arquitectura en ASCII**. → Reemplazado por diagrama Mermaid. |
| DOC-02 | Baja | ✅ Corregido | **Razonamiento del agente documentado solo en README**. → Ahora visible en tiempo real en la UI. |
| DOC-03 | Baja | ✅ Corregido | **Meta-prompt desactualizado en sección 10.3**. → Actualizado al criterio actual. |
| **DOC-05** | **Media** | ✅ Corregido | **Conteo de chunks desactualizado**: README decía 137 chunks y fuentes incorrectas. → Actualizado a 235 chunks (web 163 + Wikipedia ES 72). YouTube descartado del vectorstore por aportar contenido poco estructurado. Decisión documentada como nota de diseño. |
| **DOC-04** | **Alta** | ✅ Corregido | **README no reflejaba arquitectura de persistencia**: sección 8.2, 9, 12, 13 y 14 describían `MemorySaver` y memoria volátil. → Actualizadas para reflejar `PostgresSaver`, Docker, cookie del `thread_id`, nueva variable `POSTGRES_URI` en `.env`, comando de arranque de Docker y limitaciones reales. |
| DOC-06 | Media | ✅ Corregido | **Nombre de herramienta RAG inconsistente**: sección 10, 11 y tablas de pruebas usaban `base_documental` (nombre anterior) en lugar del nombre real `retrieve_context`. → Reemplazado en todo el documento. |
| DOC-07 | Baja | ✅ Corregido | **Ejemplo de código de `agent.py` en sección 9.1 obsoleto**: mostraba `create_react_agent` y `state_modifier` eliminados en LangGraph V1.0. → Actualizado a `create_agent` + `@dynamic_prompt` con `ModelRequest`. |
| DOC-08 | Baja | ✅ Corregido | **`config.py` ausente en la estructura del repositorio**: sección 13 no listaba `config.py` como archivo clave. → Añadido con descripción. |

---

### 8. `config.py` — Configuración centralizada

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| CFG-03 | Media | ✅ Corregido | **`config.py` incompleto**: solo tenía `EMBEDDING_MODEL`, `VECTORSTORE_PATH` y `RAG_TOP_K`. `MODEL_NAME` y `TEMPERATURE` vivían en `agent.py`; `STRUCTURED_PATH` en `tools.py`; rutas de datos en `chunking.py` y `build_vectorstore.py`. → Añadidos `MODEL_NAME`, `TEMPERATURE`, `POOL_SIZE`, `COOKIE_MAX_AGE`, `ERROR_GENERICO`, `ERROR_RATE_LIMIT`, `DATA_DIR`, `STRUCTURED_DATA_PATH`, `KNOWLEDGE_BASE_PATH`, `KNOWLEDGE_BASE_CLEAN_PATH`. |
| CFG-04 | Media | ✅ Corregido | **Paths relativos frágiles**: `Path("data/...")` se rompía si el proceso se lanzaba desde un directorio distinto al raíz del proyecto. → Todos los paths en `config.py` usan `Path(__file__).parent` como base absoluta. |

---

### 9. `app_v2.py` — Interfaz Streamlit (refactor)

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| APP-01 | Baja | ✅ Corregido | **Centinelas de error duplicados**: `ERROR_GENERICO` y `ERROR_RATE_LIMIT` definidos tanto en `agent.py` como en `app_v2.py`. → Ambos importados desde `config.py`. |
| APP-02 | Baja | ✅ Corregido | **`COOKIE_MAX_AGE` literal hardcodeado**: `max-age=2592000` disperso en dos lugares del código. → Centralizado como `COOKIE_MAX_AGE` en `config.py`. |
| APP-03 | Baja | ✅ Corregido | **Cookie del botón "Nueva conversación" sin `SameSite=Lax`**: la cookie inicial sí lo tenía pero el botón la sobreescribía sin ese atributo. → Unificado mediante helper `_cookie_attr()`. |
| APP-04 | Baja | ✅ Corregido | **Slice frágil `[8:-9]`** para extraer interior de `<script>...</script>`. → Eliminado; el helper `_cookie_attr()` retorna solo el valor del cookie y el `<script>` se construye directamente donde se necesita. |
| APP-05 | Baja | ✅ Corregido | **`logo.png` referenciado con path relativo**: `Path("assets/logo.png")` frágil. → Corregido a `Path(__file__).parent / "assets" / "logo.png"`. |

---

### 10. `chunking.py` y `build_vectorstore.py` — Scripts de construcción

| # | Severidad | Estado | Problema |
|---|-----------|--------|----------|
| BLD-01 | Baja | ✅ Corregido | **Paths hardcodeados en `chunking.py`**: `DATA_DIR = Path("data")` y `OUTPUT_FILE = Path("data/knowledge_base.txt")`. → Importan `DATA_DIR` y `KNOWLEDGE_BASE_PATH` de `config.py`. |
| BLD-02 | Baja | ✅ Corregido | **Path hardcodeado en `build_vectorstore.py`**: `KNOWLEDGE_BASE_PATH = Path("data/knowledge_base_clean.txt")`. → Importa `KNOWLEDGE_BASE_CLEAN_PATH` de `config.py`. |

---

### 11. Infraestructura — Docker + PostgreSQL

| # | Severidad | Estado | Problema / Decisión |
|---|-----------|--------|----------|
| **INF-01** | **Alta** | ✅ Implementado | **Memoria volátil requería solución de persistencia**: el profesor confirmó que se requiere persistencia real en disco. → PostgreSQL `postgres:16` desplegado en Docker con contenedor `colgate-memory` (puerto 5432). URI de conexión en `.env` como `POSTGRES_URI`. `PostgresSaver.setup()` crea las tablas automáticamente. Verificado que el historial sobrevive reinicios completos de la app. |
| **INF-02** | **Media** | ✅ Documentado | **Docker no arranca automáticamente con Windows**: el contenedor debe levantarse manualmente antes de lanzar la app. → Documentado en README sección 12 con comando `docker compose up -d` y advertencia para la demo. |
| INF-03 | Baja | ✅ Corregido | **Healthcheck de `docker-compose.yml` con credenciales hardcodeadas**: `pg_isready -U colgate -d colgate_db` ignoraba las variables de entorno del servicio. → Reemplazado por `pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}`. |
| INF-04 | Baja | ✅ Corregido | **`version: "3.7"` obsoleto en `docker-compose.yml`**: la directiva `version` fue depreciada en Docker Compose V2. → Eliminada. |

---

### 9. `app.py` vs `app_v2.py` — Regresión visual (resuelta)

La versión `app.py` (Gradio) tenía logo, sidebar con CSS corporativo, tipografía Sora y FAQ con tarjetas. `app_v2.py` eliminó todo eso al migrar a Streamlit. Resuelto en commit `d7df437` con branding completo y CSS corporativo.

---

## Historial de cambios

| Commit | Descripción |
|--------|-------------|
| `895a986` | docs: actualizar chunks a 235, descartar YouTube del vectorstore |
| `eae3736` | fix: actualizar cookie al iniciar nueva conversación |
| `8abe852` | fix: actualizar cookie al iniciar nueva conversación |
| `2549eed` | fix: actualizar cookie al iniciar nueva conversación |
| `e343f8d` | docs: actualizar diagrama de arquitectura con PostgresSaver y flujo completo |
| *(pendiente)* | refactor: revisión exhaustiva — API LangGraph V1.0, config centralizada, tests 22/22 |
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
| TLS-03 | Baja | `_cache` fallback silencioso en ejecución CLI sin Streamlit: los recursos se recargan en cada invocación sin advertencia. Impacto bajo (solo afecta ejecuciones de prueba fuera de la app). |
| INF-02 | Media | Docker no arranca automáticamente con Windows — requiere `docker compose up -d` manual antes de cada sesión. |

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
| `data/vectorstore/` | Índice FAISS (235 chunks — web 163 + Wikipedia ES 72) |
| `data/datos_estructurados.json` | Datos de contacto, horarios, sedes, marcas, etc. |
| `app.py` | Versión anterior con Gradio (referencia de estilo) |

## Infraestructura externa

| Componente | Detalle |
|-----------|---------|
| Docker Desktop | Requerido antes de lanzar la app |
| Contenedor | `postgres:16` — puerto 5432 — nombre definido en `.env` |
| Base de datos | credenciales definidas en `.env` (`POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`) |
| Arranque | `docker compose up -d` |
| Primera vez | Ver README sección 12 |
