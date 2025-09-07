from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
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

# --- Dependencias de PDF / OCR (opcionales) ---
HAS_PYMUPDF = True
try:
    import fitz  # PyMuPDF
except Exception:
    HAS_PYMUPDF = False

HAS_OCR = True
try:
    from pdf2image import convert_from_path
    import pytesseract
    import os
except Exception:
    HAS_OCR = False


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


def _pdf_to_pages_pymupdf(path: Path) -> List[str]:
    """Extrae texto por página con PyMuPDF (mejor orden de lectura)."""
    pages: List[str] = []
    doc = fitz.open(str(path))
    for i, page in enumerate(doc):
        # mejor que 'text' simple: blocks respeta más el orden
        blocks = page.get_text("blocks")
        # blocks: [x0, y0, x1, y1, text, block_no, block_type]
        blocks_sorted = sorted(blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))
        txt = "\n".join([b[4] for b in blocks_sorted if b[4]])
        pages.append(txt.strip())
    doc.close()
    return pages


def _pdf_to_pages_ocr(path: Path, lang_hint: str = "spa+eng") -> List[str]:
    """OCR por página solo si no hay texto (requiere poppler + tesseract)."""
    if not HAS_OCR:
        return []
    # Convertir a imágenes por página
    try:
        images = convert_from_path(str(path), dpi=300)
    except Exception:
        return []
    pages: List[str] = []
    for img in images:
        try:
            txt = pytesseract.image_to_string(img, lang=lang_hint)
        except Exception:
            txt = pytesseract.image_to_string(img)  # fallback
        pages.append((txt or "").strip())
    return pages


def _pdf_to_text_pages(path: Path) -> List[str]:
    """
    Devuelve lista de textos por página.
    Estrategia:
      1) PyMuPDF si está disponible.
      2) Si la suma de texto es muy baja (PDF escaneado), intenta OCR por página.
    """
    pages: List[str] = []
    if HAS_PYMUPDF:
        try:
            pages = _pdf_to_pages_pymupdf(path)
        except Exception:
            pages = []
    # Si no hay PyMuPDF o salió mal, intenta lectura muy básica con PyPDF (opcional)
    if not pages:
        try:
            from pypdf import PdfReader
            r = PdfReader(str(path))
            pages = [(p.extract_text() or "").strip() for p in r.pages]
        except Exception:
            pages = []

    # ¿Parece escaneado? (muy poco texto total)
    total_chars = sum(len(p) for p in pages)
    if total_chars < 50 and HAS_OCR:
        ocr_pages = _pdf_to_pages_ocr(path)
        if ocr_pages:
            pages = ocr_pages

    # Asegurar formato
    return [(p or "").strip() for p in pages]


def _md_to_text(path: Path) -> str:
    html = markdown(Path(path).read_text(encoding="utf-8", errors="ignore"))
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ")


def _load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_ID, cache_folder=str(EMBED_CACHE_DIR))


def build_or_update_index(files: List[Path]) -> Tuple[faiss.IndexFlatIP, List[str], List[str], List[int]]:
    """
    Crea/actualiza FAISS y meta.json con:
      - chunks: texto por fragmento
      - sources: filename por fragmento
      - pages: número de página (base 1) por fragmento
    """
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"

    # Preparar textos y metadatos
    all_chunks: List[str] = []
    all_sources: List[str] = []
    all_pages: List[int] = []

    for f in files:
        ext = f.suffix.lower()
        if ext == ".pdf":
            pages = _pdf_to_text_pages(f)  # lista por página
            for page_no, ptxt in enumerate(pages, start=1):
                cs = _chunk_text(ptxt, CHUNK_SIZE, CHUNK_OVERLAP)
                all_chunks.extend(cs)
                all_sources.extend([f.name] * len(cs))
                all_pages.extend([page_no] * len(cs))
        elif ext in (".md", ".markdown"):
            txt = _md_to_text(f)
            cs = _chunk_text(txt, CHUNK_SIZE, CHUNK_OVERLAP)
            all_chunks.extend(cs)
            all_sources.extend([f.name] * len(cs))
            all_pages.extend([1] * len(cs))
        else:
            txt = Path(f).read_text(encoding="utf-8", errors="ignore")
            cs = _chunk_text(txt, CHUNK_SIZE, CHUNK_OVERLAP)
            all_chunks.extend(cs)
            all_sources.extend([f.name] * len(cs))
            all_pages.extend([1] * len(cs))

    if not all_chunks:
        raise ValueError("No se pudo extraer texto de los archivos proporcionados.")

    # Embeddings
    model = _load_embedding_model()
    emb = model.encode(all_chunks, normalize_embeddings=True, convert_to_numpy=True)

    # Índice FAISS
    if index_path.exists():
        index = faiss.read_index(str(index_path))
        old_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        old_chunks = old_meta.get("chunks", [])
        old_sources = old_meta.get("sources", ["unknown"] * len(old_chunks))
        old_pages = old_meta.get("pages", [1] * len(old_chunks))

        faiss.normalize_L2(emb)
        index.add(emb.astype(np.float32))

        meta = {
            "chunks": old_chunks + all_chunks,
            "sources": old_sources + all_sources,
            "pages": old_pages + all_pages,
        }
    else:
        d = emb.shape[1]
        index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(emb)
        index.add(emb.astype(np.float32))
        meta = {"chunks": all_chunks, "sources": all_sources, "pages": all_pages}

    # Guardar
    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return index, meta["chunks"], meta["sources"], meta["pages"]


def load_index() -> Tuple[faiss.IndexFlatIP, List[str], List[str], List[int]]:
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"
    if not index_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Aún no hay índice. Ingresa documentos primero.")
    index = faiss.read_index(str(index_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    chunks = meta.get("chunks", [])
    sources = meta.get("sources", ["unknown"] * len(chunks))
    pages = meta.get("pages", [1] * len(chunks))
    # Alinear longitudes por compatibilidad
    ln = len(chunks)
    if len(sources) != ln:
        sources = (sources + ["unknown"] * ln)[:ln]
    if len(pages) != ln:
        pages = (pages + [1] * ln)[:ln]
    return index, chunks, sources, pages
