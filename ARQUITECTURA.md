# 🏗️ Arquitectura del Sistema RAG - v2.0

## Vista General

```
┌─────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React + TS)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  ChatPanel   │  │ DocumentView │  │  Header      │          │
│  │ (Historial)  │  │ (PDF/MD/TXT) │  │ + StatusBadge│          │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘          │
│         │                                     │                   │
│  ┌──────▼──────────────────────────────────▼──────┐            │
│  │          SettingsModal (Dashboard)             │            │
│  │  📊 Stats  │  💾 Cache  │  📚 Documents       │            │
│  └────────────────────────────────────────────────┘            │
│                                                                   │
│  ┌────────────────────────────────────────────────┐            │
│  │         SourcesSelect (Enriquecido)            │            │
│  │  📚 Todos | 📄 doc1.pdf (50 chunks)           │            │
│  └────────────────────────────────────────────────┘            │
│                                                                   │
│  ┌────────────────────────────────────────────────┐            │
│  │         MarkdownRenderer (ReactMarkdown)       │            │
│  │  Listas, Negrita, Código, Tablas...           │            │
│  └────────────────────────────────────────────────┘            │
│                                                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/REST + SSE
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 API Endpoints                             │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  POST /ask          → Query con respuesta normal         │   │
│  │  POST /ask/stream   → Query con SSE (token-by-token)     │   │
│  │  GET  /health       → Estado del sistema                 │   │
│  │  GET  /stats        → Estadísticas (docs, chunks, etc)   │   │
│  │  GET  /cache/stats  → Métricas del caché                 │   │
│  │  GET  /documents    → Lista de documentos indexados      │   │
│  │  POST /ingest       → Subir y procesar documentos        │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │              QueryCache (Thread-safe LRU)                │   │
│  │  • TTL configurable                                      │   │
│  │  • Invalidación automática tras ingesta                 │   │
│  │  • Hit rate tracking                                     │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │              RAG Core (rag.py)                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  1. Búsqueda Híbrida                                     │   │
│  │     • FAISS (vector search)                              │   │
│  │     • BM25 (keyword search)                              │   │
│  │     • Union + Dedup                                      │   │
│  │                                                           │   │
│  │  2. Filtrado (opcional)                                  │   │
│  │     • source=None     → TODO el corpus                   │   │
│  │     • source="doc"    → Un documento específico          │   │
│  │     • search_mode     → single/multi/auto                │   │
│  │                                                           │   │
│  │  3. Diversificación (si multi-doc)                       │   │
│  │     • Balanceo round-robin entre fuentes                 │   │
│  │     • Evita sesgo hacia docs grandes                     │   │
│  │                                                           │   │
│  │  4. Reranking                                            │   │
│  │     • Cross-encoder (jina-reranker-v2)                   │   │
│  │     • Top-k final                                        │   │
│  │                                                           │   │
│  │  5. Prompt Building                                      │   │
│  │     • Token clipping (llama.tokenize)                    │   │
│  │     • Mistral-Instruct format [INST]...[/INST]           │   │
│  │     • Anti-hallucination guardrails                      │   │
│  │                                                           │   │
│  │  6. LLM Generation                                       │   │
│  │     • Temperatura auto-detectada                         │   │
│  │       - Factual: 0.0 (RUC, fecha, números)               │   │
│  │       - Balanceado: 0.3 (resumen, análisis)              │   │
│  │       - Creativo: 0.7 (sugerencias, ideas)               │   │
│  │     • Streaming opcional (SSE)                           │   │
│  │     • Safe max_tokens (no overflow)                      │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                             │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │           Ingestion Pipeline (ingest.py)                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  1. File Extraction (paralelo)                           │   │
│  │     • PDF → PyMuPDF (layout-aware)                       │   │
│  │     • MD → markdown + BeautifulSoup                      │   │
│  │     • TXT → directo                                      │   │
│  │                                                           │   │
│  │  2. Cleaning                                             │   │
│  │     • Strip headers/footers repetidos                    │   │
│  │     • Normalización de espacios                          │   │
│  │                                                           │   │
│  │  3. Smart Chunking                                       │   │
│  │     • Split por oraciones                                │   │
│  │     • Overlap configurable                               │   │
│  │     • Respeta límite de tamaño                           │   │
│  │                                                           │   │
│  │  4. Deduplicación                                        │   │
│  │     • Hash: (source, page, text)                         │   │
│  │     • Intra-batch + vs índice previo                     │   │
│  │                                                           │   │
│  │  5. Embedding                                            │   │
│  │     • Model: intfloat/multilingual-e5-base               │   │
│  │     • Wrapper: "passage: {text}"                         │   │
│  │     • Batch processing                                   │   │
│  │                                                           │   │
│  │  6. Indexing                                             │   │
│  │     • FAISS IndexFlatIP (cosine similarity)              │   │
│  │     • Incremental update o rebuild                       │   │
│  │     • Meta persistence (chunks, sources, pages)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ data/docs/   │  │ data/store/  │  │ data/models/ │          │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤          │
│  │ • PDFs       │  │ faiss.index  │  │ LLM (GGUF)   │          │
│  │ • Markdowns  │  │ meta.json    │  │ Embedder     │          │
│  │ • TXT files  │  │ embed_cache/ │  │ (HF cache)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Query (Normal)

```
Usuario pregunta "¿Cuál es el RUC?"
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND: ChatPanel                                          │
│    • Valida pregunta                                            │
│    • Agrega mensaje de usuario al historial                    │
│    • Envía POST /ask                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. BACKEND: app.py                                              │
│    • Revisa caché (query, source) → HIT? devuelve cached       │
│    • Si MISS, continúa...                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RAG: Recuperación                                            │
│    a) Embedding de query                                        │
│    b) FAISS search (top 80)                                     │
│    c) BM25 search (top 60)                                      │
│    d) Union + dedup                                             │
│    e) Filtro por source (si aplica)                             │
│    f) Diversificación (si multi-doc)                            │
│    g) Cross-encoder rerank → top-k=6                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. RAG: Temperatura                                             │
│    • Auto-detecta por heurísticas:                              │
│      - "cuál", "qué", números → 0.0 (factual)                   │
│      - "explica", "resume" → 0.3 (balanceado)                   │
│      - "sugiere" → 0.7 (creativo)                               │
│    • O usa temperatura manual si se especificó                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. RAG: Prompt Building                                         │
│    • Format: [INST] <<SYS>>...contexto...<</SYS>> [/INST]       │
│    • Token clipping (65% N_CTX para prompt, 35% para respuesta)│
│    • Guardrails anti-alucinación                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. LLM: Generación                                              │
│    • llama.cpp (Mistral-7B-Instruct-Q4_K_M)                     │
│    • max_tokens = safe_calc(N_CTX - prompt_tokens)              │
│    • temperature = auto-detectada                               │
│    • stop = ["</s>"]                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. BACKEND: Respuesta                                           │
│    • Construye AskResponse:                                     │
│      - answer: texto generado                                   │
│      - citations: [chunk_id, score, text, page, source]         │
│      - cached: false                                            │
│      - search_mode_used: "single"                               │
│      - temperature_used: 0.0                                    │
│    • Cachea respuesta                                           │
│    • Devuelve JSON                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. FRONTEND: Muestra                                            │
│    • Agrega mensaje de asistente al historial                  │
│    • Renderiza con MarkdownRenderer                             │
│    • Muestra metadata (temp, modo, caché)                       │
│    • Lista citas con click-to-jump                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Flujo de Query (Streaming SSE)

