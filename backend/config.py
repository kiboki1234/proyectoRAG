from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Configuración de la aplicación con variables de entorno"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # === Rutas base ===
    base_dir: Path = Path(__file__).resolve().parent
    
    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"
    
    @property
    def docs_dir(self) -> Path:
        return self.data_dir / "docs"
    
    @property
    def store_dir(self) -> Path:
        return self.data_dir / "store"
    
    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"
    
    @property
    def llm_dir(self) -> Path:
        return self.models_dir / "llm"
    
    @property
    def embed_cache_dir(self) -> Path:
        return self.models_dir / "embed"
    
    @property
    def logs_dir(self) -> Path:
        return self.base_dir / "logs"
    
    # === Modelos ===
    embedding_model_id: str = "intfloat/multilingual-e5-base"
    llm_model_path: str = "data/models/llm/mistral-7b-instruct-q4_k_m.gguf"
    
    # === Parámetros RAG ===
    chunk_size: int = 900
    chunk_overlap: int = 150
    top_k: int = 4
    
    # === llama.cpp ===
    n_ctx: int = 1024
    n_threads: int = 4
    temperature: float = 0.2
    max_tokens: int = 256
    
    # === Seguridad ===
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_file_size_mb: int = 50
    rate_limit_per_minute: int = 10
    
    # === Cache ===
    enable_cache: bool = True
    cache_ttl_seconds: int = 300
    
    # === Logging ===
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convierte el string de CORS origins a lista"""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convierte MB a bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def llm_model_full_path(self) -> Path:
        """Ruta completa al modelo LLM"""
        path = Path(self.llm_model_path)
        if path.is_absolute():
            return path
        return self.base_dir / self.llm_model_path
    
    def ensure_directories(self):
        """Crea los directorios necesarios"""
        for d in (self.data_dir, self.docs_dir, self.store_dir, 
                  self.models_dir, self.llm_dir, self.embed_cache_dir, self.logs_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Singleton para settings (cached)"""
    settings = Settings()
    settings.ensure_directories()
    return settings


# === Mantener compatibilidad con código existente ===
settings = get_settings()

BASE_DIR = settings.base_dir
DATA_DIR = settings.data_dir
DOCS_DIR = settings.docs_dir
STORE_DIR = settings.store_dir
MODELS_DIR = settings.models_dir
LLM_DIR = settings.llm_dir
EMBED_CACHE_DIR = settings.embed_cache_dir

EMBEDDING_MODEL_ID = settings.embedding_model_id
LLM_MODEL_PATH = str(settings.llm_model_full_path)

CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
TOP_K = settings.top_k

N_CTX = settings.n_ctx
N_THREADS = settings.n_threads
TEMPERATURE = settings.temperature
MAX_TOKENS = settings.max_tokens
