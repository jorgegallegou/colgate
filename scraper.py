# ── Librerías ──────────────────────────────────────────────────────────────────
import time
import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import trafilatura

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ── URLs objetivo ──────────────────────────────────────────────────────────────
URLS_OBJETIVO = {
    "pagina_principal":  "https://www.colgatepalmolive.com.co/",
    "quienes_somos":     "https://www.colgatepalmolive.com.co/who-we-are",
    "fundacion":         "https://www.colgatepalmolive.com.co/fundacion-colgate",
    "politicas":         "https://www.colgatepalmolive.com.co/our-policies",
    "comunidad":         "https://www.colgatepalmolive.com.co/community-impact",
    "historia_colombia": "https://www.valoraanalitik.com/historia-de-colgate-palmolive-en-colombia/",
    "operacion_cali":    "https://www.elpais.com.co/economia/asi-ha-consolidado-operaciones-en-cali-la-multinacional-colgate-seguimos-creyendo-en-la-economia-y-en-el-pais-dice-su-gerente-1015.html",
    "contacto":          "https://www.colgatepalmolive.com.co/contact-us",
    "info_colombia":     "https://www.informacolombia.com/directorio-empresas/informacion-empresa/colgate-palmolive-compania",
    "palmolive_co":      "https://www.palmolive.co/",
    "larepublica_80años":"https://www.larepublica.co/empresas/la-compania-colgate-palmolive-en-colombia-celebro-80-anos-operando-en-la-industria-3670490",
    "medellin":          "https://www.medellin.gov.co/es/secretaria-de-comunicaciones/obras-y-mejoramientos-de-escenarios-deportivos-de-medellin/obras-y-mejoramientos-en-la-zona-2-de-medellin/obras-y-mejoramientos-en-la-comuna-5-castilla/colgate-palmolive/",
    "mapasocial":        "http://mapasocial.dps.gov.co/organizaciones/111",
    "gobernanza":               "https://www.colgatepalmolive.com.co/who-we-are/governance",
    "codigo_conducta":          "https://www.colgatepalmolive.com.co/who-we-are/governance/code-of-conduct",
    "linea_etica":              "https://www.colgatepalmolive.com.co/who-we-are/governance/ethics-line",
    "politica_donaciones":      "https://www.colgatepalmolive.com.co/who-we-are/our-policies/donation-policy",
    "gestion_respeto":          "https://www.colgatepalmolive.com.co/who-we-are/our-policies/managing-with-respect",
    "igualdad_oportunidades":   "https://www.colgatepalmolive.com.co/who-we-are/our-policies/equal-opportunity-employer-info",
    "valoracion_personas":      "https://www.colgatepalmolive.com.co/who-we-are/our-policies/valuing-colgate-people",
    "historias_comunidades":    "https://www.colgatepalmolive.com.co/who-we-are/stories/communities",
    "sonrisas_brillantes":      "https://www.colgatepalmolive.com.co/community-impact/bright-smiles-bright-futures",
    "global_quienes_somos":     "https://www.colgatepalmolive.com/en-us/who-we-are",
    "global_comunidad":         "https://www.colgatepalmolive.com/en-us/community-impact",
    "global_sostenibilidad":    "https://www.colgatepalmolive.com/en-us/sustainability",
    "portafolio_colgate":       "https://www.portafolio.co/negocios/empresas/colgate-palmolive-colombia-historia-787234",
}

# ── Configuración ──────────────────────────────────────────────────────────────
PAUSA_ENTRE_PETICIONES = 3  # segundos de espera entre cada página

# ── Función de limpieza de texto ───────────────────────────────────────────────
def limpiar_texto(texto: str) -> str:
    """Elimina espacios múltiples, caracteres raros y saltos de línea excesivos."""
    texto = re.sub(r"\s+", " ", texto)      # espacios múltiples → uno solo
    texto = re.sub(r"\n{3,}", "\n\n", texto) # más de 2 saltos → solo 2
    texto = texto.replace("\xa0", " ")       # espacio especial → espacio normal
    texto = texto.replace("\u200b", "")      # carácter invisible → nada
    texto = texto.strip()                    # elimina espacios al inicio y al final
    return texto

