# backend/enhanced_retrieval.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import regex as re
import numpy as np
from pathlib import Path

# ============ METADATA ============

@dataclass
class ChunkMetadata:
    source: str
    page: int
    section: Optional[str] = None
    chunk_type: str = "text"  # text|table|list|header
    confidence: float = 1.0

# ============ LIMPIEZA + CHUNKING ============

def _clean_text(s: str) -> str:
    if not s: return ""
    s = s.replace("\xa0", " ")
    s = re.sub(r"-\s*\n\s*", "", s)
    s = re.sub(r"[ \t]+", " ", s)
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
    rm_top = set([t for t,c in top_counts.items() if c >= thr])
    rm_bot = set([b for b,c in bot_counts.items() if c >= thr])

    out = []
    for p in pages:
        lines = [ln for ln in (p or "").splitlines()]
        if not lines: out.append(""); continue
        for t in rm_top:
            if tuple([ln.strip() for ln in lines[:len(t)]]) == t:
                lines = lines[len(t):]; break
        for b in rm_bot:
            if tuple([ln.strip() for ln in lines[-len(b):]]) == b:
                lines = lines[:-len(b)]; break
        out.append(_clean_text("\n".join(lines)))
    return out

class SmartChunker:
    def __init__(self, max_chunk_size=800, min_chunk_size=200, overlap_sentences=2):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_sentences = overlap_sentences

    def _detect_content_type(self, text: str) -> str:
        if re.search(r'[\|\+\-]{3,}', text) or text.count('|') > 5: return "table"
        if re.search(r'^\s*[\-\*\•]\s+', text, re.MULTILINE) or re.search(r'^\s*\d+\.\s+', text, re.MULTILINE): return "list"
        if len(text) < 100 and text.strip().isupper(): return "header"
        return "text"

    def _split_sentences(self, text: str) -> List[str]:
        abbrev = r'\b(?:Sr|Sra|Dr|Dra|Ing|Lic|etc|p|pp|Fig|Ref|No)\.'
        protected = re.sub(abbrev, lambda m: m.group().replace('.', '<DOT>'), text)
        parts = re.split(r'(?<=[.!?])\s+', protected)
        return [p.replace('<DOT>', '.').strip() for p in parts if p.strip()]

    def _smart_split(self, text: str) -> List[str]:
        sents = self._split_sentences(text)
        out, cur = [], []
        cur_len = 0
        for s in sents:
            if len(s) > self.max_chunk_size:
                if cur: out.append(" ".join(cur)); cur, cur_len = [], 0
                # corte forzado con pequeño solape
                step = self.max_chunk_size - 50
                for i in range(0, len(s), step):
                    out.append(s[i:i+self.max_chunk_size])
                continue
            if cur_len + len(s) > self.max_chunk_size:
                out.append(" ".join(cur))
                cur = cur[-self.overlap_sentences:] if self.overlap_sentences else []
                cur_len = sum(len(x) for x in cur)
            cur.append(s); cur_len += len(s)
        if cur: out.append(" ".join(cur))
        return out

    def chunk_page(self, page_text: str, meta_base: ChunkMetadata) -> List[Tuple[str, ChunkMetadata]]:
        txt = _clean_text(page_text)
        if len(txt) <= self.max_chunk_size:
            return [(txt, ChunkMetadata(**meta_base.__dict__, chunk_type=self._detect_content_type(txt)))]
        chunks = []
        for c in self._smart_split(txt):
            chunks.append((c, ChunkMetadata(**meta_base.__dict__, chunk_type=self._detect_content_type(c))))
        return chunks

