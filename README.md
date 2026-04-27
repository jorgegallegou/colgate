# Sistema Q&A de Colgate Palmolive
**Universidad Autónoma de Occidente · Taller 1 · Técnicas avanzadas de IA**

Sistema de preguntas y respuestas (Q&A) basado en inteligencia artificial, construido como base de conocimiento semántico para un futuro chatbot corporativo de Colgate-Palmolive Colombia.

---

## 1. Descripción del problema

Colgate-Palmolive Colombia requiere un canal de comunicación automatizado y preciso que permita a consumidores, colaboradores e interesados acceder a información relevante sobre la empresa de forma inmediata. La ausencia de un sistema inteligente de consulta obliga a los usuarios a navegar manualmente por múltiples fuentes dispersas, generando fricción y pérdida de tiempo.

---

## 2. Planteamiento de la solución

Se diseñó un sistema Q&A basado en técnicas de Prompt Engineering, utilizando como núcleo una base de conocimiento semántico construida a partir de fuentes públicas de la empresa. El sistema permite tres tipos de interacción:

- **Resumen ejecutivo**: generación de resúmenes estructurados sobre cualquier aspecto de la empresa
- **FAQ**: generación automática de preguntas frecuentes con respuestas basadas en el contexto
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
| `scraper.py` | Sitio web oficial Colgate-Palmolive Colombia | Selenium + BeautifulSoup + requests | 14 páginas |
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
| Páginas web | 55 | 2° |
| YouTube | 23 | 3° |
| **Total** | **105** | — |

El archivo `knowledge_base.txt` resultante tiene 105.607 caracteres. Para el prompt de sistema se cargan los primeros 50.000 caracteres, priorizando Wikipedia por su riqueza informativa.

---

## 4. Modelado

### 4.1 Modelo de lenguaje

| Parámetro | Valor |
|---|---|
| Proveedor | Mistral AI |
| Modelo | `mistral-small-latest` |
| Framework | LangChain |
| Temperatura | 0.3 |
| Contexto máximo | 50.000 caracteres |

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

### 4.4 Nota sobre el Módulo 2

Para el Módulo 2 se implementará:
- **Modelo de embedding**: `nomic-embed-text` o `text-embedding-3-small`
- **Base de datos vectorial**: ChromaDB
- **Arquitectura RAG**: recuperación semántica de chunks relevantes en lugar de enviar todo el contexto

---

## 5. Resultados

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
> Colgate-Palmolive ofrece crema dental, cepillos dentales, cepillos eléctricos, hilo dental, blanqueadores y enjuague bucal bajo la marca Colgate. En otros mercados también comercializa Dentagard y Cherish.

**P6: ¿Qué marcas de productos del hogar tiene Colgate-Palmolive?**
> Las marcas de productos para el hogar incluyen Fabuloso (limpiadores multiusos), Suavitel y Vel Rosita (suavizantes de ropa), Ajax (limpiadores) y Palmolive. Algunas marcas como Alert, Caprice y Wildroot fueron vendidas a Genomma Lab Internacional.

**P7: ¿Cuál es el compromiso de Colgate-Palmolive con la sostenibilidad?**
> El compromiso incluye iniciativas ambientales para preservar el medio ambiente, innovación sostenible, objetivos globales de salud y reconocimientos como ser una de las Compañías más Éticas del Mundo y obtener 100 puntos en el Índice de Equidad Corporativa.

**P8: ¿Qué programas sociales tiene Colgate-Palmolive en Colombia?**
> A través de la Fundación Colgate-Palmolive (creada en 1977), la empresa ha entregado 6 parques recreacionales en Cali, Popayán, Medellín, Bogotá y Cartagena, donado viviendas tras desastres naturales y establecido centros médicos y odontológicos en varias ciudades del país.

**P9: ¿Cuándo llegó Colgate-Palmolive a Colombia?**
> Colgate-Palmolive inició su expansión en América Latina en 1925, aunque el contexto no especifica la fecha exacta de establecimiento en Colombia.

**P10: ¿Dónde están ubicadas las instalaciones de Colgate-Palmolive en Colombia?**
> El contexto no especifica la ubicación exacta de las instalaciones, aunque menciona operaciones en Cali, Cartagena, Bucaramanga, Bogotá y Pereira a través de sus centros médicos y odontológicos.

