# 🚀 Roadmap de Mejoras - Sistema RAG v2.0 → v3.0

> **Estado actual**: Sistema sólido (9/10) con funcionalidad completa  
> **Objetivo**: Llevar a nivel profesional/empresarial (10/10)

---

## 📊 Evaluación del Estado Actual

### ✅ Fortalezas
- ✅ RAG híbrido (FAISS + BM25 + reranking)
- ✅ Temperatura dinámica
- ✅ Caché inteligente
- ✅ UI conversacional moderna
- ✅ Búsqueda multi-documento
- ✅ Preview de documentos (PDF, TXT, MD)
- ✅ 100% local/offline

### ⚠️ Áreas de Oportunidad
- ⚠️ Sin persistencia de historial conversacional
- ⚠️ Sin manejo de errores robusto en frontend
- ⚠️ Sin métricas de calidad de respuestas
- ⚠️ Sin optimización de embeddings (cuantización)
- ⚠️ Sin soporte para documentos grandes (>50MB)
- ⚠️ Sin análisis de sentimiento en queries
- ⚠️ Sin exportación de conversaciones
- ⚠️ Sin modo oscuro

---

## 🎯 Mejoras Prioritarias (Orden de Impacto)

### **Prioridad CRÍTICA** 🔴

#### 1. Persistencia de Historial Conversacional
**Problema**: Si refrescas la página, pierdes toda la conversación.

**Solución Backend**:
```python
# backend/conversation.py (NUEVO)
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path

class ConversationManager:
    """Gestiona conversaciones persistentes en disco"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_conversation(self, conv_id: str, messages: List[Dict]) -> None:
        """Guarda conversación en JSON"""
        file_path = self.storage_dir / f"{conv_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "id": conv_id,
                "created_at": datetime.now().isoformat(),
                "messages": messages
            }, f, indent=2, ensure_ascii=False)
    
    def load_conversation(self, conv_id: str) -> Optional[Dict]:
        """Carga conversación desde JSON"""
        file_path = self.storage_dir / f"{conv_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_conversations(self) -> List[Dict]:
        """Lista todas las conversaciones"""
        conversations = []
        for file in self.storage_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                conversations.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "message_count": len(data["messages"])
                })
        return sorted(conversations, key=lambda x: x["created_at"], reverse=True)

# Nuevos endpoints en app.py
@app.post("/conversations/{conv_id}")
def save_conversation(conv_id: str, messages: List[Dict]):
    """Guarda una conversación"""
    conv_manager.save_conversation(conv_id, messages)
    return {"status": "saved", "conv_id": conv_id}

@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: str):
    """Recupera una conversación"""
    conv = conv_manager.load_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@app.get("/conversations")
def list_conversations():
    """Lista todas las conversaciones"""
    return conv_manager.list_conversations()
```

**Solución Frontend**:
```typescript
// frontend/src/lib/storage.ts
export function saveConversation(convId: string, messages: Message[]) {
  // 1. Guardar en localStorage (inmediato)
  localStorage.setItem(`conv_${convId}`, JSON.stringify(messages))
  
  // 2. Sincronizar con backend (opcional, para backup)
  fetch(`${getBaseUrl()}/conversations/${convId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(messages)
  }).catch(err => console.warn('Backend sync failed:', err))
}

export function loadConversation(convId: string): Message[] | null {
  const data = localStorage.getItem(`conv_${convId}`)
  return data ? JSON.parse(data) : null
}

// frontend/src/components/ChatPanel.tsx
useEffect(() => {
  // Auto-guardar cada 5 segundos
  const interval = setInterval(() => {
    if (messages.length > 0) {
      saveConversation(conversationId, messages)
    }
  }, 5000)
  return () => clearInterval(interval)
}, [messages, conversationId])
```

**Impacto**: ⭐⭐⭐⭐⭐ (crítico para UX)  
**Esfuerzo**: 🔨🔨 (medio - 4-6 horas)

---

#### 2. Manejo de Errores Robusto
**Problema**: Cuando el backend falla, el frontend muestra pantalla blanca o errores genéricos.

**Solución**:
```typescript
// frontend/src/components/ErrorBoundary.tsx (NUEVO)
import { Component, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md p-6 bg-white rounded-lg shadow-lg border border-red-200">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <h2 className="text-xl font-bold text-gray-900">Oops! Algo salió mal</h2>
            </div>
            <p className="text-gray-600 mb-4">
              {this.state.error?.message || 'Error desconocido'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="w-full px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700"
            >
              Recargar página
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

// Envolver App en main.tsx
import { ErrorBoundary } from './components/ErrorBoundary'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
)
```

**Backend - Errores Estructurados**:
```python
# backend/models.py
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# backend/app.py
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Los datos enviados no son válidos",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Error interno del servidor",
            "details": str(exc) if settings.debug else None,
            "timestamp": datetime.now().isoformat()
        }
    )
