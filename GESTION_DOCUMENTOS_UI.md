# Gestión de Documentos desde la UI

## 📝 Funcionalidad Implementada

Se ha agregado gestión completa de documentos desde el modal de configuración (⚙️ Ajustes).

## ✨ Características

### 1. **Eliminar Documento Individual**
- Botón "Eliminar" en cada documento de la lista
- Confirmación antes de eliminar
- Muestra toast de éxito/error
- Actualiza automáticamente la lista

### 2. **Eliminar Todos los Documentos**
- Botón "Eliminar Todos" en la parte superior
- Confirmación con advertencia detallada:
  - Número de documentos
  - Número de chunks
  - Advertencia de acción irreversible
- Limpia completamente el índice

### 3. **Actualización Automática**
- Después de cada eliminación se recarga:
  - Lista de documentos
  - Estadísticas
  - Caché stats
- No requiere refrescar la página

## 🎨 Interfaz de Usuario

### Tab "📚 Documentos"

```
┌─────────────────────────────────────────────────┐
│ Documentos Indexados          [Eliminar Todos] │
│ 5 documentos · 234 chunks                       │
├─────────────────────────────────────────────────┤
│ 📄 documento1.pdf                   [Eliminar] │
│    🧩 45 chunks 📝 12.3k caracteres             │
├─────────────────────────────────────────────────┤
│ 📄 documento2.txt                   [Eliminar] │
│    🧩 23 chunks 📝 8.1k caracteres              │
└─────────────────────────────────────────────────┘
```

## 🔧 Implementación Técnica

### Backend (app.py)

Dos nuevos endpoints:

1. **DELETE /documents/{filename}**
   - Elimina archivo de `data/docs/`
   - Limpia entrada de `meta.json`
   - Elimina índice FAISS completo (se regenera automáticamente)
   - Retorna: `{message: "...", deleted_file: "...", chunks_removed: N}`

2. **DELETE /documents**
   - Elimina todos los archivos de `data/docs/`
   - Limpia completamente `meta.json`
   - Elimina `faiss.index`
   - Retorna: `{message: "...", deleted_count: N, total_chunks: N}`

### Frontend

**Archivo**: `frontend/src/lib/api.ts`

```typescript
// Eliminar un documento
async function deleteDocument(filename: string): Promise<DeleteDocumentResponse>

// Eliminar todos los documentos
async function deleteAllDocuments(): Promise<DeleteAllDocumentsResponse>
```

**Archivo**: `frontend/src/components/SettingsModal.tsx`

```typescript
// Handler para eliminar un documento
const handleDeleteDocument = async (filename: string) => {
  // Confirmación
  // Llamada a API
  // Toast de resultado
  // Recarga de datos
}

// Handler para eliminar todos
const handleDeleteAllDocuments = async () => {
  // Validación de documentos existentes
  // Confirmación con detalles
  // Llamada a API
  // Toast de resultado
  // Recarga de datos
}
```

## 🎯 Flujo de Eliminación

### Individual

1. Usuario hace clic en botón "Eliminar" de un documento
2. Aparece confirmación: "¿Eliminar el documento [nombre]?"
3. Si confirma:
   - Se llama a `DELETE /documents/{filename}`
   - Backend elimina archivo + limpia meta.json + borra índice
   - Se muestra toast de éxito
   - Se recargan todos los datos (documentos, stats, caché)
4. La lista se actualiza automáticamente

### Todos

1. Usuario hace clic en "Eliminar Todos"
2. Aparece confirmación con advertencia:
   ```
   ⚠️ ADVERTENCIA: Vas a eliminar TODOS los documentos
   
   • 5 documentos
   • 234 chunks
   
   Esta acción NO se puede deshacer.
   
   ¿Estás seguro?
   ```
3. Si confirma:
   - Se llama a `DELETE /documents`
   - Backend elimina todo
   - Se muestra toast de éxito
   - Se recargan todos los datos
4. La lista queda vacía, mostrando mensaje "No hay documentos indexados aún"

## 📊 Respuestas de la API

### DELETE /documents/{filename}

```json
{
  "message": "Documento eliminado: documento.pdf",
  "deleted_file": "documento.pdf",
  "chunks_removed": 45
}
```

### DELETE /documents

```json
{
  "message": "Eliminados 5 documentos (234 chunks)",
  "deleted_count": 5,
  "total_chunks": 234
}
```

## ⚠️ Consideraciones Importantes

1. **No hay deshacer**: La eliminación es permanente
2. **Índice se regenera**: FAISS index se borra completamente y se recrea cuando se suben nuevos documentos
3. **Caché se mantiene**: El caché de queries no se afecta (se puede limpiar desde el tab "💾 Caché")
4. **Sincronización automática**: Después de eliminar, la lista se actualiza sola

## 🚀 Cómo Usar

1. Abrir modal de configuración (botón ⚙️ en el header)
2. Ir al tab "📚 Documentos"
3. Para eliminar uno:
   - Clic en "Eliminar" del documento
   - Confirmar
4. Para eliminar todos:
   - Clic en "Eliminar Todos" (arriba a la derecha)
   - Leer advertencia
   - Confirmar

## 🎨 Estilos

- Botones de eliminación en **rojo** (red-600)
- Hover con fondo rojo claro
- Icono de advertencia (⚠️) en "Eliminar Todos"
- Icono de basura (🗑️) en "Eliminar" individual
- Dark mode completamente soportado

## 🐛 Manejo de Errores

- Si falla la eliminación, se muestra toast de error
- Si no hay documentos, "Eliminar Todos" muestra info toast
- Errores se logean en el backend
- Frontend muestra mensaje de error específico

## ✅ Testing Manual

Pasos para probar:

1. Subir algunos documentos
2. Abrir configuración → Tab Documentos
3. Probar eliminar un documento individual
4. Verificar que desapareció de la lista
5. Verificar que no aparece en el selector de fuentes
6. Probar "Eliminar Todos"
7. Verificar lista vacía
8. Subir nuevos documentos
9. Verificar que todo funciona normalmente

## 📝 Archivos Modificados

### Backend
- `backend/app.py`: +118 líneas (2 nuevos endpoints)

### Frontend
- `frontend/src/lib/api.ts`: +62 líneas (2 funciones + tipos)
- `frontend/src/components/SettingsModal.tsx`: +50 líneas (2 handlers + UI mejorada)

## 🎉 Resultado Final

Ahora los usuarios pueden:
- ✅ Ver todos los documentos indexados con su metadata
- ✅ Eliminar documentos individuales con un clic
- ✅ Eliminar todos los documentos con un clic
- ✅ Recibir confirmaciones antes de eliminar
- ✅ Ver feedback instantáneo (toasts)
- ✅ Ver la lista actualizada automáticamente

Sin necesidad de:
- ❌ Acceder al filesystem manualmente
- ❌ Reiniciar el backend
- ❌ Limpiar caché del navegador
- ❌ Usar comandos de terminal
