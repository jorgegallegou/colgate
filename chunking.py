import json
import re
from pathlib import Path

DATA_DIR = Path("data")
OUTPUT_FILE = Path("data/knowledge_base.txt")

def clean_text(text: str) -> str:
    """Limpia espacios, saltos de línea y caracteres raros."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7EáéíóúÁÉÍÓÚüÜñÑ¿¡.,;:()\-\'\"]+', ' ', text)
    return text.strip()

def chunk_text(text: str, max_chars: int = 1500, overlap: int = 150) -> list[str]:
    """Divide texto largo en chunks con solapamiento."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = text.rfind('. ', start, end)
            if cut != -1:
                end = cut + 1
        chunks.append(text[start:end].strip())
        next_start = end - overlap
        if next_start <= start:  # evita bucle infinito
            next_start = start + max_chars
        start = next_start
    return chunks

def load_paginas() -> list[dict]:
    path = DATA_DIR / "paginas_raw.json"
    if not path.exists():
        print("⚠ paginas_raw.json no encontrado")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for item in data:
        titulo = clean_text(item.get("nombre") or item.get("titulo") or item.get("title") or "Página web")
        contenido = clean_text(item.get("texto") or item.get("contenido") or item.get("text") or item.get("content") or "")
        url = item.get("url", "")
        if contenido:
            for chunk in chunk_text(contenido):
                entries.append({
                    "fuente": "web",
                    "titulo": titulo,
                    "url": url,
                    "texto": chunk
                })
    print(f"✓ Páginas: {len(entries)} chunks")
    return entries

def load_youtube() -> list[dict]:
    path = DATA_DIR / "youtube_raw.json"
    if not path.exists():
        print("⚠ youtube_raw.json no encontrado")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for item in data:
        titulo = clean_text(item.get("titulo") or item.get("title") or "Video YouTube")
        contenido = clean_text(
            item.get("transcripcion") or
            item.get("transcript") or
            item.get("descripcion") or
            item.get("description") or
            item.get("texto") or ""
)
        
        url = item.get("url") or item.get("webpage_url", "")
        if contenido:
            for chunk in chunk_text(contenido):
                entries.append({
                    "fuente": "youtube",
                    "titulo": titulo,
                    "url": url,
                    "texto": chunk
                })
    print(f"✓ YouTube: {len(entries)} chunks")
    return entries

def load_wikipedia() -> list[dict]:
    path = DATA_DIR / "wikipedia_raw.json"
    if not path.exists():
        print("⚠ wikipedia_raw.json no encontrado")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for item in data:
        titulo = clean_text(item.get("titulo") or item.get("title") or "Wikipedia")
        contenido = clean_text(item.get("texto_completo") or item.get("contenido") or item.get("text") or "")
        url = item.get("url", "")
        idioma = item.get("idioma") or item.get("lang") or "es"
        if contenido:
            for chunk in chunk_text(contenido):
                entries.append({
                    "fuente": f"wikipedia_{idioma}",
                    "titulo": titulo,
                    "url": url,
                    "texto": chunk
                })
    print(f"✓ Wikipedia: {len(entries)} chunks")
    return entries

def build_knowledge_base():
    print("🔧 Construyendo knowledge base...")
    all_entries = load_wikipedia() + load_paginas() + load_youtube()

    if not all_entries:
        print("❌ No se encontró contenido. Verifica los archivos en data/")
        return

    lines = []
    for entry in all_entries:
        lines.append(f"[FUENTE: {entry['fuente'].upper()}]")
        lines.append(f"[TÍTULO: {entry['titulo']}]")
        if entry.get("url"):
            lines.append(f"[URL: {entry['url']}]")
        lines.append(entry["texto"])
        lines.append("---")

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    total_chars = sum(len(e["texto"]) for e in all_entries)
    print(f"\n✅ knowledge_base.txt generado")
    print(f"   • Chunks totales : {len(all_entries)}")
    print(f"   • Caracteres     : {total_chars:,}")
    print(f"   • Archivo        : {OUTPUT_FILE}")

    # Advertencia si es demasiado grande para un solo prompt
    if total_chars > 60_000:
        print(f"\n⚠ El texto ({total_chars:,} chars) puede exceder el contexto del modelo.")
        print("  Considera filtrar por fuente o reducir max_chars en chunk_text().")

if __name__ == "__main__":
    build_knowledge_base()