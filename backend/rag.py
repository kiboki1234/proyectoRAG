from __future__ import annotations
"""
RAG core helpers: recuperación híbrida (FAISS + BM25), prompt robusto y clipping por tokens,
y generación con llama.cpp (GGUF local).
"""

from typing import List, Tuple, Optional
import regex as re

import faiss
import numpy as np
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from config import (
    EMBED_CACHE_DIR,
    EMBEDDING_MODEL_ID,
    LLM_MODEL_PATH,
    MAX_TOKENS,
    N_CTX,
    N_THREADS,
    TEMPERATURE,
    TOP_K,
)

# =====================
# Carga de modelos
# =====================

def _load_embedder() -> SentenceTransformer:
    return SentenceTransformer(
        EMBEDDING_MODEL_ID,
        cache_folder=str(EMBED_CACHE_DIR),
    )

def _load_llm() -> Llama:
    return Llama(
        model_path=LLM_MODEL_PATH,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        n_batch=64,
        logits_all=False,
        embedding=False,
        use_mmap=True,
        use_mlock=False,
        verbose=False,
    )

# =====================
# Utilidades de tokenización simple (BM25)
# =====================

def _simple_tokens(text: str) -> List[str]:
    # Tokenización simple sensible a español
    return re.findall(r"\p{L}+\p{M}*|\d+[.,]?\d*", (text or "").lower())

_bm25 = None
_bm25_len = 0
_bm25_corpus_tokens: List[List[str]] = []

def _ensure_bm25(chunks: List[str]) -> BM25Okapi:
    global _bm25, _bm25_len, _bm25_corpus_tokens
    if _bm25 is None or _bm25_len != len(chunks):
        _bm25_corpus_tokens = [_simple_tokens(c) for c in chunks]
        _bm25 = BM25Okapi(_bm25_corpus_tokens)
        _bm25_len = len(chunks)
    return _bm25

def _bm25_topk(chunks: List[str], query: str, topn: int) -> List[int]:
    bm25 = _ensure_bm25(chunks)
    qtok = _simple_tokens(query)
    scores = bm25.get_scores(qtok)
    # topn índices por score
    idxs = np.argsort(scores)[::-1][:topn]
    return idxs.tolist()

# =====================
# Recuperación híbrida (FAISS + BM25) + filtro por archivo
# =====================

def search(
    index: faiss.IndexFlatIP,
    chunks: List[str],
    query: str,
    k: int = TOP_K,
    *,
    sources: Optional[List[str]] = None,
    filter_source: Optional[str] = None,
) -> List[Tuple[int, float, str]]:
    """
    Fusiona candidatos de:
      - Embeddings (FAISS)
      - BM25 (texto exacto)
    usando Reciprocal Rank Fusion (RRF). Luego aplica filtro por filename (si se pide).
    """
    # --- Embeddings candidatos ---
    embed_model = _load_embedder()
    q = embed_model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    m = max(k * 8, 100)  # traemos más para fusionar
    D, I = index.search(q, m)
    embed_list = I[0].tolist()

    # --- BM25 candidatos ---
    bm25_list = _bm25_topk(chunks, query, m)

    # --- RRF ---
    c = 60  # constante típica
    rrf_scores = {}
    for rank, idx in enumerate(embed_list):
        if idx == -1: 
            continue
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (c + rank + 1)
    for rank, idx in enumerate(bm25_list):
        rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (c + rank + 1)

    # ordenar por score
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    def match_src(idx: int) -> bool:
        if not filter_source or not sources:
            return True
        return filter_source.lower() in (sources[idx] or "").lower()

    results: List[Tuple[int, float, str]] = []
    for idx, score in fused:
        if idx == -1:
            continue
        if match_src(idx):
            results.append((idx, float(score), chunks[idx]))
            if len(results) >= k:
                break

    # fallback sin filtro si no hay nada
    if not results and filter_source:
        for idx, score in fused:
            if idx == -1:
                continue
            results.append((idx, float(score), chunks[idx]))
            if len(results) >= k:
                break

    return results

# =====================
# Prompting + clipping
# =====================