```

**Impacto**: ⭐⭐⭐⭐⭐ (evita frustración del usuario)  
**Esfuerzo**: 🔨🔨 (medio - 3-4 horas)

---

#### 3. Streaming Real (Token-by-Token)
**Problema**: Tienes el endpoint `/ask/stream` pero el frontend no lo usa.

**Solución**:
```typescript
// frontend/src/lib/api.ts
export async function askStreaming(
  question: string,
  source?: string,
  onToken?: (token: string) => void,
  onCitations?: (citations: Citation[]) => void,
  onMetadata?: (metadata: any) => void
): Promise<void> {
  const url = `${getBaseUrl()}/ask/stream`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, source })
  })

  if (!response.ok) throw new Error(`Stream failed: ${response.statusText}`)

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        
        if (line.startsWith('event: token')) {
          onToken?.(data.token)
        } else if (line.startsWith('event: citations')) {
          onCitations?.(data)
        } else if (line.startsWith('event: metadata')) {
          onMetadata?.(data)
        }
      }
    }
  }
}

// frontend/src/components/ChatPanel.tsx
const handleAskStreaming = async () => {
  setLoading(true)
  
  const assistantMessage: Message = {
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    content: '',  // Se irá llenando token por token
    citations: [],
    timestamp: new Date()
  }
  
  setMessages(prev => [...prev, assistantMessage])

  await askStreaming(
    question,
    selectedSource,
    // onToken
    (token) => {
      setMessages(prev => {
        const last = prev[prev.length - 1]
        return [...prev.slice(0, -1), { ...last, content: last.content + token }]
      })
    },
    // onCitations
    (citations) => {
      setMessages(prev => {
        const last = prev[prev.length - 1]
        return [...prev.slice(0, -1), { ...last, citations }]
      })
    }
  )

  setLoading(false)
}
```

**Impacto**: ⭐⭐⭐⭐ (UX tipo ChatGPT)  
**Esfuerzo**: 🔨🔨 (medio - 3-4 horas)

---

### **Prioridad ALTA** 🟠

#### 4. Métricas de Calidad (Feedback del Usuario)
**Problema**: No sabes si las respuestas son buenas o malas.

**Solución**:
```typescript
// frontend/src/components/MessageFeedback.tsx (NUEVO)
import { ThumbsUp, ThumbsDown } from 'lucide-react'

