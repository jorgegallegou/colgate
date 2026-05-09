import re
from pathlib import Path
from collections import defaultdict

# ── Configuración ──────────────────────────────────────────────────────────────
INPUT_PATH  = Path("knowledge_base.txt")
OUTPUT_PATH = Path("knowledge_base_clean.txt")

CHUNK_SIZE    = 600   # chars por chunk final
CHUNK_OVERLAP = 100   # solapamiento entre chunks (captura contexto de frontera)

# URLs/títulos a descartar — contenido irrelevante confirmado
TITULOS_EXCLUIR = {"medellin"}

# ── Helpers ────────────────────────────────────────────────────────────────────
def extraer_meta(chunk: str) -> dict:
    fuente = re.search(r"\[FUENTE: (.+?)\]", chunk)
    titulo = re.search(r"\[TÍTULO: (.+?)\]", chunk)
    url    = re.search(r"\[URL: (.+?)\]",    chunk)
    return {
        "fuente": fuente.group(1) if fuente else "DESCONOCIDA",
        "titulo": titulo.group(1) if titulo else "sin_titulo",
        "url":    url.group(1)    if url    else "sin_url",
    }

def extraer_cuerpo(chunk: str) -> str:
    """Elimina las líneas de metadatos y devuelve solo el texto."""
    lineas = chunk.splitlines()
    cuerpo = [l for l in lineas if not l.startswith("[")]
    return " ".join(cuerpo).strip()

def re_chunkear(texto: str, size: int, overlap: int) -> list[str]:
    """Divide texto en fragmentos de `size` chars con `overlap` de solapamiento."""
    fragmentos = []
    start = 0
    while start < len(texto):
        end = start + size
        if end >= len(texto):
            fragmentos.append(texto[start:])
            break
        # Cortar en el último espacio para no partir palabras
        corte = texto.rfind(" ", start, end)
        if corte <= start:
            corte = end
        fragmentos.append(texto[start:corte].strip())
        start = corte - overlap  # retroceder `overlap` para el siguiente chunk
        if start < 0:
            start = 0
    return [f for f in fragmentos if len(f) > 50]  # descartar fragmentos triviales

# ── Pipeline ───────────────────────────────────────────────────────────────────
raw = INPUT_PATH.read_text(encoding="utf-8")
chunks_raw = [c.strip() for c in raw.split("---") if c.strip()]

# 1. Agrupar por URL (reconstruir artículos)
articulos: dict[str, dict] = {}
for c in chunks_raw:
    meta = extraer_meta(c)
    if meta["titulo"] in TITULOS_EXCLUIR:
        continue
    url = meta["url"]
    if url not in articulos:
        articulos[url] = {"meta": meta, "partes": []}
    articulos[url]["partes"].append(extraer_cuerpo(c))

# 2. Re-chunkear cada artículo
chunks_finales = []
for url, datos in articulos.items():
    texto_completo = " ".join(datos["partes"])
    # Limpiar espacios múltiples
    texto_completo = re.sub(r"\s+", " ", texto_completo).strip()
    meta = datos["meta"]
    header = f"[FUENTE: {meta['fuente']}]\n[TÍTULO: {meta['titulo']}]\n[URL: {meta['url']}]"
    
    if len(texto_completo) <= CHUNK_SIZE:
        chunks_finales.append(f"{header}\n{texto_completo}")
    else:
        for frag in re_chunkear(texto_completo, CHUNK_SIZE, CHUNK_OVERLAP):
            chunks_finales.append(f"{header}\n{frag}")

# 3. Guardar
OUTPUT_PATH.write_text("\n---\n".join(chunks_finales), encoding="utf-8")

# 4. Reporte
print(f"Chunks originales : {len(chunks_raw)}")
print(f"Artículos únicos  : {len(articulos)}")
print(f"Chunks finales    : {len(chunks_finales)}")
print(f"Chars totales     : {OUTPUT_PATH.stat().st_size:,}")
print(f"Guardado en       : {OUTPUT_PATH}")

# ── Post-proceso: eliminar cuerpos duplicados y basura ─────────────────────────
CUERPOS_EXCLUIR = {
    # Cookie banners sin contenido útil
    "Nos tomamos en serio su privacidad Utilizamos cookies",
    # Marcadores vacíos de YouTube sin transcripción
    "Transcripción disponible en es",
}

text = OUTPUT_PATH.read_text(encoding="utf-8")
chunks = [c.strip() for c in text.split("---") if c.strip()]

def extraer_cuerpo_chunk(c: str) -> str:
    lineas = c.splitlines()
    return " ".join(l for l in lineas if not l.startswith("[")).strip()

vistos = set()
chunks_dedup = []
for c in chunks:
    cuerpo = extraer_cuerpo_chunk(c)
    # Excluir cuerpos en lista negra
    if any(excl in cuerpo for excl in CUERPOS_EXCLUIR):
        continue
    # Excluir duplicados exactos de cuerpo
    if cuerpo in vistos:
        continue
    vistos.add(cuerpo)
    chunks_dedup.append(c)

OUTPUT_PATH.write_text("\n---\n".join(chunks_dedup), encoding="utf-8")
print(f"\nPost-proceso:")
print(f"  Antes : {len(chunks)} chunks")
print(f"  Después: {len(chunks_dedup)} chunks")
print(f"  Eliminados: {len(chunks) - len(chunks_dedup)}")
