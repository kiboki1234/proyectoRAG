# Fix: Error al Cargar Estadísticas Después de Eliminar Documentos

## 🐛 Problema Encontrado

Cuando eliminabas un documento o todos los documentos, aparecía un toast de error:
```
❌ Error cargando estadísticas: ...
```

## 🔍 Causa Raíz

### Backend

El endpoint `/stats` lanzaba un **error 404** (`FileNotFoundError`) cuando no existía el índice FAISS:

```python
except FileNotFoundError:
    raise HTTPException(status_code=404, detail="Índice no encontrado...")
```

Esto sucedía porque:
1. Usuario elimina todos los documentos
2. Backend borra `faiss.index` y limpia `meta.json`
3. Frontend intenta cargar estadísticas
4. Backend no encuentra el índice → **Error 404**
5. Frontend muestra toast de error ❌

### Frontend

Tenía dos problemas adicionales:

1. **Llamadas duplicadas**: Después de eliminar, se llamaba a `loadAllData()` dos veces:
   - Una desde el handler (`handleDeleteDocument`)
   - Otra desde el evento (`documentEvents.emit`)

2. **Manejo de errores débil**: Si alguna API fallaba, todo el `Promise.all()` fallaba y mostraba el error.

## ✅ Solución Implementada

### 1. Backend: Devolver Datos Vacíos en Lugar de Error

**Archivo**: `backend/app.py`

**Antes**:
```python
except FileNotFoundError:
    raise HTTPException(status_code=404, detail="Índice no encontrado. Ingesta documentos primero.")
```

**Ahora**:
```python
except FileNotFoundError:
    # Si no existe el índice, devolver estadísticas vacías
    app_logger.info("Índice no encontrado, devolviendo estadísticas vacías")
    return StatsResponse(
        total_documents=0,
        total_chunks=0,
        avg_chunk_size=0.0,
        index_dimension=None,
        embedder_model=settings.embedding_model_id
    )
```

**Por qué**: Es más amigable devolver datos vacíos que un error. El usuario acaba de eliminar todo, es normal que no haya documentos.

### 2. Frontend: Manejo Robusto de Errores

**Archivo**: `frontend/src/components/SettingsModal.tsx`

#### A. Eliminación de Llamadas Duplicadas

**Antes**:
```typescript
const handleDeleteDocument = async (filename: string) => {
  // ...
  documentEvents.emit('document-deleted')
  await loadAllData()  // ← Duplicado!
}
```

**Ahora**:
```typescript
const handleDeleteDocument = async (filename: string) => {
  // ...
  documentEvents.emit('document-deleted')
  // No llamar loadAllData() aquí, el evento lo hará
}
```

**Por qué**: El evento ya desencadena `loadAllData()` en todos los componentes suscritos. Llamarlo manualmente causa dos requests innecesarios.

#### B. Fallbacks Individuales para Cada API

**Antes**:
```typescript
const [statsData, cacheData, docsData] = await Promise.all([
  getStats(),        // Si falla → todo falla
  getCacheStats(),   // Si falla → todo falla
  getDocuments(),    // Si falla → todo falla
])
```

**Ahora**:
```typescript
const [statsData, cacheData, docsData] = await Promise.all([
  getStats().catch(e => {
    console.error('Error loading stats:', e)
    return { total_documents: 0, total_chunks: 0, ... }
  }),
  getCacheStats().catch(e => {
    console.error('Error loading cache stats:', e)
    return { size: 0, max_size: 0, ... }
  }),
  getDocuments().catch(e => {
    console.error('Error loading documents:', e)
    return { total_documents: 0, total_chunks: 0, documents: [] }
  }),
])
```

**Por qué**: 
- Cada API tiene su propio fallback
- Si una falla, las otras continúan
- Se muestran datos vacíos en lugar de error
- Mejor experiencia de usuario

## 🎯 Comportamiento Actual

### Flujo: Eliminar Todos los Documentos

1. Usuario hace clic en "Eliminar Todos"
2. Confirmación → Aceptar
3. Backend elimina archivos + índice + meta.json
4. Se emite evento `'documents-cleared'`
5. SettingsModal escucha evento → ejecuta `loadAllData()`
6. SourcesSelect escucha evento → ejecuta `loadData()`
7. Backend devuelve:
   ```json
   {
     "total_documents": 0,
     "total_chunks": 0,
     "avg_chunk_size": 0,
     "index_dimension": null,
     "embedder_model": "all-MiniLM-L6-v2"
   }
   ```
8. Frontend muestra:
   - ✅ Lista vacía
   - ✅ Estadísticas en 0
   - ✅ Toast de éxito: "Todos los documentos eliminados"
   - ✅ **Sin errores** ✨

