import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# ── Configuración ──────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_PATH = Path("data/knowledge_base_clean.txt")
VECTORSTORE_PATH    = Path("data/vectorstore")
EMBEDDING_MODEL     = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ── Cargar y parsear chunks ────────────────────────────────────────────────────
def cargar_chunks(path: Path) -> list[Document]:
    """
    Lee knowledge_base_clean.txt y convierte cada chunk en un Document de LangChain.
    El header [FUENTE], [TÍTULO], [URL] se guarda como metadata.
    El cuerpo del texto se guarda como page_content.
    """
    import re

    raw = path.read_text(encoding="utf-8")
    bloques = [b.strip() for b in raw.split("---") if b.strip()]

    documentos = []
    for bloque in bloques:
        lineas = bloque.splitlines()

        # Extraer metadata del header
        fuente = next((re.search(r"\[FUENTE: (.+?)\]", l) for l in lineas if "[FUENTE:" in l), None)
        titulo = next((re.search(r"\[TÍTULO: (.+?)\]", l) for l in lineas if "[TÍTULO:" in l), None)
        url    = next((re.search(r"\[URL: (.+?)\]",    l) for l in lineas if "[URL:"    in l), None)

        # Cuerpo: todo lo que no es línea de metadata
        cuerpo = " ".join(l for l in lineas if not l.startswith("[")).strip()

        if not cuerpo:
            continue

        doc = Document(
            page_content=cuerpo,
            metadata={
                "fuente": fuente.group(1) if fuente else "desconocida",
                "titulo": titulo.group(1) if titulo else "sin_titulo",
                "url":    url.group(1)    if url    else "sin_url",
            }
        )
        documentos.append(doc)

    return documentos

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"📂 Cargando knowledge base desde: {KNOWLEDGE_BASE_PATH}")
    documentos = cargar_chunks(KNOWLEDGE_BASE_PATH)
    print(f"✓ {len(documentos)} chunks cargados")

    print(f"\n🤖 Cargando modelo de embeddings: {EMBEDDING_MODEL}")
    print("   (Primera vez descarga ~420MB — puede tardar unos minutos)")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("✓ Modelo cargado")

    print(f"\n⚙️  Construyendo índice FAISS...")
    vectorstore = FAISS.from_documents(documentos, embeddings)
    print(f"✓ Índice construido con {vectorstore.index.ntotal} vectores")

    print(f"\n💾 Guardando vectorstore en: {VECTORSTORE_PATH}")
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_PATH))
    print("✓ Vectorstore guardado")

    # Prueba rápida de retrieval
    print("\n🔍 Prueba de retrieval:")
    query = "¿Cuál es la planta de producción de Colgate en Colombia?"
    resultados = vectorstore.similarity_search(query, k=3)
    for i, r in enumerate(resultados, 1):
        print(f"\n  Resultado {i} [{r.metadata['titulo']}]:")
        print(f"  {r.page_content[:120]}...")

    print("\n✅ Vectorstore listo para usar.")
