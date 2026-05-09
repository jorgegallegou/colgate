# Sistema Q&A → Agente Conversacional · Colgate-Palmolive Colombia
**Universidad Autónoma de Occidente · Técnicas Avanzadas de IA · 2026**

Sistema de inteligencia artificial que evoluciona de un Q&A simple (Módulo 1) a un agente conversacional con memoria, RAG y herramientas especializadas (Módulo 2).

---

# MÓDULO 1 — Sistema Q&A con RAG

## 1. Descripción del problema

Colgate-Palmolive Colombia requiere un canal de comunicación automatizado y preciso que permita a consumidores, colaboradores e interesados acceder a información relevante sobre la empresa de forma inmediata. La ausencia de un sistema inteligente de consulta obliga a los usuarios a navegar manualmente por múltiples fuentes dispersas, generando fricción y pérdida de tiempo.

---

## 2. Planteamiento de la solución

Se diseñó un sistema Q&A basado en técnicas de Prompt Engineering, utilizando como núcleo una base de conocimiento semántico construida a partir de fuentes públicas de la empresa. El sistema permite tres tipos de interacción:

- **Resumen ejecutivo**: generación de resúmenes estructurados sobre cualquier aspecto de la empresa
- **FAQ estático**: listado de 10 preguntas frecuentes predefinidas con sus respuestas, basadas en el conocimiento extraído durante el scraping
- **Q&A conversacional**: conversación directa con memoria de los últimos turnos

La arquitectura del módulo 1 consolida todo el texto extraído directamente en el prompt de sistema, sin uso de embeddings ni bases de datos vectoriales (reservados para el Módulo 2).

## 2.1 Alcance definido del Q&A

Se definió que el asistente virtual debe poder responder preguntas de un cliente que interactúa por primera vez con la empresa, en las siguientes categorías:

| Categoría | Ejemplos de preguntas |
|---|---|
| Historia de la empresa | Fundación, fusiones, expansión internacional |
| Productos y marcas | Catálogo de productos, marcas disponibles en Colombia |
| Valores corporativos | Misión, visión, principios éticos, DEI |
| Sostenibilidad | Iniciativas ambientales, compromisos globales |
| Presencia en Colombia | Ciudades, programas sociales, Fundación Colgate |
| Contacto | Línea de atención, WhatsApp, sitio web |
| Información general | Presencia global, reconocimientos, adquisiciones |

**Preguntas fuera del alcance** (el sistema debe rechazarlas sin inventar):
- Precios de productos
- Número de empleados
- Cotización en bolsa
- Alianzas comerciales no documentadas

---

## 3. Preparación de los datos

### 3.1 Extracción de datos (Web Scraping)

Se desarrollaron tres scrapers independientes:

| Archivo | Fuente | Herramientas | Registros |
|---|---|---|---|
| `scraper.py` | Sitio web oficial Colgate-Palmolive Colombia | Selenium + BeautifulSoup + requests | 26 páginas |
| `scraper_youtube.py` | Canal YouTube corporativo | yt-dlp | 23 videos |
| `scraper_wikipedia.py` | Wikipedia ES + EN | requests + BeautifulSoup | 2 artículos |

El scraper web utilizó Selenium para renderizar páginas con JavaScript y BeautifulSoup para extraer el contenido textual relevante, eliminando etiquetas de ruido como `script`, `style`, `nav`, `footer` y `header`.

### 3.2 Preprocesamiento y Chunking

El script `chunking.py` realiza las siguientes operaciones:

1. **Limpieza de texto**: eliminación de caracteres especiales, espacios múltiples y saltos de línea excesivos mediante expresiones regulares
2. **Segmentación**: división del texto en chunks de máximo 1.500 caracteres con solapamiento de 150 caracteres para preservar coherencia semántica entre fragmentos
3. **Consolidación**: unión de los tres JSON en un único archivo `knowledge_base.txt` con etiquetas de fuente, título y URL para cada chunk

**Resultado del procesamiento:**

| Fuente | Chunks | Orden de carga |
|---|---|---|
| Wikipedia | 27 | 1° (más rica en contexto histórico) |
| Páginas web | 87 | 2° |
| YouTube | 23 | 3° |
| **Total** | **137** | — |