**P11: ¿Cómo puede contactar un consumidor colombiano a Colgate-Palmolive?**
> A través del sitio web https://www.colgatepalmolive.com.co/contact-us, la línea gratuita 018000520800 o WhatsApp al +57 317 6405757.

**P12: ¿Cuáles son los valores corporativos de Colgate-Palmolive? (FAQ)**
> Los valores incluyen: empatía, respeto y gratitud; integridad; generosidad; confianza; pertenencia e inclusión; innovación y audacia; y compromiso con la equidad.

**P13: Resumen sobre historia de Colgate-Palmolive**
> Resumen completo desde 1806 hasta la actualidad, incluyendo fundación, innovaciones en productos, expansión internacional, fusiones y adquisiciones, y programas sociales.

**P14: Resumen sobre productos de cuidado personal**
> Resumen detallado de marcas y productos en higiene bucal, cuidado del cabello, cuidado de la piel, desodorantes y productos para bebé.

**P15: FAQ sobre presencia de Colgate-Palmolive en Colombia**
> Cinco preguntas sobre llegada al país, marcas disponibles, responsabilidad social, manejo de productos problemáticos y sostenibilidad.

**P16: ¿Qué significa "crear un futuro por el que valga la pena sonreír"?**
> Para Colgate-Palmolive significa construir un futuro más saludable para las personas, las comunidades y el planeta, mejorando el bienestar físico, fomentando la equidad y preservando el medio ambiente.

### Preguntas fuera del contexto — Anti-alucinación

**P17: ¿Cuántos empleados tiene Colgate-Palmolive en Colombia?**
> No se encuentra información en el contexto proporcionado sobre el número de empleados.

**P18: ¿Cuánto vale una acción de Colgate-Palmolive en la bolsa hoy?**
> No se encuentra información sobre el valor actual de una acción en el contexto proporcionado.

**P19: ¿Es Colgate aliado de Coca-Cola?**
> No se encuentra información en el contexto proporcionado sobre una alianza entre Colgate-Palmolive y Coca-Cola.

**P20: ¿Es verdad que COLGATE significa colosenses, gálatas, tesalonicenses?**
> No se encuentra información en el contexto que relacione la palabra COLGATE con esos términos.

### Análisis de resultados

| Categoría | Total | Correctas | Precisión |
|---|---|---|---|
| Preguntas dentro del contexto | 16 | 16 | 100% |
| Preguntas fuera del contexto | 4 | 4 | 100% |
| **Total** | **20** | **20** | **100%** |

El sistema demostró alta precisión en la recuperación de información y efectividad en la prevención de alucinaciones. Las respuestas fuera del contexto fueron rechazadas correctamente sin inventar información.

---

## 6. Instalación y uso

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
# 1. Generar knowledge base
uv run python chunking.py

# 2. Lanzar aplicación
uv run python app.py
```

La aplicación estará disponible en `http://localhost:7860`

---

## 7. Estructura del repositorio

```
colgate/
├── app.py                   # Aplicación principal Gradio + LangChain
├── chunking.py              # Preprocesamiento y consolidación de datos
├── scraper.py               # Scraper sitio web oficial
├── scraper_youtube.py       # Scraper videos YouTube
├── scraper_wikipedia.py     # Scraper Wikipedia ES + EN
├── pyproject.toml           # Dependencias del proyecto
├── README.md                # Documentación del proyecto
├── .gitignore               # Archivos excluidos del repositorio
├── data/
│   ├── paginas_raw.json     # Datos crudos páginas web
│   ├── youtube_raw.json     # Datos crudos YouTube
│   ├── wikipedia_raw.json   # Datos crudos Wikipedia
│   └── knowledge_base.txt   # Base de conocimiento consolidada
└── .env                     # API keys (no incluido en repositorio)
```

---

## 8. Limitaciones del sistema

1. **Contexto limitado**: Se cargan 50.000 de 105.607 caracteres disponibles. Preguntas sobre temas en los últimos chunks pueden no responderse correctamente.
2. **Sin memoria persistente**: El historial de conversación se pierde al reiniciar la aplicación.
3. **Dependencia de API externa**: El sistema requiere conexión a internet y una key válida de Mistral AI.
4. **Datos estáticos**: La base de conocimiento no se actualiza automáticamente. Requiere ejecutar nuevamente los scrapers y `chunking.py`.
5. **Sin validación de idioma**: El sistema puede responder en inglés si el contexto de Wikipedia EN tiene mayor relevancia para la pregunta.
6. **Módulo 1 sin RAG**: Al no usar embeddings ni búsqueda semántica, el sistema no puede recuperar chunks específicos — envía todo el contexto al modelo.

