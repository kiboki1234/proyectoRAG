# 🔄 Guía de Integración Frontend con Backend Mejorado

## 📋 Resumen de Cambios

### ✅ Compatible sin cambios
- Endpoint `/ingest` - Sigue funcionando exactamente igual
- Endpoint `/ask` - Mismos parámetros y respuesta
- Endpoint `/sources` - Sin cambios

### 🔄 Cambios Realizados en el Frontend

#### 1. **Actualización de tipos en `api.ts`**
- ✅ Agregado tipo `IngestResponse` completo con campos adicionales
- ✅ Mejorado manejo de errores para usar `ErrorResponse` del backend
- ✅ Agregadas funciones para nuevos endpoints: `/health`, `/stats`, `/cache/stats`, `/cache/clear`

#### 2. **Nuevo archivo `validation.ts`**
- ✅ Validación de longitud de pregunta (3-500 caracteres)
- ✅ Validación de nombre de fuente (previene path traversal)
- ✅ Validación de tamaño de archivo (límite 10MB por defecto)
- ✅ Validación de extensión de archivo (.pdf, .md, .txt)

#### 3. **Nuevo componente `SystemStatus.tsx`**
- ✅ Muestra estado de salud del backend
- ✅ Estadísticas del sistema RAG
- ✅ Métricas del caché de queries
- ✅ Auto-refresh cada 30 segundos

---

## 🚀 Cómo Usar las Validaciones

### En el componente `AskPanel.tsx`

```typescript
import { validateQuestion, validateSource } from '../lib/validation';

const handleSubmit = async () => {
  // Validar pregunta antes de enviar
  const questionValidation = validateQuestion(question);
  if (!questionValidation.valid) {
    alert(questionValidation.error);
    return;
  }

  // Validar fuente si se proporciona
  if (source) {
    const sourceValidation = validateSource(source);
    if (!sourceValidation.valid) {
      alert(sourceValidation.error);
      return;
    }
  }

  // Continuar con la llamada a la API
  const response = await ask(question, source);
  // ...
};
```

### En el componente `UploadZone.tsx`

```typescript
import { validateFileSize, validateFileExtension } from '../lib/validation';

const handleFileChange = (files: FileList) => {
  const validFiles: File[] = [];
  const errors: string[] = [];

  Array.from(files).forEach(file => {
    // Validar extensión
    const extValidation = validateFileExtension(file);
    if (!extValidation.valid) {
      errors.push(extValidation.error!);
      return;
    }

    // Validar tamaño (10MB límite)
    const sizeValidation = validateFileSize(file, 10);
    if (!sizeValidation.valid) {
      errors.push(sizeValidation.error!);
      return;
    }

    validFiles.push(file);
  });

  if (errors.length > 0) {
    alert(errors.join('\n'));
  }

  if (validFiles.length > 0) {
    // Proceder con la carga de archivos válidos
    ingestFiles(validFiles);
  }
};
```

---

## 📊 Cómo Integrar el Sistema de Monitoreo

### Opción 1: Agregar pestaña en la interfaz principal

En `App.tsx`:

```typescript
import SystemStatus from './components/SystemStatus';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'status'>('chat');

  return (
    <div>
      <nav>
        <button onClick={() => setActiveTab('chat')}>Chat</button>
        <button onClick={() => setActiveTab('status')}>Estado del Sistema</button>
      </nav>

      {activeTab === 'chat' && (
        <>
          <AskPanel />
          <UploadZone />
        </>
      )}

      {activeTab === 'status' && <SystemStatus />}
    </div>
  );
}
```

### Opción 2: Agregar indicador de salud en el header

En `Header.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { getHealth } from '../lib/api';

export function Header() {
  const [status, setStatus] = useState<'ok' | 'degraded' | 'error' | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await getHealth();
        setStatus(health.status as any);
      } catch {
        setStatus('error');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check cada 1 min
    return () => clearInterval(interval);
  }, []);

  const statusIcon = {
    ok: '🟢',
    degraded: '🟡',
    error: '🔴',
  }[status ?? 'error'];

  return (
    <header>
      <h1>RAG System</h1>
      <div title={`Estado: ${status}`}>{statusIcon}</div>
    </header>
  );
}
```

