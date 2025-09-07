# RAG Offline Soberano — MVP


RAG local con FastAPI + FAISS + llama.cpp (LLM GGUF) + sentence-transformers (embeddings).


## Requisitos
- Python 3.10+
- CPU x86_64 con AVX2 (recomendado)
- RAM 16 GB (mínimo 8 GB)
- **Sin GPU**: OK (modelo 7B cuantizado Q4_K_M)


## Instalación
```bash
cd backend
python -m venv .venv && source .venv/bin/activate # en Windows: .venv\\Scripts\\activate
pip install -r requirements.txt