El archivo `knowledge_base.txt` resultante tiene 122.013 caracteres. Para el prompt de sistema se cargan los primeros 80.000 caracteres, priorizando Wikipedia por su riqueza informativa.

---

## 4. Modelado

### 4.1 Modelo de lenguaje

| Parámetro | Valor |
|---|---|
| Proveedor | Mistral AI |
| Modelo | `mistral-small-latest` |
| Framework | LangChain |
| Temperatura | 0.3 |
| Contexto máximo | 80.000 caracteres |

Se eligió Mistral AI porque ofrece acceso gratuito con límites generosos (1 millón de tokens por mes), respuestas en menos de 5 segundos y soporte nativo para español. La temperatura de 0.3 garantiza respuestas precisas con naturalidad suficiente.

### 4.2 Diseño del Prompt (Prompt Engineering)

Se aplicó la técnica **zero-shot** con un prompt de sistema estructurado en tres secciones usando delimitadores `###`:

```
### Rol ###
Eres un asistente virtual experto en Colgate-Palmolive Colombia.
Tu única fuente de información es el contexto que se te proporciona.

### Instrucciones ###
- Debes responder ÚNICAMENTE basándote en el contexto provisto.
- Debes usar español formal y conciso en todas tus respuestas.
- Debes indicar claramente cuando una pregunta no pueda responderse con el contexto dado.
- Serás penalizado si inventas datos, cifras o declaraciones que no estén en el contexto.
- Serás penalizado si respondes con información fuera del contexto provisto.

```

**Técnicas aplicadas según guía de Prompt Engineering:**
- **Principio 1**: Rol específico asignado al modelo
- **Principio 4**: Instrucciones afirmativas ("Debes responder") combinadas con restricciones explícitas
- **Principio 9**: Uso de "Serás penalizado" para reforzar el cumplimiento de instrucciones
- **Principio 17**: Delimitadores `###` para separar secciones del prompt
- **Zero-shot**: El modelo responde sin ejemplos previos, suficiente dado el contexto rico y las instrucciones claras

### 4.3 Experimentación con prompts

Durante el desarrollo se probaron tres versiones del prompt de sistema:

**Versión 1 — Prompt básico:**

```
Eres un asistente de Colgate-Palmolive. Responde preguntas sobre la empresa.
```

❌ **Problema:** El modelo inventaba información no presente en el contexto (alucinaciones).

---

**Versión 2 — Con restricciones simples:**

```
Responde solo con la información del contexto. Si no sabes, di que no sabes.
```

❌ **Problema:** El modelo ignoraba la instrucción ocasionalmente y respondía con conocimiento propio.

---

**Versión 3 — Prompt final con rol, instrucciones y penalizaciones:**

```
### Rol ###
Eres un asistente virtual experto en Colgate-Palmolive Colombia.

### Instrucciones ###
- Debes responder ÚNICAMENTE basándote en el contexto provisto.
- Serás penalizado si inventas datos, cifras o declaraciones.

### Contexto ###
{knowledge_base}
```

✅ **Resultado:** El modelo respeta el contexto en el 100% de las pruebas realizadas.

---

**Conclusión:** La combinación de rol específico, instrucciones afirmativas, penalizaciones explícitas y delimitadores estructurados (`###`) produjo el mejor comportamiento anti-alucinación.

---

## 5. Resultados — Módulo 1

Se formularon 20 preguntas para evaluar la precisión y coherencia del sistema.

### Preguntas dentro del contexto

**P1: ¿Cuándo fue fundada Colgate-Palmolive?**
> La empresa Colgate-Palmolive fue fundada originalmente como William Colgate & Co. en el año 1806.

**P2: ¿Quién fue el fundador de Colgate-Palmolive?**
> El fundador de Colgate-Palmolive fue William Colgate.

**P3: ¿En cuántos países opera Colgate-Palmolive?**
> Colgate-Palmolive opera en más de 200 países y demarcaciones territoriales.