# ── Función de extracción con BeautifulSoup ────────────────────────────────────
def extraer_con_bs4(html: str) -> str:
    """Extrae el texto limpio de un HTML eliminando ruido."""
    soup = BeautifulSoup(html, "lxml")

    # Eliminar etiquetas de ruido
    for tag in soup(["script", "style", "noscript", "iframe",
                     "nav", "footer", "header"]):
        tag.decompose()

    # Buscar el contenido principal
    contenido = (
        soup.find("main") or
        soup.find("div", id="main") or
        soup.find("div", id="content") or
        soup.find("body")
    )

    if not contenido:
        return ""

    fragmentos = []
    for tag in contenido.find_all(["h1", "h2", "h3", "h4", "p", "li", "td"]):
        texto = tag.get_text(separator=" ", strip=True)
        if len(texto) > 30:
            fragmentos.append(texto)

    return limpiar_texto("\n".join(fragmentos))

# ── Función de extracción con Selenium ─────────────────────────────────────────
def extraer_con_selenium(url: str) -> str:
    """Usa Chrome para extraer texto de páginas con bloqueo anti-bot."""
    opciones = Options()
    opciones.add_argument("--headless")           # Chrome sin ventana visible
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    servicio = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)

    try:
        driver.get(url)
        time.sleep(3)  # esperar que cargue el JavaScript
        html = driver.page_source
        html = html.encode("utf-8").decode("utf-8")
        texto = extraer_con_bs4(html)
        return texto
    except Exception as e:
        print(f"    ✗ Error Selenium: {e}")
        return ""
    finally:
        driver.quit()  # siempre cerrar el navegador

# ── Función principal ──────────────────────────────────────────────────────────
def ejecutar_scraping():
    """Recorre todas las URLs y extrae el texto de cada una."""
    resultados = []

    print("=" * 60)
    print("WEB SCRAPING - Colgate-Palmolive Colombia")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total URLs: {len(URLS_OBJETIVO)}")
    print("=" * 60)

    for nombre, url in URLS_OBJETIVO.items():
        print(f"\n  Procesando: [{nombre}]")
        print(f"  URL: {url}")

                # Usar Selenium directamente para cargar JavaScript
        print(f"  → Usando Selenium...")
        texto = extraer_con_selenium(url)
        metodo = "selenium"

        if texto and es_contenido_valido(texto, nombre):
            print(f"  ✓ Extraídos {len(texto):,} caracteres con {metodo}")
            resultados.append({
                "nombre":     nombre,
                "url":        url,
                "metodo":     metodo,
                "texto":      texto,
                "num_chars":  len(texto),
                "fecha":      datetime.now().isoformat(),
            })
        else:
            print(f"  ✗ Sin contenido")

        time.sleep(PAUSA_ENTRE_PETICIONES)

    # Guardar resultados
    with open("data/paginas_raw.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"FINALIZADO: {len(resultados)} páginas extraídas")
    print("Guardado en: data/paginas_raw.json")
    print("=" * 60)

    return resultados

# ── Filtro de calidad ──────────────────────────────────────────────────────────
def es_contenido_valido(texto: str, nombre: str) -> bool:
    """Descarta páginas con demasiado ruido o muy poco contenido útil."""
    # Demasiado largo probablemente es ruido (cookies, publicidad)
    if len(texto) > 80000:
        print(f"  ⚠ [{nombre}] Descartado por exceso de ruido ({len(texto):,} chars)")
        return False
    # Muy corto no tiene información útil
    if len(texto) < 200:
        print(f"  ⚠ [{nombre}] Descartado por contenido insuficiente")
        return False
    return True

# ── Ejecutar ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    ejecutar_scraping()