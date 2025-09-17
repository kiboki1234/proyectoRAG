from __future__ import annotations
"""
Ingesta de documentos para el backend RAG.

- Extracción por página (PDF) o completa (MD/TXT/otros)
- Chunking por oraciones con solapamiento
- Paralelización por archivo
- Deduplicación por (source, page, text) (tanto intra-batch como vs índice previo)
- Construcción/actualización de índice FAISS con E5
- Helpers de reconstrucción y carga segura (auto-rebuild si cambiaste el embedder)
"""
import json
import os
import hashlib
import concurrent.futures
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import regex as re

import faiss
import numpy as np
from markdown import markdown
from bs4 import BeautifulSoup

from config import (
    STORE_DIR,
    DOCS_DIR,
    EMBEDDING_MODEL_ID,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

# =========================
# Limpieza
# =========================

def _clean_text(s: str) -> str:
    s = re.sub(r"\r\n?", "\n", s or "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\u00A0", " ", s)  # nbsp
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _strip_headers_footers(pages: List[str], max_lines: int = 3) -> List[str]:
    from collections import Counter
    tops, bots = [], []
    for p in pages:
        lines = [ln.strip() for ln in (p or "").splitlines() if ln.strip()]
        tops.append(tuple(lines[:max_lines]) if lines else None)
        bots.append(tuple(lines[-max_lines:]) if lines else None)
    top_counts = Counter([t for t in tops if t])
    bot_counts = Counter([b for b in bots if b])
    thr = max(2, int(0.6 * len(pages)))
    rm_top = set([t for t, c in top_counts.items() if c >= thr])
    rm_bot = set([b for b, c in bot_counts.items() if c >= thr])

    out: List[str] = []
    for p in pages:
        lines = [ln for ln in (p or "").splitlines()]
        if not lines:
            out.append("")
            continue
        for t in rm_top:
            if t and tuple([ln.strip() for ln in lines[:len(t)]]) == t:
                lines = lines[len(t):]
                break
        for b in rm_bot:
            if b and tuple([ln.strip() for ln in lines[-len(b):]]) == b:
                lines = lines[:-len(b)]
                break
        out.append(_clean_text("\n".join(lines)))
    return out

# =========================
# Chunking por oraciones
# =========================

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

def _split_sentences(text: str) -> List[str]:
    abbrev = r'\b(?:Sr|Sra|Dr|Dra|Ing|Lic|etc|p|pp|Fig|Ref|No|Mr|Mrs|Ms|Prof)\.'
    protected = re.sub(abbrev, lambda m: m.group().replace('.', '<DOT>'), text or "")
    parts = _SENT_SPLIT.split(protected)
    parts = [p.replace('<DOT>', '.').strip() for p in parts if p.strip()]
    return parts

def _smart_chunk(text: str, max_chunk_size: int = CHUNK_SIZE, overlap_sents: int = 2) -> List[str]:
    sents = _split_sentences(text)
    if not sents:
        return []
    out: List[str] = []
    buf: List[str] = []
    cur_len = 0
    for s in sents:
        if cur_len + len(s) + 1 > max_chunk_size and buf:
            out.append(_clean_text(" ".join(buf)))
            buf = buf[-overlap_sents:] if overlap_sents > 0 else []
            cur_len = sum(len(x) for x in buf) + (len(buf) - 1 if buf else 0)
        buf.append(s)
        cur_len += len(s) + 1
    if buf:
        out.append(_clean_text(" ".join(buf)))
    return [c for c in out if c.strip()]

# =========================
# Lectores
# =========================

def _pdf_to_text_pages(path: Path) -> List[str]:
    # 1) PyMuPDF si está disponible (mejor layout)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        pages = [doc.load_page(i).get_text("text") for i in range(doc.page_count)]
        doc.close()
    except Exception:
        # 2) Fallback: pypdf
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages]
    pages = [p or "" for p in pages]
    pages = _strip_headers_footers(pages)
    pages = [_clean_text(p) for p in pages]
    return pages

def _md_to_text(path: Path) -> str:
    html = markdown(path.read_text(encoding="utf-8", errors="ignore"))
    soup = BeautifulSoup(html, "html.parser")
    return _clean_text(soup.get_text(" "))

# =========================
# Extracción por archivo
# =========================