---

## 🔧 Variables de Entorno Opcionales

Si quieres hacer el frontend más configurable, crea `.env` en la raíz del frontend:

```bash
# URL del backend
VITE_API_BASE_URL=http://localhost:8000

# Límites de validación (deben coincidir con el backend)
VITE_MAX_FILE_SIZE_MB=10
VITE_QUESTION_MIN_LENGTH=3
VITE_QUESTION_MAX_LENGTH=500
```

Luego actualiza `validation.ts`:

```typescript
const MAX_FILE_SIZE_MB = Number(import.meta.env.VITE_MAX_FILE_SIZE_MB) || 10;
const QUESTION_MIN_LENGTH = Number(import.meta.env.VITE_QUESTION_MIN_LENGTH) || 3;
const QUESTION_MAX_LENGTH = Number(import.meta.env.VITE_QUESTION_MAX_LENGTH) || 500;
```

---

## 🎯 Nuevos Endpoints Disponibles

### 1. **GET `/health`** - Estado de salud
```typescript
const health = await getHealth();
console.log(health);
// {
//   status: "ok",
//   timestamp: "2025-10-11T...",
//   llm_loaded: true,
//   index_exists: true,
//   chunks_count: 1523,
//   version: "1.0.0"
// }
```

### 2. **GET `/stats`** - Estadísticas del sistema
```typescript
const stats = await getStats();
console.log(stats);
// {
//   total_documents: 12,
//   total_chunks: 1523,
//   avg_chunk_size: 456.7,
//   index_dimension: 384,
//   embedder_model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
// }
```

### 3. **GET `/cache/stats`** - Estadísticas del caché
```typescript
const cacheStats = await getCacheStats();
console.log(cacheStats);
// {
//   size: 15,
//   max_size: 100,
//   hit_rate: 0.67,
//   total_hits: 42,
//   total_misses: 21
// }
```

### 4. **POST `/cache/clear`** - Limpiar caché
```typescript
const result = await clearCache();
console.log(result);
// { ok: true, message: "Caché limpiado correctamente" }
```

---

## 📝 Mensajes de Error Mejorados

El backend ahora responde con una estructura consistente:

```json
{
  "detail": "La pregunta debe tener al menos 3 caracteres",
  "error_type": "validation_error",
  "timestamp": "2025-10-11T15:30:00.000Z"
}
```

El código actualizado en `api.ts` ya maneja esto correctamente.

---

## ✅ Checklist de Integración

- [x] Actualizar tipos en `api.ts` (IngestResponse)
- [x] Crear `validation.ts` con funciones de validación
- [x] Crear componente `SystemStatus.tsx`
- [x] Agregar funciones para nuevos endpoints
- [ ] Integrar validaciones en `AskPanel.tsx`
- [ ] Integrar validaciones en `UploadZone.tsx`
- [ ] Agregar `SystemStatus` a la UI principal (opcional)
- [ ] Agregar indicador de salud en header (opcional)
- [ ] Probar todos los endpoints
- [ ] Verificar manejo de errores

---

## 🐛 Problemas Comunes y Soluciones

### Problema: "La pregunta debe tener al menos 3 caracteres"
**Solución**: Usa `validateQuestion()` antes de llamar a `ask()`

### Problema: "Archivo excede el límite de 10MB"
**Solución**: Usa `validateFileSize()` antes de llamar a `ingestFiles()`

### Problema: Rate limit excedido (429)
**Solución**: El backend tiene rate limiting (60 req/min por defecto). Implementa throttling en el frontend o pide al usuario que espere.

### Problema: Caché devolviendo respuestas antiguas
**Solución**: Llama a `clearCache()` después de ingestar nuevos documentos

---

## 🚀 Próximos Pasos Recomendados

1. **Testing**: Agregar tests unitarios para las validaciones
2. **Rate Limiting Frontend**: Implementar debounce en el input de preguntas
3. **Feedback Visual**: Mostrar progreso al subir archivos
4. **Manejo de Errores**: Componente Toast/Snackbar para errores
5. **Persistencia**: Guardar configuración del usuario en localStorage

---

¿Necesitas ayuda implementando alguna de estas mejoras? 🚀