## 9. Proceso de desarrollo y desafíos técnicos

Durante el desarrollo se encontraron múltiples desafíos técnicos que obligaron a tomar decisiones de arquitectura progresivas.

### 9.1 Modelos locales con Ollama

Se intentó inicialmente usar modelos locales a través de Ollama para evitar dependencias externas:

| Modelo | Problema encontrado |
|---|---|
| `qwen3.5:2b` | Modo "Thinking" activado por defecto — el modelo razonaba internamente durante más de 3 minutos sin responder |
| `gemma3:4b` | Tiempos de respuesta superiores a 2 minutos con contextos mayores a 5.000 caracteres |
| `gemma4:e2b` | Mismo problema de modo "Thinking" — respuesta después de 60 segundos |

**Causa raíz:** Los modelos locales disponibles tenían activado el modo de razonamiento extendido, incompatible con contextos largos en el hardware disponible (Windows 11, sin GPU dedicada).

**Decisión:** Migrar a APIs externas para garantizar tiempos de respuesta aceptables.

### 9.2 Problemas con APIs externas

Se probaron múltiples proveedores antes de encontrar una solución estable:

**Groq (llama-3.3-70b-versatile)**
- ✅ Respuestas rápidas (3-5 segundos)
- ❌ Límite de 6.000 tokens por minuto en plan gratuito
- ❌ Límite de 100.000 tokens por día — agotado durante las pruebas
- ❌ Contexto máximo funcional: 12.000 caracteres (3.000 tokens)

**Google Gemini (gemini-2.0-flash)**
- ❌ Cuota del plan gratuito agotada en la cuenta disponible
- ❌ Modelo `gemini-1.5-flash` no disponible en la versión de API utilizada

**OpenRouter (meta-llama/llama-3.3-70b-instruct:free)**
- ❌ Rate limiting temporal del proveedor upstream (Venice)
- ❌ Modelo `google/gemma-3-27b-it:free` también con rate limiting

**Mistral AI (mistral-small-latest)**
- ✅ 1 millón de tokens por mes en plan gratuito
- ✅ Respuestas en menos de 5 segundos
- ✅ Soporte nativo para español
- ✅ Contexto de 50.000 caracteres sin errores
- ✅ Sin problemas de rate limiting durante las pruebas

**Decisión final:** Mistral AI como proveedor definitivo por estabilidad, generosidad del plan gratuito y calidad de respuestas.

### 9.3 Problemas con el contexto

El tamaño del knowledge base (105.607 caracteres) presentó desafíos al cargarse en el prompt:

| Caracteres cargados | Resultado |
|---|---|
| 91.000 | Modelo ignoraba el contexto completamente |
| 50.000 | Groq: error 413 (demasiados tokens) |
| 25.000 | Groq: funcional pero agotaba cuota rápidamente |
| 50.000 | Mistral: funcional y estable |

**Solución:** Reorganizar el `knowledge_base.txt` para que Wikipedia (fuente más rica) quedara primero, garantizando que los primeros 50.000 caracteres cargados contuvieran la información más relevante.

### 9.4 Problemas con Gradio 6.0

La versión instalada de Gradio (6.0) introdujo cambios incompatibles con el código generado para versiones anteriores:

| Problema | Solución aplicada |
|---|---|
| `theme` y `css` en `gr.Blocks()` deprecados | Mover parámetros a `demo.launch()` |
| `show_copy_button` no soportado en `gr.Textbox` | Eliminar el parámetro |
| `type="messages"` no soportado en `gr.Chatbot` | Eliminar el parámetro |
| Historial del chatbot requiere diccionarios `{role, content}` | Reemplazar tuplas por diccionarios |

### 9.5 Problema de seguridad en GitHub

Al intentar subir el repositorio por primera vez, GitHub bloqueó el push porque detectó la API key de Groq hardcodeada en `app.py`. 

**Solución:** 
1. Mover todas las keys a un archivo `.env` excluido del repositorio
2. Usar `python-dotenv` para cargar las variables de entorno
3. Reescribir el historial de Git con `git checkout --orphan` para eliminar el commit con la key expuesta

*Proyecto académico · Universidad Autónoma de Occidente · 2026*
*Los datos provienen de fuentes públicas de Colgate-Palmolive.*