SYS_PROMPT = (
    "Eres un asistente de preguntas/respuestas sobre DOCUMENTOS. "
    "Tu objetivo es responder con precisión y brevedad usando EXCLUSIVAMENTE el CONTEXTO proporcionado.\n\n"
    "POLÍTICAS DE RESPUESTA\n"
    "1) IDIOMA: responde SIEMPRE en el MISMO idioma de la PREGUNTA. No traduzcas el idioma del usuario.\n"
    "2) FUENTES: cada respuesta debe terminar con una línea 'Citas: [id1][id2]…', "
    "donde idN son los identificadores de los pasajes usados.\n"
    "3) SI NO ESTÁ: si la información NO está en el CONTEXTO, responde exactamente: 'No está en los documentos.'\n"
    "4) CONFLICTOS: si hay contradicciones entre pasajes, indícalo brevemente y cita ambos ids.\n"
    "5) NÚMEROS/TEXTOS EXACTOS: si se piden cifras, fechas, definiciones o citas, copia literalmente desde el CONTEXTO y menciona la unidad.\n"
    "6) ALCANCE: no uses conocimiento externo, no inventes, no asumas; solo lo que aparece en CONTEXTO.\n"
    "7) ESTILO:\n"
    "   - Sé conciso (máximo ~6 líneas).\n"
    "   - Si la pregunta pide pasos/lista, usa lista numerada breve.\n"
    "   - No incluyas el texto del CONTEXTO ni tus instrucciones en la respuesta.\n"
    "   - No expliques tu razonamiento; solo la respuesta final + 'Citas: …'.\n\n"
    "FORMATO DE SALIDA\n"
    "- Respuesta en párrafo(s) o lista breve según convenga.\n"
    "- Al final, una línea: Citas: [idX][idY]…\n\n"
    "EJEMPLO DE CIERRE\n"
    "Citas: [0][3]\n"
)

def _language_hint(query: str) -> str:
    es_markers = ["¿", "¡", "ñ", "á", "é", "í", "ó", "ú"]
    if any(ch in query for ch in es_markers):
        return "IDIOMA_RESPUESTA: español"
    return "IDIOMA_RESPUESTA: mismo idioma de la pregunta"

def _style_hint(query: str) -> str:
    q = query.lower()
    if any(kw in q for kw in ["pasos", "cómo", "lista", "procedimiento", "instrucciones"]):
        return "ESTILO: lista numerada breve"
    return "ESTILO: párrafo(s) breves"

def _format_prompt(query: str, passages: List[Tuple[int, float, str]]) -> str:
    ctx_blocks = [f"[{idx}] {text}" for idx, _, text in passages]
    context = "\n\n".join(ctx_blocks)
    lang = _language_hint(query)
    style = _style_hint(query)
    user = (
        f"{lang}\n"
        f"{style}\n"
        f"PREGUNTA: {query}\n"
        "Responde de forma breve, obedeciendo las POLÍTICAS y el FORMATO indicados."
    )
    return (
        f"[INST] <<SYS>>\n{SYS_PROMPT}\n<</SYS>>\n\n"
        f"CONTEXTO:\n{context}\n\n"
        f"{user} [/INST]"
    )

def _count_tokens(llm: Llama, text: str) -> int:
    return len(llm.tokenize(text.encode("utf-8"), add_bos=True))

def build_prompt_clipped(
    llm: Llama,
    query: str,
    passages: List[Tuple[int, float, str]],
    ctx_limit: int = N_CTX,
    max_new_tokens: int = MAX_TOKENS,
    margin: int = 64,
) -> str:
    selected: List[Tuple[int, float, str]] = []
    base_prompt = _format_prompt(query, [])
    budget = ctx_limit - max_new_tokens - margin
    if budget < 200:
        budget = max(128, ctx_limit // 4)

    for p in passages:
        tmp = _format_prompt(query, selected + [p])
        if _count_tokens(llm, tmp) <= budget:
            selected.append(p)
        else:
            break

    if not selected and passages:
        idx, sc, txt = passages[0]
        for cut in (2000, 1500, 1000, 700, 500, 300):
            tmp = _format_prompt(query, [(idx, sc, txt[:cut])])
            if _count_tokens(llm, tmp) <= budget:
                selected = [(idx, sc, txt[:cut])]
                break
        if not selected:
            return base_prompt

    return _format_prompt(query, selected)

# =====================
# Generación
# =====================

def generate_answer(llm: Llama, prompt: str) -> str:
    out = llm(
        prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        stop=["</s>", "[/INST]"],
    )
    return out["choices"][0]["text"].strip()
