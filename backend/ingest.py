from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
from pypdf import PdfReader
from markdown import markdown
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from config import (
    STORE_DIR,
    EMBEDDING_MODEL_ID,
    EMBED_CACHE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return [c.strip() for c in chunks if c.strip()]


def _pdf_to_text(path: Path) -> str:
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            pass
    return "\n".join(texts)


def _md_to_text(path: Path) -> str:
    html = markdown(Path(path).read_text(encoding="utf-8"))
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ")


def _load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_ID, cache_folder=str(EMBED_CACHE_DIR))


def build_or_update_index(files: List[Path]) -> Tuple[faiss.IndexFlatIP, List[str], List[str]]:
    """Crea/actualiza FAISS y meta.json con chunks + sources (filename por chunk)."""
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"

    texts: List[str] = []
    for f in files:
        ext = f.suffix.lower()
        if ext == ".pdf":
            texts.append(_pdf_to_text(f))
        elif ext in (".md", ".markdown"):
            texts.append(_md_to_text(f))
        else:
            texts.append(Path(f).read_text(encoding="utf-8", errors="ignore"))

    # Particionar + etiquetar con filename
    split_chunks: List[str] = []
    split_sources: List[str] = []
    for f, t in zip(files, texts):
        cs = _chunk_text(t, CHUNK_SIZE, CHUNK_OVERLAP)
        split_chunks.extend(cs)
        split_sources.extend([f.name] * len(cs))

    if not split_chunks:
        raise ValueError("No se pudo extraer texto de los archivos proporcionados.")

    # Embeddings
    model = _load_embedding_model()
    emb = model.encode(split_chunks, normalize_embeddings=True, convert_to_numpy=True)

    # Índice FAISS
    if index_path.exists():
        index = faiss.read_index(str(index_path))
        old_meta = json.loads(meta_path.read_text(encoding="utf-8"))

        old_chunks = old_meta.get("chunks", [])
        old_sources = old_meta.get("sources", ["unknown"] * len(old_chunks))

        faiss.normalize_L2(emb)
        index.add(emb.astype(np.float32))

        meta = {
            "chunks": old_chunks + split_chunks,
            "sources": old_sources + split_sources,
        }
    else:
        d = emb.shape[1]
        index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(emb)
        index.add(emb.astype(np.float32))
        meta = {"chunks": split_chunks, "sources": split_sources}

    # Guardar
    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return index, meta["chunks"], meta["sources"]


def load_index() -> Tuple[faiss.IndexFlatIP, List[str], List[str]]:
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"
    if not index_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Aún no hay índice. Ingresa documentos primero.")
    index = faiss.read_index(str(index_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    chunks = meta.get("chunks", [])
    sources = meta.get("sources", ["unknown"] * len(chunks))
    if len(sources) != len(chunks):
        # Compatibilidad con índices viejos: rellena con "unknown"
        sources = (sources + ["unknown"] * len(chunks))[:len(chunks)]
    return index, chunks, sources
