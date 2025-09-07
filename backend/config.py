from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
STORE_DIR = DATA_DIR / "store"
MODELS_DIR = DATA_DIR / "models"
LLM_DIR = MODELS_DIR / "llm"
EMBED_CACHE_DIR = MODELS_DIR / "embed"

# Crear directorios si no existen
STORE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)
LLM_DIR.mkdir(parents=True, exist_ok=True)
EMBED_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Modelos
EMBEDDING_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL_PATH = str(LLM_DIR / "mistral-7b-instruct-q4_k_m.gguf")  # cambia si usas otro nombre

# Parámetros RAG (aprox. por caracteres)
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 4

# Llama.cpp
N_CTX = 1024
N_THREADS = 4  # ajusta según tu CPU
TEMPERATURE = 0.2
MAX_TOKENS = 256
