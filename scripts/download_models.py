"""
Descarga modelos necesarios:
- Embeddings (HF): sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- NOTA: El LLM (.gguf) debes descargarlo manualmente o proveer URL confiable.
  Sugerido: Mistral-7B-Instruct quantizado Q4_K_M (licencia Apache-2.0)

Coloca el .gguf en backend/data/models/llm/ y nómbralo como en config.py
"""
from huggingface_hub import snapshot_download
from pathlib import Path

EMBED_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIR = Path(__file__).resolve().parent.parent / "backend" / "data" / "models" / "embed"

if __name__ == "__main__":
    EMBED_DIR.mkdir(parents=True, exist_ok=True)
    print("Descargando embeddings…")
    snapshot_download(repo_id=EMBED_ID, local_dir=str(EMBED_DIR), local_dir_use_symlinks=False)
    print("Listo. Ahora coloca el .gguf del LLM en backend/data/models/llm/")