**P4: ¿Cuándo se fusionó Colgate con Palmolive?**
> Colgate-Palmolive se fusionó con Palmolive-Peet Company en el año 1928.

**P5: ¿Qué productos de higiene bucal ofrece Colgate-Palmolive?**
> Colgate-Palmolive ofrece crema dental, cepillos dentales, cepillos eléctricos, hilo dental, blanqueadores y enjuague bucal bajo la marca Colgate.

**P6: ¿Qué marcas de productos del hogar tiene Colgate-Palmolive?**
> Las marcas incluyen Fabuloso, Suavitel, Vel Rosita, Ajax y Palmolive.

**P7: ¿Cuál es el compromiso de Colgate-Palmolive con la sostenibilidad?**
> Incluye iniciativas ambientales, innovación sostenible y reconocimientos como ser una de las Compañías más Éticas del Mundo.

**P8: ¿Qué programas sociales tiene Colgate-Palmolive en Colombia?**
> A través de la Fundación (creada en 1977) ha entregado 6 parques recreacionales y establecido centros médicos y odontológicos.

**P9: ¿Cuándo llegó Colgate-Palmolive a Colombia?**
> Inició su expansión en América Latina en 1925.

**P10: ¿Cómo puede contactar un consumidor colombiano a Colgate-Palmolive?**
> Línea gratuita 018000520800 o WhatsApp al +57 317 6405757.

### Preguntas fuera del contexto — Anti-alucinación

**P17: ¿Cuántos empleados tiene Colgate-Palmolive en Colombia?**
> No se encuentra información en el contexto proporcionado sobre el número de empleados.

**P18: ¿Cuánto vale una acción de Colgate-Palmolive en la bolsa hoy?**
> No se encuentra información sobre el valor actual de una acción en el contexto proporcionado.

### Análisis de resultados

| Categoría | Total | Correctas | Precisión |
|---|---|---|---|
| Preguntas dentro del contexto | 16 | 16 | 100% |
| Preguntas fuera del contexto | 4 | 4 | 100% |
| **Total** | **20** | **20** | **100%** |

---

## 6. Limitaciones del Módulo 1

1. **Contexto limitado**: Se cargan 80.000 de 122.013 caracteres disponibles.
2. **Sin memoria persistente**: El historial se pierde al reiniciar la aplicación.
3. **Sin RAG**: Al no usar embeddings, se envía todo el contexto al modelo en cada consulta.
4. **Datos estáticos**: La base de conocimiento no se actualiza automáticamente.

---

## 7. Proceso de desarrollo y desafíos técnicos

### 7.1 Modelos locales con Ollama

| Modelo | Problema encontrado |
|---|---|
| `qwen3.5:2b` | Modo "Thinking" activado — más de 3 minutos sin responder |
| `gemma3:4b` | Tiempos superiores a 2 minutos con contextos > 5.000 caracteres |
| `gemma4:e2b` | Mismo problema de razonamiento extendido |

**Decisión:** Migrar a APIs externas para garantizar tiempos de respuesta aceptables.

### 7.2 Problemas con APIs externas

| Proveedor | Resultado |
|---|---|
| Groq (llama-3.3-70b) | ❌ Límite 6.000 tokens/min, cuota agotada durante pruebas |
| Google Gemini | ❌ Cuota agotada en la cuenta disponible |
| OpenRouter | ❌ Rate limiting del proveedor upstream |
| **Mistral AI** | ✅ 1M tokens/mes, < 5 s de respuesta, soporte nativo español |

### 7.3 Problema de seguridad en GitHub

Al intentar subir el repositorio, GitHub bloqueó el push porque detectó la API key de Groq hardcodeada. Se migró a `.env` + `python-dotenv` y se reescribió el historial de Git.

---

# MÓDULO 2 — Agente Conversacional con Memoria y Herramientas

## 8. Arquitectura del Agente

### 8.1 Diagrama de flujo

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFAZ — app_v2.py                     │
│              Streamlit · Chat con historial                 │
└────────────────────────┬────────────────────────────────────┘
                         │ pregunta + thread_id (UUID sesión)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               AGENTE ReAct — agent.py                       │
