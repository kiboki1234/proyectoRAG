# 🎨 Frontend - Sistema RAG

Frontend en React + TypeScript + Vite para el sistema de Retrieval-Augmented Generation (RAG).

## 🚀 Inicio Rápido

### 1. **Verificar Backend**
Asegúrate de que el backend esté corriendo:
```bash
cd ../backend
uvicorn app:app --reload --port 8000
```

### 2. **Instalar Dependencias**
```bash
npm install
```

### 3. **Verificar Compatibilidad** (Opcional)
```bash
npm run check:backend
```

### 4. **Iniciar Frontend**
```bash
npm run dev
```

Abre: http://localhost:5173

---

## 📋 Scripts Disponibles

```bash
npm run dev            # Inicia servidor de desarrollo
npm run build          # Compila para producción
npm run preview        # Preview de build de producción
npm run check:backend  # Verifica compatibilidad con backend
```

---

## 🆕 Mejoras Implementadas

### ✅ **Compatibilidad Total**
El frontend funciona perfectamente con el backend mejorado **sin necesidad de cambios**.

### 🔧 **Archivos Nuevos (Opcionales)**

#### 1. `src/lib/validation.ts`
Validaciones del lado del cliente:
- ✅ Validación de longitud de pregunta (3-500 caracteres)
- ✅ Sanitización de nombres de archivo
- ✅ Validación de tamaño de archivo (10MB)
- ✅ Validación de extensión (.pdf, .md, .txt)

**Ejemplo de uso:**
```typescript
import { validateQuestion } from '@/lib/validation'

const result = validateQuestion(userInput)
if (!result.valid) {
  alert(result.error)
  return
}
```

#### 2. `src/components/SystemStatus.tsx`
Panel de monitoreo del sistema:
- 🟢 Estado de salud en tiempo real
- 📊 Estadísticas del índice RAG
- 💾 Métricas de caché
- 🔄 Auto-refresh cada 30 segundos

**Ejemplo de integración:**
```typescript
import SystemStatus from '@/components/SystemStatus'

// En tu App.tsx
<SystemStatus />
```

#### 3. `src/components/AskPanel.enhanced.tsx`
Versión mejorada del panel de preguntas con:
- ✅ Validación en tiempo real
- ✅ Contador de caracteres
- ✅ Indicadores visuales
- ✅ Mejor manejo de errores

#### 4. `src/lib/api.ts` (Actualizado)
Funciones adicionales para nuevos endpoints:
```typescript
import { getHealth, getStats, getCacheStats, clearCache } from '@/lib/api'

// Estado de salud
const health = await getHealth()
console.log(health.status) // "ok", "degraded", "error"

// Estadísticas del sistema
const stats = await getStats()
console.log(stats.total_documents, stats.total_chunks)

// Estadísticas del caché
const cache = await getCacheStats()
console.log(cache.hit_rate) // 0.67 = 67% hit rate

// Limpiar caché
await clearCache()
```

---

## 📚 Documentación

### Archivos de Documentación:
- **`COMPATIBILIDAD_RESUMEN.md`** - Resumen de compatibilidad Frontend ↔ Backend
- **`INTEGRACION_BACKEND.md`** - Guía detallada de integración

### Estructura del Proyecto:
```
frontend/
├── src/
│   ├── components/
│   │   ├── AskPanel.tsx              # Panel de preguntas (original)
│   │   ├── AskPanel.enhanced.tsx     # Versión mejorada (opcional)
│   │   ├── SystemStatus.tsx          # Monitoreo del sistema (nuevo)
│   │   ├── UploadZone.tsx           # Zona de carga de archivos
│   │   └── ...
│   ├── lib/
│   │   ├── api.ts                    # Funciones API (actualizado)
│   │   ├── validation.ts             # Validaciones (nuevo)
│   │   └── ...
│   └── ...
├── scripts/
│   └── check-compatibility.mjs       # Script de verificación (nuevo)
├── COMPATIBILIDAD_RESUMEN.md         # Resumen de compatibilidad
├── INTEGRACION_BACKEND.md            # Guía de integración
└── package.json
```

---

## 🎯 Endpoints del Backend

### Endpoints Originales (Compatibles):
- **POST `/ingest`** - Subir documentos
- **POST `/ask`** - Hacer pregunta al RAG
- **GET `/sources`** - Listar fuentes disponibles

### Nuevos Endpoints Disponibles:
- **GET `/health`** - Estado de salud del sistema
- **GET `/stats`** - Estadísticas del índice RAG
- **GET `/cache/stats`** - Métricas del caché
- **POST `/cache/clear`** - Limpiar caché de queries

---

## 🔧 Configuración Opcional

### Variables de Entorno
Crea `.env` en la raíz del frontend:

```bash
# URL del backend
VITE_API_BASE_URL=http://localhost:8000

# Límites de validación
VITE_MAX_FILE_SIZE_MB=10
VITE_QUESTION_MIN_LENGTH=3
VITE_QUESTION_MAX_LENGTH=500
```

---

## 🚦 Opciones de Implementación

### Opción 1: Sin Cambios ⚡
```bash
# El frontend actual funciona sin modificaciones
npm run dev
```
**Pros:** Inmediato, sin trabajo adicional  
**Contras:** Sin validaciones mejoradas, sin monitoreo

### Opción 2: Con Validaciones 🔧
```typescript
// En AskPanel.tsx, agregar:
import { validateQuestion } from '@/lib/validation'

const handleSubmit = async () => {
  const result = validateQuestion(question)
  if (!result.valid) {
    toast.error(result.error)
    return
  }
  // ... resto del código
}
```
**Pros:** Mejor UX, previene errores  
**Contras:** Requiere modificar componentes

### Opción 3: Completa 🚀
```typescript
// Reemplazar AskPanel.tsx con enhanced version
mv AskPanel.tsx AskPanel.original.tsx
mv AskPanel.enhanced.tsx AskPanel.tsx

// Agregar SystemStatus en App.tsx
import SystemStatus from '@/components/SystemStatus'
```
**Pros:** Experiencia premium, listo para producción  
**Contras:** Más tiempo de integración

---

## 🐛 Troubleshooting

### Error: "Cannot connect to backend"
```bash
# Verifica que el backend esté corriendo
npm run check:backend

# Si falla, inicia el backend:
cd ../backend
uvicorn app:app --reload --port 8000
```

### Error: "Invalid question length"
- El backend ahora valida longitud mínima de 3 caracteres
- Usa `validateQuestion()` antes de enviar al backend

### Rate Limit (429)
- El backend tiene rate limiting (60 req/min)
- Implementa debounce en el input de preguntas

---

## 📞 Soporte

Para más información:
1. Lee `COMPATIBILIDAD_RESUMEN.md` - Resumen ejecutivo
2. Lee `INTEGRACION_BACKEND.md` - Guía detallada
3. Ejecuta `npm run check:backend` - Verifica compatibilidad

---

## 🎉 ¡Listo!

El frontend está completamente preparado para trabajar con el backend mejorado. Todas las mejoras son **opcionales** y **backward-compatible**.

**Inicio rápido:**
```bash
npm install
npm run check:backend  # Verificar backend
npm run dev           # Iniciar frontend
```

🚀 **Happy coding!**