def enhanced_pdf_extraction(path: Path) -> List[Tuple[str, ChunkMetadata]]:
    pages: List[str] = []
    try:
        import fitz
        doc = fitz.open(str(path))
        for pg in doc:
            blocks = pg.get_text("blocks")
            blocks = sorted(blocks, key=lambda b: (round(b[1],1), round(b[0],1)))
            pages.append(_clean_text("\n".join([b[4] for b in blocks if len(b)>4 and b[4]])))
        doc.close()
    except Exception:
        # fallback simple
        try:
            from pypdf import PdfReader
            r = PdfReader(str(path)); pages = [(p.extract_text() or "") for p in r.pages]
        except Exception:
            pages = []

    pages = _strip_headers_footers(pages)
    chunker = SmartChunker()
    all_chunks: List[Tuple[str, ChunkMetadata]] = []
    for i, ptxt in enumerate(pages, start=1):
        base = ChunkMetadata(source=path.name, page=i)
        all_chunks.extend(chunker.chunk_page(ptxt, base))
    return all_chunks

# ============ EMBEDDINGS + RERANK ============

class EmbeddingConfig:
    def __init__(self,
                 model_id: str = "intfloat/multilingual-e5-base",
                 normalize: bool = True,
                 batch_size: int = 32):
        self.model_id = model_id
        self.normalize = normalize
        self.batch_size = batch_size

class HybridEmbedder:
    def __init__(self, config: EmbeddingConfig, cache_dir: Path):
        from sentence_transformers import SentenceTransformer
        self.cfg = config
        self.cache_dir = cache_dir
        self.model = SentenceTransformer(self.cfg.model_id, cache_folder=str(cache_dir))

    def _wrap_doc(self, text: str) -> str:
        mid = self.cfg.model_id.lower()
        if "e5" in mid or "bge" in mid:
            return f"passage: {text}"
        return text

    def _wrap_query(self, q: str) -> str:
        mid = self.cfg.model_id.lower()
        if "e5" in mid or "bge" in mid:
            return f"query: {q}"
        return q

    def encode_documents(self, texts: List[str]) -> np.ndarray:
        X = [self._wrap_doc(t) for t in texts]
        emb = self.model.encode(X, normalize_embeddings=self.cfg.normalize, convert_to_numpy=True, batch_size=self.cfg.batch_size)
        return emb

    def encode_query(self, q: str) -> np.ndarray:
        e = self.model.encode([self._wrap_query(q)], normalize_embeddings=self.cfg.normalize, convert_to_numpy=True)
        return e[0]

class CrossEncoderReranker:
    def __init__(self):
        self.model = None
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder("jinaai/jina-reranker-v2-base-multilingual")
        except Exception:
            # fallback inglés
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            except Exception:
                self.model = None

    def rerank(self, query: str, passages: List[Tuple[int,float,str]], top_k:int) -> List[Tuple[int,float,str]]:
        if not self.model or not passages: return passages[:top_k]
        pairs = [[query, p[2]] for p in passages[: min(64, len(passages))]]
        scores = self.model.predict(pairs)
        order = np.argsort(scores)[::-1]
        return [passages[i] for i in order[:top_k]]

class DenseRetriever:
    def __init__(self, embedder: HybridEmbedder, use_rerank: bool = True):
        self.embedder = embedder
        self.rerank = CrossEncoderReranker() if use_rerank else None

    def search(self, index, chunks: List[str], query: str, k:int=6) -> List[Tuple[int,float,str]]:
        qv = self.embedder.encode_query(query).reshape(1,-1).astype(np.float32)
        kk = min(max(k*5, 50), len(chunks))
        D, I = index.search(qv, kk)
        cands = [(int(i), float(d), chunks[int(i)]) for i,d in zip(I[0], D[0]) if int(i) >= 0]
        if self.rerank:
            cands = self.rerank.rerank(query, cands, k)
        return cands[:k]

# ============ ÍNDICE ============

def create_enhanced_index(chunks: List[str], store_dir: Path, model_id: str) -> Tuple:
    import faiss, json
    cfg = EmbeddingConfig(model_id=model_id)
    emb = HybridEmbedder(cfg, store_dir / "embed_cache")
    X = emb.encode_documents(chunks)
    faiss.normalize_L2(X)
    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X.astype(np.float32))
    faiss.write_index(index, str(store_dir / "faiss.index"))
    (store_dir / "embedder_config.json").write_text(json.dumps({"model_id": model_id}), encoding="utf-8")
    return index, emb