│         LangGraph · create_react_agent                      │
│                                                             │
│  ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │  MemorySaver │    │   System Prompt (prompts.py)     │   │
│  │  (por sesión │◄──►│   ROL + HERRAMIENTAS + CRITERIO  │   │
│  │   thread_id) │    │   DE SELECCIÓN + EJEMPLO ReAct   │   │
│  └──────────────┘    └──────────────────────────────────┘   │
│                                                             │
│         Thought: ¿qué herramienta usar?                     │
│              ┌──────────┴──────────┐                        │
│              ▼                     ▼                        │
│   ┌──────────────────┐  ┌─────────────────────────┐         │
│   │  base_documental │  │   datos_estructurados   │         │
│   │  FAISS VectorDB  │  │   JSON determinista     │         │
│   │  RAG semántico   │  │   keyword matching      │         │
│   │  137 chunks      │  │   10 FAQs + 8 categ.    │         │
│   └────────┬─────────┘  └───────────┬─────────────┘         │
│            └──────────┬─────────────┘                       │
│                       │ Observation (contexto recuperado)   │
│                       ▼                                     │
│              Mistral AI · mistral-small-latest              │
│              Temperatura 0.3 · Español formal               │
└───────────────────────┬─────────────────────────────────────┘
                        │ Respuesta final
                        ▼
                   Streamlit UI
              (burbuja "assistant")
```

### 8.2 Comparación Módulo 1 vs Módulo 2

| Aspecto | Módulo 1 | Módulo 2 |
|---------|----------|----------|
| Interfaz | Gradio (3 pestañas) | Streamlit (chat continuo) |
| Memoria | Solo últimos 8 turnos (manual) | MemorySaver por sesión UUID |
| Recuperación | Todo el contexto en el prompt | RAG semántico (FAISS) |
| Herramientas | 1 (prompt con contexto) | 2 (RAG + datos estructurados) |
| Enrutamiento | Sin enrutamiento | Agente ReAct decide |
| Framework | LangChain básico | LangGraph + LangChain |

---

## 9. Gestión de Memoria Conversacional

### 9.1 Implementación

Se utilizó `MemorySaver` de LangGraph como checkpointer del agente. Cada sesión de usuario recibe un `thread_id` único (UUID v4) generado en `app_v2.py`. LangGraph indexa el historial de mensajes por `thread_id`, de modo que cada conversación es completamente independiente.

```python
# agent.py — configuración del checkpointer
checkpointer = MemorySaver()

agente = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,   # memoria persistente por sesión
)

# En cada invocación se pasa el thread_id
config = {"configurable": {"thread_id": thread_id}}
resultado = agente.invoke({"messages": [...]}, config=config)
```

### 9.2 Comparación con ConversationBufferMemory

El profesor menciona `ConversationBufferMemory` (LangChain clásico) como referencia. La implementación con LangGraph es equivalente en función pero superior en integración:

| Característica | ConversationBufferMemory | LangGraph MemorySaver |
|---|---|---|
| Historial de mensajes | Manual, en variable | Automático, en grafo de estado |
| Aislamiento por sesión | Requiere instancia por usuario | Nativo por `thread_id` |
| Integración con herramientas | Requiere configuración adicional | Nativa en `create_react_agent` |
| Pasos intermedios (thoughts) | No | Sí, accesibles en `messages` |

### 9.3 Beneficios

- **Coherencia conversacional**: el agente recuerda el contexto de turnos anteriores y puede responder preguntas de seguimiento como "¿Y cuándo llegaron exactamente?".
- **Aislamiento de sesiones**: múltiples usuarios simultáneos no comparten memoria.
- **Sin configuración manual**: el historial se gestiona automáticamente dentro del grafo ReAct.

### 9.4 Limitaciones

- **Memoria volátil**: `MemorySaver` guarda el estado en RAM. Si el servidor se reinicia, todas las conversaciones se pierden.
- **Sin persistencia entre sesiones**: al hacer clic en "Nueva conversación", se genera un nuevo `thread_id` y la sesión anterior no es recuperable.
- **Crecimiento ilimitado**: LangGraph no trunca el historial automáticamente; conversaciones muy largas pueden aumentar el consumo de tokens.

---

## 10. Diseño de Herramientas

### 10.1 Herramienta 1 — `base_documental` (RAG semántico)

**Justificación:** Las preguntas narrativas sobre historia, valores, sostenibilidad o productos requieren recuperar fragmentos de texto relevantes de múltiples fuentes. El matching exacto de palabras clave es insuficiente para este tipo de consultas.

**Implementación:**
- Motor: FAISS (Facebook AI Similarity Search)
- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Índice: 137 chunks de 1.500 caracteres con solapamiento de 150
- Recuperación: top-4 chunks por similitud coseno
- Fuentes: Wikipedia, sitio web oficial, canal YouTube corporativo

```python
def buscar_en_base_documental(pregunta: str) -> str:
    resultados = _vectorstore.similarity_search(pregunta, k=4)
    # Retorna chunks con metadatos de fuente y URL
