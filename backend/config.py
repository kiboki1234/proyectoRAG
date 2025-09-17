from pathlib import Path

# === Rutas base ===
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
STORE_DIR = DATA_DIR / "store"
MODELS_DIR = DATA_DIR / "models"
LLM_DIR = MODELS_DIR / "llm"
EMBED_CACHE_DIR = MODELS_DIR / "embed"

# Crear directorios si no existen
for d in (DATA_DIR, DOCS_DIR, STORE_DIR, MODELS_DIR, LLM_DIR, EMBED_CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)

# === Modelos ===
# Embedder multilingüe con formato 'query: ...' / 'passage: ...'
EMBEDDING_MODEL_ID = "intfloat/multilingual-e5-base"
# Cambia al GGUF que tengas disponible
LLM_MODEL_PATH = str(LLM_DIR / "mistral-7b-instruct-q4_k_m.gguf")

# === Parámetros RAG ===
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 4

# === llama.cpp ===
# Puedes subirlo si tu GGUF lo soporta (2048/4096/8192)
N_CTX = 1024
N_THREADS = 4
TEMPERATURE = 0.2
MAX_TOKENS = 256