def _hash_key(source: str, page: int, text: str) -> str:
    h = hashlib.sha1()
    h.update((source or "unknown").encode("utf-8", errors="ignore"))
    h.update(str(int(page or 1)).encode())
    h.update((text or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()

def _extract_file_chunks(f: Path) -> List[Tuple[str, str, int]]:
    """
    Devuelve lista de (chunk, source, page). page es base-1.
    """
    out: List[Tuple[str, str, int]] = []
    ext = f.suffix.lower()
    if ext == ".pdf":
        pages = _pdf_to_text_pages(f)
        for page_no, ptxt in enumerate(pages, start=1):
            for ch in _smart_chunk(ptxt, max_chunk_size=CHUNK_SIZE, overlap_sents=CHUNK_OVERLAP // 75 or 2):
                out.append((ch, f.name, page_no))
    elif ext in (".md", ".markdown"):
        txt = _md_to_text(f)
        for ch in _smart_chunk(txt, max_chunk_size=CHUNK_SIZE, overlap_sents=CHUNK_OVERLAP // 75 or 2):
            out.append((ch, f.name, 1))
    else:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for ch in _smart_chunk(_clean_text(txt), max_chunk_size=CHUNK_SIZE, overlap_sents=CHUNK_OVERLAP // 75 or 2):
            out.append((ch, f.name, 1))
    return out

# =========================
# Embeddings
# =========================

class _Embedder:
    def __init__(self, model_id: str, cache_dir: Path):
        from sentence_transformers import SentenceTransformer
        self.model_id = model_id
        self.model = SentenceTransformer(model_id, cache_folder=str(cache_dir))

    def _wrap_doc(self, text: str) -> str:
        mid = (self.model_id or "").lower()
        if "e5" in mid or "bge" in mid:
            return f"passage: {text}"
        return text

    def encode_docs(self, texts: List[str]) -> np.ndarray:
        X = [self._wrap_doc(t) for t in texts]
        emb = self.model.encode(
            X,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=32,
        )
        return emb

# =========================
# IO índice & meta
# =========================

def _read_existing_index() -> Tuple[faiss.IndexFlatIP, Dict]:
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"
    index = faiss.read_index(str(index_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return index, meta

def _save_index_and_meta(index, chunks: List[str], sources: List[str], pages: List[int], embedder_id: str):
    assert len(chunks) == len(sources) == len(pages), "meta inconsistente: chunks/sources/pages con longitudes distintas"
    faiss.write_index(index, str(STORE_DIR / "faiss.index"))
    (STORE_DIR / "meta.json").write_text(
        json.dumps({"chunks": chunks, "sources": sources, "pages": pages}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (STORE_DIR / "embedder_config.json").write_text(
        json.dumps({"model_id": embedder_id}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def _load_embedder_id() -> Optional[str]:
    cfg_path = STORE_DIR / "embedder_config.json"
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        return data.get("model_id")
    except Exception:
        return None

# =========================
# Build / Update índice
# =========================

def build_or_update_index(files: List[Path]) -> Tuple[faiss.IndexFlatIP, List[str], List[str], List[int]]:
    """
    Construye o actualiza el índice FAISS.
    - Si cambia el modelo de embeddings, reconstruye.
    - Si es el mismo, hace append sólo de lo nuevo (con deduplicación).
    """
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Meta previa
    prev_chunks: List[str] = []
    prev_sources: List[str] = []
    prev_pages: List[int] = []
    prev_index = None
    prev_model_id = _load_embedder_id()

    if (STORE_DIR / "faiss.index").exists() and (STORE_DIR / "meta.json").exists():
        try:
            prev_index, prev_meta = _read_existing_index()
            prev_chunks = prev_meta.get("chunks", [])
            prev_sources = prev_meta.get("sources", ["unknown"] * len(prev_chunks))
            prev_pages = prev_meta.get("pages", [1] * len(prev_chunks))
        except Exception:
            prev_index = None
            prev_chunks, prev_sources, prev_pages = [], [], []

    # 2) Extracción nueva EN PARALELO
    new_chunks: List[str] = []
    new_sources: List[str] = []
    new_pages: List[int] = []

    max_workers = min(8, (os.cpu_count() or 4))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for chunks_triplets in ex.map(_extract_file_chunks, files):
            for ch, src, pg in chunks_triplets:
                new_chunks.append(ch)
                new_sources.append(src)
                new_pages.append(pg)

    # --- NUEVO: deduplicación *intra-batch* (evita duplicados idénticos en esta corrida)
    seen_keys = set()
    uniq_chunks, uniq_sources, uniq_pages = [], [], []
    for ch, s, p in zip(new_chunks, new_sources, new_pages):
        k = _hash_key(s or "unknown", int(p or 1), ch or "")
        if k in seen_keys:
            continue
        seen_keys.add(k)
        uniq_chunks.append(ch)
        uniq_sources.append(s)
        uniq_pages.append(p)
    new_chunks, new_sources, new_pages = uniq_chunks, uniq_sources, uniq_pages

    # 3) DEDUP contra lo previo
    def _build_keys(chs: List[str], srcs: List[str], pgs: List[int]) -> Dict[str, int]:
        d: Dict[str, int] = {}
        for i, (t, s, p) in enumerate(zip(chs, srcs, pgs)):
            d[_hash_key(s or "unknown", int(p or 1), t or "")] = i
        return d

    prev_keys = _build_keys(prev_chunks, prev_sources, prev_pages) if prev_chunks else {}
    dedup_new: List[Tuple[str, str, int]] = []
    for ch, s, p in zip(new_chunks, new_sources, new_pages):
        k = _hash_key(s or "unknown", int(p or 1), ch or "")
        if k not in prev_keys:
            dedup_new.append((ch, s, p))

    new_chunks = [x[0] for x in dedup_new]
    new_sources = [x[1] for x in dedup_new]
    new_pages   = [x[2] for x in dedup_new]

    # 4) Reconstruir o append
    embedder = _Embedder(EMBEDDING_MODEL_ID, STORE_DIR / "embed_cache")

    if prev_index is None or (prev_model_id and prev_model_id != EMBEDDING_MODEL_ID):
        # Rebuild total
        all_chunks = prev_chunks + new_chunks if prev_index is not None else new_chunks
        all_sources = prev_sources + new_sources if prev_index is not None else new_sources
        all_pages = prev_pages + new_pages if prev_index is not None else new_pages

        if not all_chunks:
            raise ValueError("No hay contenido para indexar.")

        X = embedder.encode_docs(all_chunks)
        faiss.normalize_L2(X)
        index = faiss.IndexFlatIP(X.shape[1])
        index.add(X.astype(np.float32))
        _save_index_and_meta(index, all_chunks, all_sources, all_pages, EMBEDDING_MODEL_ID)
        return index, all_chunks, all_sources, all_pages
    else:
        # Append incremental
        if prev_index is None:
            raise RuntimeError("Estado inconsistente del índice previo.")
        index = prev_index
        all_chunks = prev_chunks
        all_sources = prev_sources
        all_pages = prev_pages

        if new_chunks:
            X_new = embedder.encode_docs(new_chunks)
            faiss.normalize_L2(X_new)
            index.add(X_new.astype(np.float32))
            all_chunks = prev_chunks + new_chunks
            all_sources = prev_sources + new_sources
            all_pages = prev_pages + new_pages

        _save_index_and_meta(index, all_chunks, all_sources, all_pages, EMBEDDING_MODEL_ID)
        return index, all_chunks, all_sources, all_pages

# =========================
# Helpers: reconstrucción / carga segura
# =========================

def _current_embed_dim() -> int:
    emb = _Embedder(EMBEDDING_MODEL_ID, STORE_DIR / "embed_cache")
    try:
        return emb.model.get_sentence_embedding_dimension()
    except Exception:
        v = emb.encode_docs(["probe"])
        return int(v.shape[1])

def rebuild_index_from_meta() -> tuple:
    """Re-embebe todos los chunks de meta.json con el modelo actual y guarda un índice nuevo."""
    meta_path = STORE_DIR / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError("No existe meta.json para reconstruir el índice.")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    chunks = meta.get("chunks", [])
    sources = meta.get("sources", ["unknown"] * len(chunks))
    pages = meta.get("pages", [1] * len(chunks))

    emb = _Embedder(EMBEDDING_MODEL_ID, STORE_DIR / "embed_cache")
    X = emb.encode_docs(chunks)
    faiss.normalize_L2(X)
    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X.astype(np.float32))
    _save_index_and_meta(index, chunks, sources, pages, EMBEDDING_MODEL_ID)
    return index, chunks, sources, pages

def load_index() -> Tuple[faiss.IndexFlatIP, List[str], List[str], List[int]]:
    """Versión simple (mantengo por compatibilidad)."""
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"
    if not index_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Aún no hay índice. Ingresa documentos primero.")
    index = faiss.read_index(str(index_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    chunks = meta.get("chunks", [])
    sources = meta.get("sources", ["unknown"] * len(chunks))
    pages = meta.get("pages", [1] * len(chunks))
    ln = len(chunks)
    if len(sources) != ln:
        sources = (sources + ["unknown"] * ln)[:ln]
    if len(pages) != ln:
        pages = (pages + [1] * ln)[:ln]
    return index, chunks, sources, pages

def load_index_safe() -> tuple:
    """
    Carga el índice y verifica dimensión/modelo; si no coincide, reconstruye desde meta.json.
    Úsalo en app.py para evitar AssertionError al cambiar de embedder.
    """
    index_path = STORE_DIR / "faiss.index"
    meta_path = STORE_DIR / "meta.json"
    cfg_path = STORE_DIR / "embedder_config.json"

    if not index_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Aún no hay índice. Ingresa documentos primero.")

    index = faiss.read_index(str(index_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    chunks = meta.get("chunks", [])
    sources = meta.get("sources", ["unknown"] * len(chunks))
    pages = meta.get("pages", [1] * len(chunks))

    prev_model = None
    if cfg_path.exists():
        try:
            prev_model = json.loads(cfg_path.read_text(encoding="utf-8")).get("model_id")
        except Exception:
            prev_model = None

    cur_model = EMBEDDING_MODEL_ID
    cur_dim = _current_embed_dim()
    idx_dim = getattr(index, "d", None)

    # Si cambió el modelo o la dimensión no coincide, reconstruye
    if prev_model and prev_model != cur_model:
        return rebuild_index_from_meta()
    if idx_dim is None or idx_dim != cur_dim:
        return rebuild_index_from_meta()

    ln = len(chunks)
    if len(sources) != ln:
        sources = (sources + ["unknown"] * ln)[:ln]
    if len(pages) != ln:
        pages = (pages + [1] * ln)[:ln]

    return index, chunks, sources, pages