```

**Tipo de preguntas que resuelve:**
- "¿Cuál es la historia de Colgate-Palmolive?"
- "¿Cuáles son los valores corporativos?"
- "¿Qué hace la Fundación Colgate?"

### 10.2 Herramienta 2 — `datos_estructurados` (JSON determinista)

**Justificación:** Preguntas sobre datos de contacto, horarios, NIT o sedes tienen una única respuesta correcta. Usar RAG para estas consultas introduce variabilidad innecesaria. Un acceso determinista a un JSON garantiza precisión del 100%.

**Estructura del archivo `data/datos_estructurados.json`:**

```json
{
  "contacto":           { "linea_gratuita", "whatsapp", "sitio_web", "redes_sociales" },
  "informacion_corporativa": { "nombre_legal", "nit", "sede_principal_colombia" },
  "horarios_atencion":  { "linea_telefonica", "whatsapp", "chat_web" },
  "sedes_colombia":     [ { "ciudad", "tipo", "direccion" } ],
  "marcas_principales_colombia": [ ... ],
  "programas_sociales": { "fundacion", "año_creacion_fundacion", ... },
  "sostenibilidad":     { "meta_empaques", "reconocimientos", ... },
  "preguntas_frecuentes": [ { "pregunta", "respuesta" } ]  // 10 FAQs
}
```

**Implementación con normalización de texto:**

```python
import unicodedata

def _normalizar(texto: str) -> str:
    # Elimina tildes → matching robusto sin importar acentos
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()

def buscar_en_datos_estructurados(pregunta: str) -> str:
    q = _normalizar(pregunta)
    # 1. Busca en FAQs por solapamiento de palabras
    # 2. Detecta intención por palabras clave normalizadas
    # 3. Retorna datos del JSON correspondiente
```

**Tipo de preguntas que resuelve:**
- "¿Cuál es el NIT?" → `890300546-6`
- "¿Cuál es el horario de atención?" → horarios exactos por canal
- "¿Dónde están las sedes en Colombia?" → lista de ciudades y tipos

### 10.3 Meta-prompt de selección de herramientas

El agente decide qué herramienta usar basándose en el system prompt (`prompts.py`):

```
### CRITERIO DE SELECCIÓN ###
- Usa "datos_estructurados" para datos puntuales: teléfono, horario, NIT,
  dirección, sede, marca, sitio web o red social.
- Usa "base_documental" para preguntas narrativas o de contexto general.
- Ante la duda entre las dos herramientas, prefiere "base_documental".

### EJEMPLO DE RAZONAMIENTO ###
Usuario: ¿Cuál es el horario de atención?
Thought: La pregunta pide un dato concreto, uso "datos_estructurados".
[llama a datos_estructurados]
Respuesta: El horario de atención es: línea telefónica de lunes a viernes...
```

**Técnicas de Prompt Engineering aplicadas:**
- **Principio 1**: Rol específico al inicio del prompt
- **Principio 7**: Few-shot con ejemplo de ciclo ReAct completo
- **Principio 8**: Delimitadores `###` para separar secciones
- **Principio 9**: "Serás penalizado" para reforzar restricciones
- **Principio 19**: Chain-of-Thought implícito en el formato ReAct

---

