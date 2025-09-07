from __future__ import annotations
"""
RAG core helpers: búsqueda semántica + construcción de prompt + generación con LLM local (llama.cpp).

- Usa FAISS para recuperación top-k con filtro opcional por archivo (source).
- Construye un prompt Instruct con contexto + reglas (idioma, estilo, citas).
- Recorta el contexto para no exceder N_CTX del modelo.
- Genera respuesta con llama.cpp (modelo GGUF local).
"""

from typing import List, Tuple, Optional

import faiss
import numpy as np
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer

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
    """Carga el modelo de embeddings (cache local)."""
    return SentenceTransformer(
        EMBEDDING_MODEL_ID,
        cache_folder=str(EMBED_CACHE_DIR),
    )

def _load_llm() -> Llama:
    """Carga el LLM (GGUF) con llama.cpp, ajustado para menor uso de RAM."""
    return Llama(
        model_path=LLM_MODEL_PATH,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        n_batch=64,        # lotes pequeños ↓ RAM (prueba 32 si aún falta)
        logits_all=False,  # no guardar logits de todo el contexto
        embedding=False,   # no usar modo embeddings aquí
        use_mmap=True,     # mapea el archivo del modelo
        use_mlock=False,   # en Windows no aplica
        verbose=False,
    )

# =====================
# Búsqueda vectorial (con filtro opcional por archivo)
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
    """Top-k (con filtro opcional por filename)."""
    model = _load_embedder()
    q = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)

    # Si hay filtro, pedimos más candidatos y luego filtramos
    nprobe = max(k, k * 6) if filter_source else k
    D, I = index.search(q, nprobe)

    def match_src(idx: int) -> bool:
        if not filter_source or not sources:
            return True
        return filter_source.lower() in (sources[idx] or "").lower()

    results: List[Tuple[int, float, str]] = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx == -1:
            continue
        if match_src(idx):
            results.append((idx, float(score), chunks[idx]))
            if len(results) >= k:
                break

    # Si no hubo resultados con filtro, cae a sin filtro
    if not results and filter_source:
        for score, idx in zip(D[0].tolist(), I[0].tolist()):
            if idx == -1:
                continue
            results.append((idx, float(score), chunks[idx]))
            if len(results) >= k:
                break

    return results

# =====================
# Prompting (idioma + estilo + citas)
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
    """Heurística mínima para reforzar idioma español; si no, usa idioma de la pregunta."""
    es_markers = ["¿", "¡", "ñ", "á", "é", "í", "ó", "ú"]
    if any(ch in query for ch in es_markers):
        return "IDIOMA_RESPUESTA: español"
    return "IDIOMA_RESPUESTA: mismo idioma de la pregunta"

def _style_hint(query: str) -> str:
    """Sugerencia de estilo: lista si la pregunta pide pasos/procedimiento."""
    q = query.lower()
    if any(kw in q for kw in ["pasos", "cómo", "lista", "procedimiento", "instrucciones"]):
        return "ESTILO: lista numerada breve"
    return "ESTILO: párrafo(s) breves"

def _format_prompt(query: str, passages: List[Tuple[int, float, str]]) -> str:
    """Construye el prompt sin recorte (sin <s> para evitar el warning)."""
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

    # OJO: no anteponemos "<s>" para evitar "duplicate <s>"
    prompt = (
        f"[INST] <<SYS>>\n{SYS_PROMPT}\n<</SYS>>\n\n"
        f"CONTEXTO:\n{context}\n\n"
        f"{user} [/INST]"
    )
    return prompt

# ---- utilidades de recorte por tokens ----

def _count_tokens(llm: Llama, text: str) -> int:
    """Cuenta tokens con el tokenizer real del modelo."""
    return len(llm.tokenize(text.encode("utf-8"), add_bos=True))

def build_prompt_clipped(
    llm: Llama,
    query: str,
    passages: List[Tuple[int, float, str]],
    ctx_limit: int = N_CTX,
    max_new_tokens: int = MAX_TOKENS,
    margin: int = 64,
) -> str:
    """
    Incluye pasajes uno a uno hasta no exceder (ctx_limit - max_new_tokens - margin).
    Si ningún pasaje cabe, devuelve prompt con el primero truncado.
    """
    selected: List[Tuple[int, float, str]] = []
    base_prompt = _format_prompt(query, [])
    budget = ctx_limit - max_new_tokens - margin
    if budget < 200:
        budget = max(128, ctx_limit // 4)

    # agregar pasajes mientras quepa
    for p in passages:
        tmp = _format_prompt(query, selected + [p])
        if _count_tokens(llm, tmp) <= budget:
            selected.append(p)
        else:
            break

    # si no cupo ninguno, forzar con el primero truncado por caracteres
    if not selected and passages:
        idx, sc, txt = passages[0]
        for cut in (2000, 1500, 1000, 700, 500, 300):
            tmp = _format_prompt(query, [(idx, sc, txt[:cut])])
            if _count_tokens(llm, tmp) <= budget:
                selected = [(idx, sc, txt[:cut])]
                break
        if not selected:
            return base_prompt  # sin contexto, el modelo responderá "No está…"

    return _format_prompt(query, selected)

# =====================
# Generación
# =====================

def generate_answer(llm: Llama, prompt: str) -> str:
    """Genera respuesta concisa. Controla temperatura y tokens."""
    out = llm(
        prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        stop=["</s>", "[/INST]"],
    )
    return out["choices"][0]["text"].strip()
