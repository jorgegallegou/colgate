"""
scraper_youtube.py - Extracción de información de YouTube
Colgate-Palmolive Colombia - Knowledge Base
"""

import json
import os
from datetime import datetime
import yt_dlp


# ── Términos de búsqueda ───────────────────────────────────────────────────────
BUSQUEDAS = [
    "Colgate Palmolive Colombia",
    "Colgate Palmolive Cali Valle del Cauca",
    "Colgate Palmolive planta Cali",
    "Colgate Palmolive sostenibilidad Colombia",
    "Colgate Palmolive historia Colombia",
    "Fundación Colgate Palmolive Colombia",
]

# Máximo de videos por búsqueda
MAX_VIDEOS = 5

# ── Función de extracción ──────────────────────────────────────────────────────
def extraer_videos(termino: str, max_videos: int = 5) -> list:
    """
    Busca videos en YouTube y extrae título, descripción y transcripción.
    """
    resultados = []

    opciones = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["es", "es-419", "en"],
        "skip_download": True,
        "max_downloads": max_videos,
    }

    url_busqueda = f"ytsearch{max_videos}:{termino}"

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url_busqueda, download=False)

            if not info or "entries" not in info:
                print(f"  ✗ Sin resultados para: {termino}")
                return []

            for video in info["entries"]:
                if not video:
                    continue

                # Extraer transcripción si está disponible
                transcripcion = ""
                subtitulos = video.get("subtitles", {}) or {}
                auto_subtitulos = video.get("automatic_captions", {}) or {}

                for lang in ["es", "es-419", "en"]:
                    if lang in subtitulos or lang in auto_subtitulos:
                        transcripcion = f"Transcripción disponible en {lang}"
                        break

                resultado = {
                    "titulo":       video.get("title", ""),
                    "descripcion":  video.get("description", "")[:2000],
                    "url":          video.get("webpage_url", ""),
                    "canal":        video.get("uploader", ""),
                    "duracion":     video.get("duration", 0),
                    "vistas":       video.get("view_count", 0),
                    "fecha":        video.get("upload_date", ""),
                    "transcripcion": transcripcion,
                    "busqueda":     termino,
                    "scraped_at":   datetime.now().isoformat(),
                }

                if resultado["titulo"]:
                    resultados.append(resultado)
                    print(f"  ✓ {resultado['titulo'][:60]}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    return resultados

# ── Pipeline principal ─────────────────────────────────────────────────────────
def ejecutar_scraping_youtube():
    """Ejecuta todas las búsquedas y consolida los resultados."""
    todos_resultados = []
    urls_vistas = set()  # para evitar duplicados

    print("=" * 60)
    print("SCRAPING YOUTUBE - Colgate-Palmolive Colombia")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Búsquedas: {len(BUSQUEDAS)} | Máx videos c/u: {MAX_VIDEOS}")
    print("=" * 60)

    for termino in BUSQUEDAS:
        print(f"\n🔍 Buscando: '{termino}'")
        videos = extraer_videos(termino, MAX_VIDEOS)

        for video in videos:
            # Evitar duplicados por URL
            if video["url"] not in urls_vistas:
                urls_vistas.add(video["url"])
                todos_resultados.append(video)

    # Guardar resultados
    os.makedirs("data", exist_ok=True)
    with open("data/youtube_raw.json", "w", encoding="utf-8") as f:
        json.dump(todos_resultados, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"FINALIZADO: {len(todos_resultados)} videos únicos extraídos")
    print("Guardado en: data/youtube_raw.json")
    print("=" * 60)

    return todos_resultados


# ── Ejecutar ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ejecutar_scraping_youtube()