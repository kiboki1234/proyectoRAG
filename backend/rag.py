from __future__ import annotations
"""
RAG core helpers:
- Recuperación híbrida (FAISS + BM25) con rerank de cross-encoder
- Filtro estricto por archivo
- Prompt en formato Mistral-Instruct [INST] con guardrails anti-alucinación
- Clipping por tokens REALES (llama.tokenize) para no exceder N_CTX
- Generación segura con tope dinámico de max_tokens
"""
from typing import List, Tuple, Optional
import numpy as np
import faiss
import regex as re
from rank_bm25 import BM25Okapi
from llama_cpp import Llama

from config import (
    TOP_K,
    EMBEDDING_MODEL_ID,
    LLM_MODEL_PATH,
    N_CTX,
    N_THREADS,
    TEMPERATURE,
    MAX_TOKENS,
)
from enhanced_retrieval import EmbeddingConfig, HybridEmbedder, CrossEncoderReranker

# =====================
# Carga perezosa
# =====================

_EMB: Optional[HybridEmbedder] = None
_RER: Optional[CrossEncoderReranker] = None
_LLM: Optional[Llama] = None

_bm25: Optional[BM25Okapi] = None
_bm25_len: int = 0
_bm25_corpus_tokens: List[List[str]] = []

def _load_embedder() -> HybridEmbedder:
    global _EMB
    if _EMB is None:
        cfg = EmbeddingConfig(model_id=EMBEDDING_MODEL_ID)
        from pathlib import Path
        from config import STORE_DIR
        _EMB = HybridEmbedder(cfg, STORE_DIR / "embed_cache")
    return _EMB

def _get_reranker() -> CrossEncoderReranker:
    global _RER
    if _RER is None:
        _RER = CrossEncoderReranker()
    return _RER

def _load_llm() -> Llama:
    """Expuesto para app.py si necesitas forzar la carga."""
    global _LLM
    if _LLM is None:
        _LLM = Llama(
            model_path=LLM_MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            verbose=False,
        )
    return _LLM

# =====================
# BM25 utils
# =====================

def _simple_tokens(text: str) -> List[str]:
    return re.findall(r"\p{L}+\p{M}*|\d+[.,]?\d*", (text or "").lower())

def _ensure_bm25(chunks: List[str]) -> BM25Okapi:
    global _bm25, _bm25_len, _bm25_corpus_tokens
    if _bm25 is None or _bm25_len != len(chunks):
        _bm25_corpus_tokens = [_simple_tokens(c) for c in chunks]
        _bm25 = BM25Okapi(_bm25_corpus_tokens)
        _bm25_len = len(chunks)
    return _bm25

def _bm25_topk(chunks: List[str], query: str, topn: int = 50) -> List[int]:
    bm25 = _ensure_bm25(chunks)
    scores = bm25.get_scores(_simple_tokens(query))
    idxs = np.argsort(scores)[::-1][:topn]
    return idxs.tolist()

# =====================
# Seguridad de dimensión FAISS
# =====================

def _ensure_dim_match(index, qv: np.ndarray):
    idx_d = getattr(index, "d", None)
    q_d = int(qv.shape[1])
    if idx_d is None or idx_d != q_d:
        raise ValueError(
            f"Dimensión de embeddings incompatible: índice={idx_d}, consulta={q_d}. "
            "El índice fue creado con otro modelo. Reconstruye la ingesta."
        )

# =====================
# Recuperación híbrida + rerank
# =====================

def search(
    index,
    chunks: List[str],
    query: str,
    k: int = TOP_K,
    *,
    sources: Optional[List[str]] = None,
    filter_source: Optional[str] = None,
) -> List[Tuple[int, float, str]]:
    """
    Devuelve [(idx_chunk, score, texto_chunk)] ya rerankeados con cross-encoder.
    Si filter_source se proporciona, aplica filtro estricto por nombre de archivo.
    """
    if not chunks:
        return []

    # 1) Vectorial de alto recall
    emb = _load_embedder()
    qv = emb.encode_query(query).reshape(1, -1).astype(np.float32)
    _ensure_dim_match(index, qv)  # evita AssertionError d != self.d
    kk = min(max(k * 8, 80), len(chunks))
    D, I = index.search(qv, kk)
    vec_cands = [(int(i), float(d), chunks[int(i)]) for i, d in zip(I[0], D[0]) if int(i) >= 0]

    # 2) BM25
    bm25_idxs = _bm25_topk(chunks, query, topn=min(max(k * 6, 60), len(chunks)))
    bm25_cands = [(i, 0.0, chunks[i]) for i in bm25_idxs]

    # 3) Unión preservando orden (vectorial primero), sin duplicados
    seen = set()
    merged: List[Tuple[int, float, str]] = []
    for cand in vec_cands + bm25_cands:
        if cand[0] not in seen:
            merged.append(cand)
            seen.add(cand[0])

    # 4) Filtro por archivo (exacto -> contiene)
    if filter_source and sources:
        fs = filter_source.strip().lower()
        exact = [c for c in merged if (sources[c[0]] or "").lower() == fs]
        if not exact:
            exact = [c for c in merged if fs in (sources[c[0]] or "").lower()]
        merged = exact
        if not merged:
            return []

    # 5) Rerank cross-encoder y recorte a k
    rer = _get_reranker()
    ranked = rer.rerank(query, merged, top_k=k)
    return ranked[:k]

