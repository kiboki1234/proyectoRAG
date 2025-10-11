# RAG Offline Soberano — v1.0

RAG local con FastAPI + FAISS + llama.cpp (LLM GGUF) + sentence-transformers (embeddings).

## ✨ Características

- 🔒 **100% Local y Privado**: Sin conexión a internet, tus datos nunca salen de tu máquina
- 🚀 **Recuperación Híbrida**: FAISS (vectorial) + BM25 (léxico) + Cross-Encoder reranking
- 🧠 **LLM Local**: Mistral 7B con llama.cpp (GGUF)
- 📄 **Multi-formato**: PDF, Markdown, TXT
- 🎯 **Búsqueda Avanzada**: Filtrado por documento, navegación a páginas específicas
- ⚡ **Optimizado**: Caché de queries, deduplicación de chunks, chunking semántico
- 🔧 **Production-Ready**: Health checks, rate limiting, logging estructurado, validaciones

## 🆕 Nuevas Características (v1.0)

- ✅ **Configuración con Variables de Entorno** (.env)
- ✅ **Validaciones Pydantic** con Field validators
- ✅ **Logging Estructurado** (JSON opcional)
- ✅ **Rate Limiting** (slowapi)
- ✅ **Caché de Respuestas** (TTL configurable)
- ✅ **Health Checks** (`/health`, `/stats`)
- ✅ **CORS Configurable** (no más `allow_origins=["*"]`)
- ✅ **Validación de Archivos** (tamaño, tipo)
- ✅ **Tests Unitarios** (pytest + coverage)
- ✅ **Docker Compose** para desarrollo

## 📋 Requisitos

- Python 3.10+
- CPU x86_64 con AVX2 (recomendado)
- RAM 16 GB (mínimo 8 GB)
- **Sin GPU**: OK (modelo 7B cuantizado Q4_K_M)

## 🚀 Instalación Rápida

### 1. Clonar repositorio
```bash
git clone <url-repo>
cd proyectoRAG
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv

# Activar (Windows PowerShell)
.venv\Scripts\activate
# Activar (Linux/Mac)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Descargar modelo LLM (ejemplo)
# Descarga mistral-7b-instruct-q4_k_m.gguf desde HuggingFace
# y colócalo en: backend/data/models/llm/
```

### 3. Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install

# Copiar PDF.js assets
npm run pdfjs:copy
```

## 🏃‍♂️ Ejecución

### Desarrollo

**Backend** (con hot-reload):
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev
```

### Con Docker Compose

```bash
# Desde la raíz del proyecto
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## 📡 API Endpoints

### Principales

- `POST /ingest` - Subir y indexar documentos
- `POST /ingest/all` - Reindexar todos los documentos
- `POST /ask` - Hacer una pregunta al sistema RAG
- `GET /sources` - Listar documentos disponibles

### Health & Monitoring

- `GET /health` - Health check (status, LLM loaded, chunks count)
- `GET /stats` - Estadísticas del sistema (docs, chunks, embedder)
- `GET /cache/stats` - Estadísticas del caché
- `POST /cache/clear` - Limpiar caché

### Debug

- `GET /debug/paths` - Ver rutas configuradas
- `GET /debug/pdfjs` - Verificar PDF.js

## ⚙️ Configuración (.env)

```bash
# Modelos
EMBEDDING_MODEL_ID=intfloat/multilingual-e5-base
LLM_MODEL_PATH=data/models/llm/mistral-7b-instruct-q4_k_m.gguf

# RAG Parameters
CHUNK_SIZE=900
CHUNK_OVERLAP=150
TOP_K=4

# llama.cpp
N_CTX=1024
N_THREADS=4
TEMPERATURE=0.2
MAX_TOKENS=256

# Seguridad
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_FILE_SIZE_MB=50
RATE_LIMIT_PER_MINUTE=10

# Cache
ENABLE_CACHE=true
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## 🧪 Testing

```bash
cd backend

# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=backend --cov-report=html

# Ver reporte HTML
# Abre: htmlcov/index.html

# Tests específicos
pytest tests/test_models.py
pytest tests/test_cache.py
pytest tests/test_api.py
```

## 📊 Arquitectura

```
proyectoRAG/
├── backend/
│   ├── app.py              # FastAPI app principal
│   ├── config.py           # Configuración con pydantic-settings
│   ├── models.py           # Modelos Pydantic
│   ├── rag.py              # Lógica RAG (FAISS + BM25 + rerank)
│   ├── ingest.py           # Ingesta y chunking
│   ├── enhanced_retrieval.py  # Embeddings y cross-encoder
│   ├── logger.py           # Sistema de logging
│   ├── cache.py            # Sistema de caché
│   ├── .env.example        # Template de configuración
│   ├── requirements.txt    # Dependencias Python
│   ├── pyproject.toml      # Config de pytest
│   ├── tests/              # Tests unitarios
│   │   ├── test_models.py
│   │   ├── test_cache.py
│   │   └── test_api.py
│   └── data/
│       ├── docs/           # Documentos a indexar
│       ├── store/          # Índice FAISS + metadata
│       ├── models/         # Modelos descargados
│       └── logs/           # Archivos de log
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── lib/            # Utilidades (API, storage, PDF)
│   │   └── styles/         # CSS global
│   └── package.json
├── docker-compose.yml      # Compose para desarrollo
└── README.md
```

## 🔧 Troubleshooting

### Error: "LLM no encontrado"
- Verifica que `LLM_MODEL_PATH` en `.env` apunte al archivo GGUF correcto
- Descarga un modelo compatible desde HuggingFace

### Error: "Import pydantic_settings not found"
```bash
pip install pydantic-settings
```

### Error: Rate limit exceeded
- Ajusta `RATE_LIMIT_PER_MINUTE` en `.env`
- O desactiva temporalmente el rate limiting

### Puerto 8000 ya en uso
```bash
# Cambiar puerto
uvicorn app:app --port 8001
```

## 📈 Performance Tips

1. **Aumentar N_CTX**: Si tienes RAM suficiente, aumenta a 2048 o 4096
2. **Ajustar N_THREADS**: Iguala al número de cores de tu CPU
3. **Habilitar Caché**: `ENABLE_CACHE=true` reduce latencia en queries repetidas
4. **Chunk Size**: Ajusta `CHUNK_SIZE` según tus documentos (más pequeño = más preciso, más grande = más contexto)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit tus cambios (`git commit -am 'Agregar mejora'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un Pull Request

## 📝 Licencia

MIT License - ver archivo LICENSE para detalles

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [sentence-transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- Comunidad de Software Libre ❤️

---

**Hecho con ❤️ y Software Libre · Funciona 100% local**
