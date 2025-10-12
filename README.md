# RAG Offline Soberano — MVP

RAG local con FastAPI + FAISS + llama.cpp (LLM GGUF) + sentence-transformers (embeddings).

## 📋 Requisitos Previos

### Para Instalación Local desde GitHub
- Python 3.10+ (recomendado 3.11)
- Node.js 18+ y npm
- Git
- CPU x86_64 con AVX2 (recomendado)
- RAM 16 GB (mínimo 8 GB)
- **Sin GPU**: OK (modelo 7B cuantizado Q4_K_M)

### Para Instalación con Docker
- Docker 20.10+
- Docker Compose 2.0+
- RAM 16 GB (mínimo 8 GB)
- Espacio en disco: ~10 GB

---

## 🚀 Opción 1: Instalación Local desde GitHub

### 1. Clonar el repositorio

```bash
git clone https://github.com/kiboki1234/proyectoRAG.git
cd proyectoRAG
```

### 2. Configurar el Backend

```bash
cd backend

# Crear y activar entorno virtual
# En Linux/Mac:
python -m venv .venv
source .venv/bin/activate

# En Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Descargar modelos de IA

```bash
# Desde el directorio raíz del proyecto con el entorno virtual activado
python scripts/download_models.py
```

Este script descargará:
- **Modelo de embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (~470 MB)

**Importante**: El modelo LLM debe descargarse manualmente:
1. Descargar Mistral 7B Instruct Q4_K_M desde [Hugging Face](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
2. Colocar el archivo `.gguf` en `backend/data/models/llm/`
3. Asegurarse de que el nombre coincida con el configurado en `backend/config.py` (por defecto: `mistral-7b-instruct-q4_k_m.gguf`)

Los modelos se guardarán en `backend/data/models/`.

### 4. Iniciar el Backend

```bash
# Desde el directorio backend
uvicorn app:app --reload --port 8000
```

El backend estará disponible en: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 5. Configurar el Frontend

Abrir una **nueva terminal** y ejecutar:

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

### 6. ✅ Verificar Instalación

1. Abrir el navegador en `http://localhost:5173`
2. Subir un documento PDF de prueba
3. Realizar una consulta sobre el documento
4. Verificar que se obtiene una respuesta

---

## 🐳 Opción 2: Instalación con Docker

### 1. Clonar el repositorio

```bash
git clone https://github.com/kiboki1234/proyectoRAG.git
cd proyectoRAG
```

### 2. Descargar modelos de IA (requerido)

Los modelos no están incluidos en la imagen Docker por su tamaño. Debes descargarlos antes de construir:

```bash
# Crear entorno virtual temporal solo para descargar modelos
cd backend
python -m venv .venv

# Activar entorno
# Linux/Mac:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Instalar solo las dependencias mínimas
pip install huggingface-hub requests tqdm

# Volver al directorio raíz y descargar embeddings
cd ..
python scripts/download_models.py

# Desactivar entorno temporal
deactivate
```

**Importante**: También necesitas descargar el modelo LLM manualmente:
1. Descargar Mistral 7B Instruct Q4_K_M desde [Hugging Face](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
2. Colocar el archivo `.gguf` en `backend/data/models/llm/`
3. Asegurarse de que el nombre sea `mistral-7b-instruct-q4_k_m.gguf` o actualizar la variable `LLM_MODEL_PATH` en el `docker-compose.yml`

### 3. Construir y levantar los contenedores

```bash
# Desde el directorio raíz del proyecto
docker-compose up --build
```

O para ejecutar en segundo plano:

```bash
docker-compose up -d --build
```

### 4. Acceder a la aplicación

- **Frontend**: `http://localhost:5173` (si configuraste frontend en Docker)
- **Backend**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### 5. Comandos útiles de Docker

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs solo del backend
docker-compose logs -f backend

# Detener los contenedores
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra datos)
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart backend

# Ver estado de los contenedores
docker-compose ps
```

### 6. ✅ Verificar Instalación

1. Verificar que los contenedores estén corriendo:
   ```bash
   docker-compose ps
   ```

2. Verificar health del backend:
   ```bash
   curl http://localhost:8000/health
   ```

3. Abrir `http://localhost:5173` y probar subir un documento

---

## 📁 Estructura de Datos Persistentes

Los siguientes directorios contienen datos persistentes y deben preservarse:

```
backend/data/
├── docs/           # Documentos PDF subidos
├── models/         # Modelos de IA descargados (⚠️ no commitear)
├── store/          # Índices FAISS
├── conversations/  # Historial de conversaciones
└── feedback/       # Feedback de usuarios
```

**Importante**: Los modelos de IA no se incluyen en Git por su tamaño. Deben descargarse con `scripts/download_models.py`.

---

## �� Configuración Avanzada

### Variables de Entorno

Puedes personalizar el comportamiento editando `backend/config.py` o usando variables de entorno:

```bash
# Ejemplo de variables de entorno
EMBEDDING_MODEL_ID=intfloat/multilingual-e5-base
CHUNK_SIZE=900
CHUNK_OVERLAP=150
TOP_K=4
TEMPERATURE=0.2
MAX_TOKENS=256
ENABLE_CACHE=true
LOG_LEVEL=INFO
```

### Configuración de Docker

Edita `docker-compose.yml` para ajustar:
- Puertos expuestos
- Variables de entorno
- Límites de recursos
- Volúmenes montados

---

## 🐛 Solución de Problemas

### Error: Modelos no encontrados

**Síntoma**: Error al iniciar backend: "Model file not found"

**Solución**:
```bash
cd backend
python scripts/download_models.py
```

### Error: Puerto 8000 ya en uso

**Solución**:
```bash
# Cambiar puerto en docker-compose.yml o al iniciar uvicorn
uvicorn app:app --reload --port 8001
```

### Error de memoria al cargar modelo

**Solución**: 
- Cerrar otras aplicaciones
- Usar modelo más pequeño (Mistral 7B Q4_K_M ya es la versión ligera)
- Aumentar swap del sistema

### Frontend no conecta con Backend

**Solución**:
1. Verificar que backend esté corriendo: `curl http://localhost:8000/health`
2. Verificar CORS en `backend/config.py`
3. Verificar que frontend apunte a `http://localhost:8000`

---

## 📚 Documentación Adicional

- [Arquitectura del Sistema](ARQUITECTURA.md)
- [Guía de Testing](TESTING_GUIDE.md)
- [Guía de Pruebas](GUIA_PRUEBAS.md)
- [Roadmap de Mejoras](ROADMAP_MEJORAS.md)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork del repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

---

## 📄 Licencia

[Especificar licencia del proyecto]

---

## 👤 Autor

**kiboki1234**
- GitHub: [@kiboki1234](https://github.com/kiboki1234)

---

## ⭐ Agradecimientos

- FastAPI
- FAISS
- llama.cpp
- sentence-transformers
- Hugging Face
