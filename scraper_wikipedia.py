"""
scraper_wikipedia.py - Extracción de información de Wikipedia
Colgate-Palmolive Colombia - Knowledge Base
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def limpiar_texto_wikipedia(texto: str) -> str:
    """Corrige palabras pegadas y limpia texto de Wikipedia."""
    texto = re.sub(r"([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])", r"\1 \2", texto)
    texto = re.sub(r" {2,}", " ", texto)
    texto = texto.strip()
    return texto

# ── URLs objetivo ──────────────────────────────────────────────────────────────
URLS_WIKIPEDIA = {
    "wikipedia_es": "https://es.wikipedia.org/wiki/Colgate-Palmolive",
    "wikipedia_en": "https://en.wikipedia.org/wiki/Colgate-Palmolive",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Función de extracción ──────────────────────────────────────────────────────
def extraer_wikipedia(nombre: str, url: str) -> dict:
    """Extrae el contenido de un artículo de Wikipedia por secciones."""
    print(f"\n  Extrayendo: [{nombre}] {url}")

    try:
        respuesta = requests.get(url, headers=HEADERS, timeout=15)
        respuesta.raise_for_status()
        respuesta.encoding = "utf-8"

        soup = BeautifulSoup(respuesta.text, "lxml")

        for tag in soup(["script", "style", "sup", "table",
                         ".mw-editsection", ".reference"]):
            tag.decompose()

        titulo = soup.find("h1", id="firstHeading")
        titulo = titulo.get_text(strip=True) if titulo else "Sin título"

        contenido = soup.find("div", id="mw-content-text")
        if not contenido:
            return {}

        secciones = {}
        seccion_actual = "introduccion"
        textos_actuales = []

        for elemento in contenido.find_all(["h2", "h3", "p", "li"]):
            if elemento.name in ["h2", "h3"]:
                if textos_actuales:
                    texto = " ".join(textos_actuales).strip()
                    if len(texto) > 50:
                        secciones[seccion_actual] = texto
                seccion_actual = elemento.get_text(strip=True).lower()
                seccion_actual = re.sub(r"[^\w\s]", "", seccion_actual)
                textos_actuales = []
            else:
                texto = limpiar_texto_wikipedia(
                    elemento.get_text(separator=" ", strip=True)
                )
                if len(texto) > 30:
                    textos_actuales.append(texto)

        if textos_actuales:
            texto = " ".join(textos_actuales).strip()
            if len(texto) > 50:
                secciones[seccion_actual] = texto

        texto_completo = " ".join(secciones.values())

        print(f"  ✓ {len(secciones)} secciones | {len(texto_completo):,} caracteres")

        return {
            "nombre":         nombre,
            "url":            url,
            "titulo":         titulo,
            "secciones":      secciones,
            "texto_completo": texto_completo,
            "num_chars":      len(texto_completo),
            "scraped_at":     datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {}

# ── Pipeline principal ─────────────────────────────────────────────────────────
def ejecutar_scraping_wikipedia():
    resultados = []

    print("=" * 60)
    print("SCRAPING WIKIPEDIA - Colgate-Palmolive")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    for nombre, url in URLS_WIKIPEDIA.items():
        resultado = extraer_wikipedia(nombre, url)
        if resultado:
            resultados.append(resultado)

    with open("data/wikipedia_raw.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"FINALIZADO: {len(resultados)} artículos extraídos")
    print("Guardado en: data/wikipedia_raw.json")
    print("=" * 60)

    return resultados

# ── Ejecutar ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ejecutar_scraping_wikipedia()