export function MessageFeedback({ messageId }: { messageId: string }) {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)

  const handleFeedback = async (type: 'up' | 'down') => {
    setFeedback(type)
    await fetch(`${getBaseUrl()}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message_id: messageId, feedback: type })
    })
    toast.success('¡Gracias por tu feedback!')
  }

  return (
    <div className="flex gap-2 mt-2">
      <button
        onClick={() => handleFeedback('up')}
        className={`p-1 rounded hover:bg-gray-100 ${feedback === 'up' ? 'text-green-600' : 'text-gray-400'}`}
      >
        <ThumbsUp className="h-4 w-4" />
      </button>
      <button
        onClick={() => handleFeedback('down')}
        className={`p-1 rounded hover:bg-gray-100 ${feedback === 'down' ? 'text-red-600' : 'text-gray-400'}`}
      >
        <ThumbsDown className="h-4 w-4" />
      </button>
    </div>
  )
}
```

**Backend**:
```python
# backend/feedback.py (NUEVO)
from pathlib import Path
import json
from datetime import datetime

class FeedbackManager:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(exist_ok=True)
    
    def save_feedback(self, message_id: str, feedback: str, metadata: dict = None):
        """Guarda feedback en JSONL"""
        with open(self.storage_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "message_id": message_id,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }) + '\n')
    
    def get_stats(self) -> dict:
        """Calcula estadísticas de feedback"""
        if not self.storage_path.exists():
            return {"total": 0, "positive": 0, "negative": 0}
        
        total = positive = negative = 0
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                total += 1
                if data["feedback"] == "up":
                    positive += 1
                else:
                    negative += 1
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": positive / total if total > 0 else 0
        }

# app.py
feedback_manager = FeedbackManager(Path("data/feedback/feedback.jsonl"))

@app.post("/feedback")
def submit_feedback(message_id: str, feedback: str):
    feedback_manager.save_feedback(message_id, feedback)
    return {"status": "ok"}

@app.get("/feedback/stats")
def feedback_stats():
    return feedback_manager.get_stats()
```

**Impacto**: ⭐⭐⭐⭐ (datos para mejorar el modelo)  
**Esfuerzo**: 🔨🔨 (medio - 3-4 horas)

---

#### 5. Modo Oscuro
**Problema**: Los usuarios que trabajan de noche sufren.

**Solución**:
```typescript
// frontend/src/lib/theme.ts (NUEVO)
export type Theme = 'light' | 'dark' | 'system'

export function getTheme(): Theme {
  return (localStorage.getItem('theme') as Theme) || 'system'
}

export function setTheme(theme: Theme) {
  localStorage.setItem('theme', theme)
  applyTheme(theme)
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement
  
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', prefersDark)
  } else {
    root.classList.toggle('dark', theme === 'dark')
  }
}

// Inicializar tema al cargar
applyTheme(getTheme())

// frontend/tailwind.config.ts
export default {
  darkMode: 'class',  // ← Activar modo oscuro
  theme: {
    extend: {
      colors: {
        // Colores oscuros personalizados
      }
    }
  }
}

// frontend/src/components/ThemeToggle.tsx (NUEVO)
import { Moon, Sun } from 'lucide-react'

export function ThemeToggle() {
  const [theme, setThemeState] = useState<Theme>(getTheme())

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setThemeState(newTheme)
    setTheme(newTheme)
  }

  return (
    <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
      {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
    </button>
  )
}
```

**Impacto**: ⭐⭐⭐ (confort visual)  
**Esfuerzo**: 🔨🔨🔨 (alto - 6-8 horas, hay que revisar todos los componentes)

---

#### 6. Exportación de Conversaciones
**Problema**: No puedes guardar/compartir conversaciones interesantes.

**Solución**:
```typescript
// frontend/src/lib/export.ts (NUEVO)
export function exportToMarkdown(messages: Message[]): string {
  let md = `# Conversación RAG - ${new Date().toLocaleDateString()}\n\n`
  
  messages.forEach(msg => {
    md += `## ${msg.role === 'user' ? '👤 Usuario' : '🤖 Asistente'}\n\n`
    md += `${msg.content}\n\n`
    
    if (msg.citations && msg.citations.length > 0) {
      md += `### 📚 Fuentes\n\n`
      msg.citations.forEach(cit => {
        md += `- **${cit.source}** (pág. ${cit.page}) - Score: ${(cit.score * 100).toFixed(1)}%\n`
        md += `  > ${cit.text.slice(0, 150)}...\n\n`
      })
    }
    
    md += `---\n\n`
  })
  
  return md
}

export function downloadMarkdown(messages: Message[], filename: string) {
  const md = exportToMarkdown(messages)
  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// Agregar botón en ChatPanel
<button
  onClick={() => downloadMarkdown(messages, `conversacion-${Date.now()}.md`)}
  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
>
  <Download className="h-4 w-4" />
  Exportar MD
</button>
```

**Impacto**: ⭐⭐⭐ (útil para documentación)  
**Esfuerzo**: 🔨 (bajo - 2-3 horas)

---

### **Prioridad MEDIA** 🟡

#### 7. Chunking Inteligente con Overlapping Semántico
**Problema**: El chunking actual es estático (por tamaño).

**Solución**:
```python
# backend/smart_chunking.py (NUEVO)
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticChunker:
    """Chunking basado en similaridad semántica"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def chunk_by_similarity(
        self, 
        sentences: List[str], 
        threshold: float = 0.7,
        max_chunk_size: int = 500
    ) -> List[str]:
        """
        Agrupa oraciones semánticamente similares.
        
        Args:
            sentences: Lista de oraciones
            threshold: Umbral de similaridad (0-1)
            max_chunk_size: Tamaño máximo de chunk en caracteres
        
        Returns:
            Lista de chunks
        """
        if not sentences:
            return []
        
        # Embeddings de oraciones
        embeddings = self.model.encode(sentences)
        
        chunks = []
        current_chunk = [sentences[0]]
        current_size = len(sentences[0])
        
        for i in range(1, len(sentences)):
            # Similaridad con la última oración del chunk actual
            sim = np.dot(embeddings[i], embeddings[i-1])
            
            # Si es similar y no excede tamaño, agregar al chunk actual
            if sim >= threshold and current_size + len(sentences[i]) <= max_chunk_size:
                current_chunk.append(sentences[i])
                current_size += len(sentences[i])
            else:
                # Guardar chunk actual y empezar uno nuevo
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]
                current_size = len(sentences[i])
        
        # Agregar último chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
```

**Impacto**: ⭐⭐⭐ (mejor calidad de retrieval)  
**Esfuerzo**: 🔨🔨🔨 (alto - 6-8 horas)

---

#### 8. Optimización de Embeddings (Cuantización)
**Problema**: Los embeddings de 768 dimensiones ocupan mucha RAM.

**Solución**:
```python
# backend/optimized_embeddings.py (NUEVO)
import faiss
import numpy as np

class OptimizedEmbeddingStore:
    """Store de embeddings cuantizados para ahorrar memoria"""
    
    def __init__(self, dimension: int = 768):
        # Product Quantization: reduce 768 dims a 96 bytes (8x compresión)
        quantizer = faiss.IndexFlatIP(dimension)
        self.index = faiss.IndexIVFPQ(
            quantizer,
            dimension,
            100,  # nlist: número de clusters
            96,   # m: número de sub-cuantizadores
            8     # nbits: bits por sub-cuantizador
        )
        self.is_trained = False
    
    def train(self, vectors: np.ndarray):
        """Entrena el índice con vectores de muestra"""
        if not self.is_trained:
            self.index.train(vectors)
            self.is_trained = True
    
    def add(self, vectors: np.ndarray):
        """Agrega vectores al índice"""
        if not self.is_trained:
            raise ValueError("Index not trained. Call train() first.")
        self.index.add(vectors)
    
    def search(self, query: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Busca los k vecinos más cercanos"""
        return self.index.search(query, k)

# Beneficios:
# - Reduce uso de RAM de ~3GB a ~400MB (para 100k chunks)
# - Búsqueda 2-3x más rápida
# - Pérdida de precisión < 2%
```

**Impacto**: ⭐⭐⭐ (escalabilidad)  
**Esfuerzo**: 🔨🔨🔨 (alto - 8-10 horas)

---

#### 9. Análisis de Intención de Query
**Problema**: No distingues entre queries de búsqueda vs. conversacionales.

**Solución**:
```python
# backend/query_classifier.py (NUEVO)
import regex as re
from typing import Literal

QueryType = Literal['search', 'conversation', 'command']

class QueryClassifier:
    """Clasifica el tipo de query del usuario"""
    
    SEARCH_PATTERNS = [
        r'^(busca|encuentra|muéstrame|dónde|cuál|qué es)',
        r'(RUC|fecha|número|dato|información)',
    ]
    
    CONVERSATION_PATTERNS = [
        r'^(explica|resume|analiza|compara|por qué)',
        r'(cómo funciona|qué significa|dame un ejemplo)',
    ]
    
    COMMAND_PATTERNS = [
        r'^(lista|enumera|muestra todos|dame la lista)',
        r'^(borra|limpia|exporta|guarda)',
    ]
    
    def classify(self, query: str) -> QueryType:
        """Clasifica el tipo de query"""
        query_lower = query.lower()
        
        # Verificar comandos primero (más específicos)
        for pattern in self.COMMAND_PATTERNS:
            if re.search(pattern, query_lower):
                return 'command'
        
        # Luego búsquedas factuales
        for pattern in self.SEARCH_PATTERNS:
            if re.search(pattern, query_lower):
                return 'search'
        
        # Por defecto, conversacional
        for pattern in self.CONVERSATION_PATTERNS:
            if re.search(pattern, query_lower):
                return 'conversation'
        
        return 'conversation'  # default

# Uso en rag.py
classifier = QueryClassifier()
query_type = classifier.classify(question)

if query_type == 'search':
    # Temperatura baja, top_k alto, priorizar BM25
    temperature = 0.0
    top_k = 10
elif query_type == 'conversation':
    # Temperatura media, top_k medio
    temperature = 0.3
    top_k = 6
else:
    # Comando: sin LLM, solo retrieval
    temperature = 0.0
    top_k = 20
```

**Impacto**: ⭐⭐⭐ (respuestas más precisas)  
**Esfuerzo**: 🔨🔨 (medio - 4-5 horas)

---

#### 10. Compresión de Documentos Grandes
**Problema**: PDFs grandes (>50MB) fallan al subir.

**Solución**:
```python
# backend/compression.py (NUEVO)
from PIL import Image
import PyPDF2
import io

class PDFCompressor:
    """Comprime PDFs grandes reduciendo calidad de imágenes"""
    
    def compress(self, input_path: str, output_path: str, quality: int = 50):
        """
        Comprime PDF reduciendo resolución de imágenes.
        
        Args:
            input_path: Ruta del PDF original
            output_path: Ruta del PDF comprimido
            quality: Calidad de imágenes (0-100)
        """
        reader = PyPDF2.PdfReader(input_path)
        writer = PyPDF2.PdfWriter()
        
        for page in reader.pages:
            # Comprimir imágenes en la página
            if '/XObject' in page['/Resources']:
                xobjects = page['/Resources']['/XObject'].get_object()
                for obj in xobjects:
                    if xobjects[obj]['/Subtype'] == '/Image':
                        self._compress_image(xobjects[obj], quality)
            
            writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
    
    def _compress_image(self, image_obj, quality: int):
        """Comprime una imagen dentro del PDF"""
        # Implementación de compresión de imagen
        pass

# app.py
@app.post("/ingest")
async def ingest_file(file: UploadFile):
    # Si es PDF y es muy grande, comprimir
    if file.filename.endswith('.pdf') and file.size > 50 * 1024 * 1024:
        compressor = PDFCompressor()
        compressed_path = temp_dir / f"compressed_{file.filename}"
        compressor.compress(temp_path, compressed_path, quality=60)
        file_path = compressed_path
```

**Impacto**: ⭐⭐ (casos de uso específicos)  
**Esfuerzo**: 🔨🔨 (medio - 4-5 horas)

---

### **Prioridad BAJA** 🟢

#### 11. Búsqueda Semántica en Nombres de Archivo
**Problema**: Solo buscas en contenido, no en nombres.

**Solución**:
```python
# backend/rag.py
def search_with_filename_boost(question: str, top_k: int = 6):
    """Búsqueda que también considera nombres de archivo"""
    
    # 1. Búsqueda normal en contenido
    content_results = search(question, top_k=top_k * 2)
    
    # 2. Buscar similitud con nombres de archivo
    sources = list(set(chunk.meta['source'] for chunk in all_chunks))
    source_embeddings = embedder.embed_batch([s.lower() for s in sources])
    query_embedding = embedder.embed(question)
    
    source_scores = {}
    for src, emb in zip(sources, source_embeddings):
        score = np.dot(query_embedding, emb)
        source_scores[src] = score
    
    # 3. Boost chunks de archivos con nombres relevantes
    for chunk in content_results:
        filename_boost = source_scores.get(chunk.meta['source'], 0) * 0.2
        chunk.score += filename_boost
    
    # 4. Re-rankear y retornar top_k
    content_results.sort(key=lambda x: x.score, reverse=True)
    return content_results[:top_k]
```

**Impacto**: ⭐⭐ (mejora marginal)  
**Esfuerzo**: 🔨 (bajo - 2-3 horas)

---

#### 12. Multi-idioma Automático
**Problema**: El sistema asume español, pero los documentos pueden ser inglés.

**Solución**:
```python
# backend/lang_detector.py (NUEVO)
from langdetect import detect

class LanguageAwareRAG:
    """RAG que adapta prompts según idioma detectado"""
    
    def detect_language(self, text: str) -> str:
        """Detecta idioma del texto"""
        try:
            return detect(text)
        except:
            return 'es'  # default español
    
    def build_prompt(self, question: str, context: str) -> str:
        """Construye prompt en el idioma apropiado"""
        lang = self.detect_language(question)
        
        if lang == 'en':
            system = "You are a helpful assistant. Answer based ONLY on the context provided."
        else:
            system = "Eres un asistente útil. Responde SOLO basándote en el contexto proporcionado."
        
        return f"[INST] <<SYS>>{system}<</SYS>>\n\nContext:\n{context}\n\nQuestion: {question} [/INST]"
```

**Impacto**: ⭐⭐ (útil para documentos técnicos en inglés)  
**Esfuerzo**: 🔨 (bajo - 2-3 horas)

---

## 📋 Plan de Implementación Recomendado

### **Sprint 1 (Semana 1)** - Fundamentos
- [x] ✅ Sistema base completo (ya terminado)
- [ ] 🔴 Persistencia de historial
- [ ] 🔴 Manejo de errores robusto
- [ ] 🔴 Streaming real token-by-token

### **Sprint 2 (Semana 2)** - UX/Métricas
- [ ] 🟠 Feedback de usuario
- [ ] 🟠 Modo oscuro
- [ ] 🟠 Exportación de conversaciones

### **Sprint 3 (Semana 3)** - Optimización
- [ ] 🟡 Chunking inteligente
- [ ] 🟡 Análisis de intención
- [ ] 🟡 Optimización de embeddings

### **Sprint 4 (Semana 4)** - Extras
- [ ] 🟢 Búsqueda en nombres de archivo
- [ ] 🟢 Multi-idioma
- [ ] 🟢 Compresión de PDFs grandes

---

## 🎯 Métricas de Éxito

### Cuantitativas
- **Latencia promedio**: < 3s (actualmente ~5-8s)
- **Hit rate caché**: > 60% (actualmente ~50%)
- **Satisfacción usuario**: > 80% (feedback positivo)
- **Uso de memoria**: < 4GB RAM (actualmente ~6GB)

### Cualitativas
- ✅ Conversaciones persisten entre sesiones
- ✅ Errores se manejan gracefully (no pantallas blancas)
- ✅ Respuestas streaming fluidas
- ✅ Dashboard de métricas completo

---

## 🚨 Consideraciones de Seguridad

### Actualmente falta:
1. **Autenticación**: Cualquiera puede usar el sistema
2. **Sanitización de archivos**: No validamos contenido de PDFs
3. **HTTPS**: Solo HTTP local
4. **Logs de auditoría**: No hay trazabilidad

### Soluciones mínimas:
```python
# backend/auth.py (BÁSICO)
from fastapi import Depends, HTTPException, Header

def verify_token(x_api_key: str = Header(None)):
    """Verificación básica de API key"""
    if not x_api_key or x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")

# Aplicar a endpoints sensibles
@app.post("/ingest", dependencies=[Depends(verify_token)])
async def ingest_file(file: UploadFile):
    ...
```

---

## 💡 Conclusión

**Tu sistema ya es sólido (9/10)**. Las mejoras sugeridas lo llevarían a nivel **empresarial (10/10)**:

### **Implementa YA** (ROI máximo):
1. ✅ Persistencia de historial (crítico para UX)
2. ✅ Manejo de errores (evita frustración)
3. ✅ Streaming real (UX moderna)

### **Implementa pronto** (alto valor):
4. ✅ Feedback de usuario (datos para mejorar)
5. ✅ Modo oscuro (confort)

### **Implementa después** (optimizaciones):
6. Chunking inteligente
7. Optimización de embeddings
8. Análisis de intención

---

*Documento generado el 11 de octubre de 2025*
