# Asistente Virtual de Colgate-Palmolive
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

Contexto de conocimiento
{knowledge_base}
Fin del contexto

**Técnicas aplicadas según guía de Prompt Engineering:**
- **Principio 1**: Rol específico asignado al modelo
- **Principio 4**: Instrucciones afirmativas ("Debes responder") combinadas con restricciones explícitas
- **Principio 9**: Uso de "Serás penalizado" para reforzar el cumplimiento de instrucciones
- **Principio 17**: Delimitadores `###` para separar secciones del prompt
- **Zero-shot**: El modelo responde sin ejemplos previos, suficiente dado el contexto rico y las instrucciones claras

### 4.3 Nota sobre el Módulo 2

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

MISTRAL_API_KEY=su_key_aquí

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

colgate/
├── app.py                  # Aplicación principal Gradio + LangChain
├── chunking.py             # Preprocesamiento y consolidación de datos
├── scraper.py              # Scraper sitio web oficial
├── scraper_youtube.py      # Scraper videos YouTube
├── scraper_wikipedia.py    # Scraper Wikipedia ES + EN
├── pyproject.toml          # Dependencias del proyecto
├── data/
│   ├── paginas_raw.json    # Datos crudos páginas web
│   ├── youtube_raw.json    # Datos crudos YouTube
│   ├── wikipedia_raw.json  # Datos crudos Wikipedia
│   └── knowledge_base.txt  # Base de conocimiento consolidada
└── .env                    # API keys (no incluido en repositorio)

---

*Proyecto académico · Universidad Autónoma de Occidente · 2026*
*Los datos provienen de fuentes públicas de Colgate-Palmolive.*