# =====================
# Prompting y control de tokens (llama.cpp)
# =====================

def _language_hint(question: str) -> str:
    tokens = _simple_tokens(question)
    non_ascii = sum(1 for t in tokens if re.search(r"[áéíóúñü]", t))
    return "es" if non_ascii >= max(1, int(0.1 * len(tokens))) else "es"

# --- helpers de tokens seguros ---
def _tok_len(llm: Llama, text: str) -> int:
    try:
        return len(llm.tokenize(text.encode("utf-8")))
    except Exception:
        return int(len(re.findall(r"\S+", text)) / 0.7) + 1

def _safe_max_new_tokens(llm: Llama, prompt: str, *, min_answer: int = 32) -> int:
    """Máx. tokens de salida que caben sin pasar N_CTX."""
    used = _tok_len(llm, prompt)
    room = max(0, N_CTX - used - 16)  # margen por tokens especiales
    if room < min_answer:
        return max(8, room)  # nunca 0
    return min(MAX_TOKENS, room)

# --- NUEVO: plantilla Mistral-Instruct + guardrails anti-alucinación ---
def _format_prompt_inst(question: str, contexts: List[str]) -> str:
    sys = (
        "Eres un asistente PRECISO. Responde SOLO con información que esté en los "
        "fragmentos proporcionados. No inventes nada. "
        "Si el contexto no contiene la respuesta, escribe EXACTAMENTE: "
        "\"No hay información suficiente en el contexto.\""
    )
    sep = "\n\n"
    ctx_block = sep.join([f"[{i+1}] {c.strip()}" for i, c in enumerate(contexts) if c and c.strip()])
    user = (
        "Usa EXCLUSIVAMENTE los fragmentos anteriores. "
        "Responde en español, de forma breve y directa. "
        f"Pregunta: {question.strip()}"
    )
    # Plantilla Mistral-Instruct
    return f"<s>[INST] <<SYS>>\n{sys}\n<</SYS>>\n\nContexto:\n{ctx_block}\n\n{user} [/INST]"

def build_prompt_clipped(llm: Llama, question: str, passages: List[Tuple[int, float, str]]) -> str:
    """
    Construye el prompt midiendo tokens REALES con llama.tokenize.
    Agrega pasajes hasta un presupuesto y envuelve en formato [INST].
    """
    target_prompt_budget = int(N_CTX * 0.65)  # deja ~35% para la respuesta
    contexts: List[str] = []

    for _, _, txt in passages:
        t = (txt or "").strip()
        if not t:
            continue
        candidate = contexts + [t]
        probe = _format_prompt_inst(question, candidate)
        if _tok_len(_load_llm(), probe) <= target_prompt_budget:
            contexts = candidate
        else:
            break

    # Si no cupo nada, igual valida con las reglas del sistema
    return _format_prompt_inst(question, contexts)

# =====================
# Generación
# =====================

def generate_answer(
    llm: Llama,
    prompt: str,
    *,
    temp: float | None = None,
    max_tokens: int | None = None,
    stop: Optional[List[str]] = None,
) -> str:
    temperature = TEMPERATURE if temp is None else float(temp)
    # Capamos al espacio real disponible
    max_new = _safe_max_new_tokens(llm, prompt, min_answer=32) if max_tokens is None else int(max_tokens)
    if max_tokens is None and max_new < 8:
        max_new = _safe_max_new_tokens(llm, prompt, min_answer=8)
    # Mistral-Instruct suele cerrar con </s>
    stop = stop or ["</s>"]

    out = llm(
        prompt,
        max_tokens=max_new,
        temperature=temperature,
        stop=stop,
    )
    return out["choices"][0]["text"].strip()