```
Usuario pregunta (mismo input)
    │
    ▼
POST /ask/stream
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: Generación Streaming                                   │
│                                                                   │
│  event: metadata                                                │
│  data: {"cached": false, "search_mode": "single", "temp": 0.0} │
│                                                                   │
│  event: token                                                   │
│  data: {"token": "El", "done": false}                           │
│                                                                   │
│  event: token                                                   │
│  data: {"token": " RUC", "done": false}                         │
│                                                                   │
│  event: token                                                   │
│  data: {"token": " es", "done": false}                          │
│                                                                   │
│  ... más tokens ...                                             │
│                                                                   │
│  event: citations                                               │
│  data: [{...}, {...}]                                            │
│                                                                   │
│  event: done                                                    │
│  data: {"done": true}                                            │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
FRONTEND: EventSource listener
    • Recibe tokens → append a respuesta
    • UX tipo ChatGPT (typing effect)
    • Al final, muestra citas
```

---

## 🗂️ Estructura de Datos

### Message (Frontend)
```typescript
{
  id: "user-1697123456789",
  role: "user" | "assistant",
  content: "¿Cuál es el RUC?",
  citations: [...],
  timestamp: Date,
  cached: false,
  searchMode: "single",
  temperature: 0.0
}
```

### Citation
```typescript
{
  id: 42,                    // Índice en el vector store
  score: 0.85,               // Similaridad (0-1)
  text: "RUC: 1234567890",   // Fragmento (max 400 chars)
  page: 1,                   // Número de página (PDF)
  source: "factura.pdf"      // Nombre del archivo
}
```