### Flujo: Eliminar Documento Individual

Similar al anterior, pero:
- Backend actualiza `meta.json` (remueve chunks del documento)
- Si quedan documentos, devuelve estadísticas actualizadas
- Si no quedan documentos, devuelve estadísticas en 0

## 📊 Comparación

### Antes ❌

```
Usuario elimina documento
↓
Backend borra índice
↓
Frontend intenta cargar stats
↓
Backend: 404 Error
↓
Toast: "❌ Error cargando estadísticas"
↓
Modal muestra datos obsoletos
```

### Ahora ✅

```
Usuario elimina documento
↓
Backend borra índice
↓
Frontend intenta cargar stats
↓
Backend: 200 OK (datos vacíos)
↓
Toast: "✅ Documento eliminado"
↓
Modal muestra lista vacía correctamente
```

## 🧪 Casos de Prueba

### Test 1: Eliminar Último Documento
1. Tener un solo documento
2. Abrir modal → Tab Documentos
3. Eliminar ese documento
4. **Resultado esperado**:
   - ✅ Toast de éxito
   - ✅ Lista vacía
   - ✅ Estadísticas en 0
   - ❌ SIN error

### Test 2: Eliminar Todos
1. Tener varios documentos
2. Abrir modal → Tab Documentos
3. "Eliminar Todos" → Confirmar
4. **Resultado esperado**:
   - ✅ Toast de éxito
   - ✅ Lista vacía
   - ✅ Estadísticas en 0
   - ❌ SIN error

### Test 3: Navegar entre Tabs Después de Eliminar Todo
1. Eliminar todos los documentos
2. Ir al tab "Estadísticas"
3. **Resultado esperado**:
   - ✅ Total documentos: 0
   - ✅ Total chunks: 0
   - ✅ Gráficos vacíos
   - ❌ SIN error

### Test 4: Caché de Stats con Index Vacío
1. Eliminar todos los documentos
2. Abrir modal → Tab Caché
3. **Resultado esperado**:
   - ✅ Stats de caché (hits: 0, misses: 0)
   - ❌ SIN error

## 🔧 Archivos Modificados

### Backend
- `backend/app.py`
  - Función: `get_stats()`
  - Cambio: Devolver datos vacíos en lugar de error 404
  - Líneas: ~10 modificadas

### Frontend
- `frontend/src/components/SettingsModal.tsx`
  - Función: `loadAllData()`
  - Cambio: Fallbacks individuales por API
  - Función: `handleDeleteDocument()` y `handleDeleteAllDocuments()`
  - Cambio: Eliminar llamada duplicada a `loadAllData()`
  - Líneas: ~30 modificadas

## 🎉 Beneficios

### Usuario
- ✅ No ve errores confusos
- ✅ Interfaz coherente con el estado real
- ✅ Feedback positivo al eliminar
- ✅ Puede usar la app normalmente después de eliminar todo

### Desarrollador
- ✅ Código más robusto
- ✅ Mejor manejo de errores
- ✅ Menos requests duplicados
- ✅ Logs más claros (console.error específicos)

## 📝 Notas Importantes

### Por Qué Datos Vacíos y No Error 404

**Razonamiento**:
1. Después de eliminar todo, **no hay documentos** = Estado válido
2. No es un error del usuario ni del sistema
3. El usuario espera ver una lista vacía, no un mensaje de error
4. Es consistente con otras apps (ej: bandeja de entrada vacía)

### Por Qué Fallbacks en Frontend

**Razonamiento**:
1. Resiliencia: Si una API falla, las otras siguen
2. UX: Mejor mostrar datos parciales que nada
3. Debugging: Logs específicos por API
4. Flexibilidad: Fácil agregar más endpoints

## 🚀 Próximos Pasos (Opcional)

Si quieres mejorar aún más:

1. **Loading States Granulares**:
   ```typescript
   const [statsLoading, setStatsLoading] = useState(false)
   const [docsLoading, setDocsLoading] = useState(false)
   ```

2. **Retry Logic**:
   ```typescript
   const fetchWithRetry = async (fn, retries = 3) => {
     for (let i = 0; i < retries; i++) {
       try {
         return await fn()
       } catch (e) {
         if (i === retries - 1) throw e
         await sleep(1000 * (i + 1))
       }
     }
   }
   ```

3. **Estado de "Vacío" Explícito**:
   ```typescript
   if (documents?.documents.length === 0) {
     return <EmptyState />
   }
   ```

## ✅ Resultado Final

Ahora cuando eliminas documentos:
- ✅ Todo funciona suave
- ✅ Sin errores molestos
- ✅ Interfaz coherente
- ✅ Experiencia profesional

**¡El bug está completamente resuelto!** 🎉