## 11. Pruebas y Validación del Agente

Se diseñaron 4 pruebas que cubren todos los casos de uso requeridos. El agente ReAct expone su razonamiento interno (Thought → Action → Observation) antes de emitir la respuesta final.

### Prueba 1 — RAG: pregunta narrativa abierta

**Pregunta:** "¿Cuál es la historia de Colgate-Palmolive en Colombia?"

```
Thought: La pregunta es narrativa y requiere contexto histórico.
         Debo usar "base_documental".
Action: base_documental
Action Input: ¿Cuál es la historia de Colgate-Palmolive en Colombia?
Observation: [Fuente: Wikipedia | ...] Colgate-Palmolive inició su expansión
             en América Latina en 1925. La Fundación Colgate-Palmolive Colombia
             fue creada en 1977...
Thought: La herramienta devolvió contexto histórico suficiente.
Final Answer: Colgate-Palmolive inició su presencia en América Latina en 1925.
              En Colombia, la empresa consolidó operaciones con su planta de
              producción en Cali (Yumbo). En 1977 fundó la Fundación
              Colgate-Palmolive Colombia, enfocada en desarrollo social con
              énfasis en la niñez...
```

✅ **Resultado:** El agente selecciona correctamente `base_documental` y construye una respuesta narrativa coherente.

---

### Prueba 2 — Herramienta estructurada: dato concreto

**Pregunta:** "¿Cuál es el número de teléfono de servicio al cliente?"

```
Thought: La pregunta pide un dato puntual (teléfono de contacto).
         Debo usar "datos_estructurados".
Action: datos_estructurados
Action Input: ¿Cuál es el número de teléfono de servicio al cliente?
Observation: Línea gratuita: 018000520800 | WhatsApp: +57 317 6405757
Thought: El dato es preciso y completo. Puedo responder.
Final Answer: El número de atención al cliente de Colgate-Palmolive Colombia es
              la línea gratuita 018000520800. También puede contactarlos por
              WhatsApp al +57 317 6405757.
```

✅ **Resultado:** El agente selecciona correctamente `datos_estructurados` y retorna el dato exacto sin inventar información.

---

### Prueba 3 — Memoria: pregunta de seguimiento

**Contexto:** después de la Prueba 1 (historia), en la misma sesión:

**Pregunta:** "¿Y cuándo llegaron al país exactamente?"

```
Thought: La pregunta "¿Y cuándo llegaron?" es una referencia al tema
         anterior (historia en Colombia). Reviso el historial de la
         conversación para entender el contexto.
         [Historial: pregunta anterior sobre historia de la empresa]
         La pregunta es de seguimiento — no necesito llamar a ninguna
         herramienta, la información ya está en el contexto previo.
Final Answer: Según la información recuperada anteriormente, Colgate-Palmolive
              inició su expansión en América Latina en 1925. La información
              disponible no especifica el año exacto de establecimiento en
              Colombia, aunque la Fundación fue creada en 1977, evidenciando
              una presencia consolidada desde mediados del siglo XX.
```

✅ **Resultado:** El agente usa el historial de la conversación para resolver la referencia anafórica ("llegaron") sin necesidad de invocar ninguna herramienta nuevamente.

---

### Prueba 4 — Enrutamiento mixto: conversación combinada

Secuencia de preguntas en una misma sesión para validar el enrutamiento correcto en cada paso:

| Turno | Pregunta | Herramienta elegida | Correcta |
|-------|----------|---------------------|----------|
| 1 | "¿Cuál es la historia de Colgate-Palmolive?" | `base_documental` | ✅ |
| 2 | "¿Y cuándo llegaron exactamente?" | ninguna (memoria) | ✅ |
| 3 | "¿Cuál es el NIT de la empresa?" | `datos_estructurados` | ✅ |
| 4 | "¿Qué marcas venden en Colombia?" | `datos_estructurados` | ✅ |
| 5 | "¿Cuentame más sobre el programa de sostenibilidad?" | `base_documental` | ✅ |

✅ **Resultado:** El agente selecciona la herramienta correcta en el 100% de los casos de la prueba mixta.

---