### AskRequest
```python
{
  "question": "¿Cuál es el RUC?",
  "source": "factura.pdf",      # None para TODO el corpus
  "temperature": 0.0,           # None para auto-detect
  "search_mode": "auto"         # single/multi/auto
}
```

### AskResponse
```python
{
  "answer": "El RUC es...",
  "citations": [...],
  "cached": false,
  "search_mode_used": "single",
  "temperature_used": 0.0
}
```

---

## 🔐 Seguridad

### Validaciones (Pydantic)
```python
question: min_length=3, max_length=500
source: sanitización (no .., /, \)
temperature: ge=0.0, le=2.0
```

### Rate Limiting
```python
@limiter.limit("10/minute")  # Por IP
```

### CORS
```python
allow_origins = ["http://localhost:5173"]  # Específicos
```

---

## ⚙️ Configuración (.env)

```bash
# Modelos
EMBEDDING_MODEL_ID=intfloat/multilingual-e5-base
LLM_MODEL_PATH=data/models/llm/mistral-7b-instruct-q4_k_m.gguf

# RAG
TOP_K=6
N_CTX=4096
TEMPERATURE=0.0  # Default (ahora auto-detect)

# Caché
ENABLE_CACHE=true
CACHE_TTL_SECONDS=300
CACHE_MAX_SIZE=100

# Seguridad
RATE_LIMIT_PER_MINUTE=10
MAX_FILE_SIZE_MB=50
```

---

## 📊 Métricas Clave

### Performance
- **Latencia sin caché**: 2-10s (depende del corpus)
- **Latencia con caché**: <100ms
- **Tokens/segundo (streaming)**: ~20-30 (CPU)

### Calidad
- **Hit rate caché**: >50% (con uso frecuente)
- **Cross-encoder accuracy**: >85% top-3
- **Temperature auto-detect**: >90% accuracy

---

## 🎯 Decisiones de Diseño

### ¿Por qué E5-base?
- ✅ Multilingüe (español + inglés)
- ✅ Dim=768 (balance size/quality)
- ✅ SOTA en benchmarks multilingües

### ¿Por qué Mistral-7B-Instruct?
- ✅ Pequeño pero potente (7B params)
- ✅ Cuantizado Q4_K_M (4GB RAM)
- ✅ Instruct-tuned (sigue instrucciones)

### ¿Por qué FAISS IndexFlatIP?
- ✅ Exacto (no approximate)
- ✅ Rápido para corpus <100k chunks
- ✅ Cosine similarity nativa

### ¿Por qué BM25 + FAISS?
- ✅ Complementarios (semántico + keywords)
- ✅ Mejor recall que solo uno
- ✅ Robusto ante queries ambiguas

### ¿Por qué Cross-encoder?
- ✅ Mejor precisión que bi-encoder solo
- ✅ Jina-reranker-v2 multilingüe
- ✅ Costo aceptable para top-k pequeño

---

*Arquitectura v2.0 - Octubre 2025*