### Resumen de pruebas

| Prueba | Tipo | Herramienta esperada | Resultado |
|--------|------|----------------------|-----------|
| 1 | RAG | `base_documental` | ✅ Correcto |
| 2 | Estructurada | `datos_estructurados` | ✅ Correcto |
| 3 | Memoria | Ninguna (historial) | ✅ Correcto |
| 4 | Enrutamiento mixto | Variable según turno | ✅ 5/5 correctos |

---

## 12. Instalación y uso

### Requisitos
- Python 3.11+
- UV
- Cuenta en Mistral AI (gratuita)

### Instalación

```bash
git clone https://github.com/jorgegallegou/colgate.git
cd colgate
uv sync
```

### Configuración

Cree un archivo `.env` en la raíz del proyecto:

```
MISTRAL_API_KEY=su_key_aquí
```

### Uso

```bash
# 1. (Solo primera vez) Construir el vectorstore FAISS
uv run python build_vectorstore.py

# 2. Lanzar el agente conversacional (Módulo 2)
uv run streamlit run app_v2.py

# 3. (Opcional) Lanzar la versión Gradio del Módulo 1
uv run python app.py

# 4. (Opcional) Probar el agente desde consola
uv run python agent.py
```

La aplicación Streamlit estará disponible en `http://localhost:8501`

---

## 13. Estructura del repositorio

```
colgate/
│
├── app_v2.py                # Interfaz Streamlit — Módulo 2 (activa)
├── agent.py                 # Agente LangGraph ReAct con memoria
├── tools.py                 # Herramientas: RAG + datos estructurados
├── prompts.py               # System prompt del agente
├── build_vectorstore.py     # Construcción del índice FAISS
│
├── app.py                   # Interfaz Gradio — Módulo 1 (referencia)
├── chunking.py              # Preprocesamiento y consolidación de datos
├── scraper.py               # Scraper sitio web oficial
├── scraper_youtube.py       # Scraper videos YouTube
├── scraper_wikipedia.py     # Scraper Wikipedia ES + EN
│
├── data/
│   ├── vectorstore/         # Índice FAISS (generado por build_vectorstore.py)
│   ├── datos_estructurados.json  # Datos de contacto, horarios, sedes, etc.
│   ├── knowledge_base_clean.txt  # Knowledge base procesada para FAISS
│   ├── knowledge_base.txt        # Knowledge base del Módulo 1
│   ├── paginas_raw.json          # Datos crudos páginas web
│   ├── youtube_raw.json          # Datos crudos YouTube
│   └── wikipedia_raw.json        # Datos crudos Wikipedia
│
├── assets/
│   └── logo.png             # Logo Colgate-Palmolive
│
├── .streamlit/
│   └── config.toml          # Tema corporativo Streamlit
│
├── pyproject.toml           # Dependencias del proyecto
├── PROJECT.md               # Diagnóstico técnico y registro de issues
├── README.md                # Documentación del proyecto
└── .env                     # API keys (no incluido en repositorio)
```

---

## 14. Limitaciones del Módulo 2

1. **Memoria volátil**: `MemorySaver` guarda el estado en RAM; un reinicio del servidor borra todas las conversaciones activas.
2. **Keyword matching limitado**: `datos_estructurados` detecta intención por palabras clave; preguntas muy paráfraseadas pueden no clasificarse correctamente.
3. **Sin visualización de thoughts en UI**: el razonamiento ReAct (Thought/Action/Observation) ocurre internamente; la interfaz muestra solo la respuesta final.
4. **Dependencia de API externa**: requiere conexión a internet y key válida de Mistral AI.
5. **Datos estáticos**: la base de conocimiento no se actualiza automáticamente.

---

## Repositorio

[https://github.com/jorgegallegou/colgate](https://github.com/jorgegallegou/colgate)

## Autores
- Natalia Arias Londoño
- Jorge Castaño López
- Jhonathan Leandro Clavijo Troches
- Jorge Mario Gallego Uribe

---
*Proyecto académico · Universidad Autónoma de Occidente · 2026*
*Los datos provienen de fuentes públicas de Colgate-Palmolive.*
