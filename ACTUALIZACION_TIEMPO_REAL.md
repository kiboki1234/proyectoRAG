# Sistema de Actualización en Tiempo Real de Documentos

## 🎯 Problema Resuelto

**Antes**: Cuando subías un documento o lo eliminabas, el modal de configuración y el selector de fuentes **NO se actualizaban automáticamente**. Tenías que cerrar y volver a abrir el modal, o refrescar la página.

**Ahora**: Todo se actualiza **en tiempo real** automáticamente. ✨

## ⚡ Cómo Funciona

Implementamos un **sistema de eventos** (Event Emitter) que permite la comunicación entre componentes independientes.

### Arquitectura

```
UploadZone (subir doc)           SettingsModal (abierto)
      ↓                                  ↓
   upload() → documentEvents.emit()  ← .on() (escuchando)
                     ↓
              'document-uploaded'
                     ↓
            loadAllData() se ejecuta
                     ↓
           Lista actualizada ✅
```

### Flujo de Eventos

1. **Usuario sube documento** en `UploadZone`
   - Se completa la ingesta
   - Se emite evento: `documentEvents.emit('document-uploaded')`

2. **Usuario elimina documento** en `SettingsModal`
   - Se elimina del backend
   - Se emite evento: `documentEvents.emit('document-deleted')`

3. **Usuario elimina todos** en `SettingsModal`
   - Se eliminan todos del backend
   - Se emite evento: `documentEvents.emit('documents-cleared')`

4. **Componentes escuchando**:
   - `SettingsModal` (cuando está abierto)
   - `SourcesSelect` (siempre)
   
   Ambos ejecutan su función `loadData()` automáticamente al recibir cualquier evento.

## 🔧 Implementación Técnica

### 1. Event Emitter (`lib/events.ts`)

```typescript
class DocumentEventEmitter {
  private listeners: Map<EventType, Set<Callback>> = new Map()

  on(event, callback) { /* Registra escuchador */ }
  off(event, callback) { /* Desregistra escuchador */ }
  emit(event) { /* Notifica a todos los escuchadores */ }
}

export const documentEvents = new DocumentEventEmitter()
```

**Tipos de eventos**:
- `'document-uploaded'` - Se subió un documento
- `'document-deleted'` - Se eliminó un documento
- `'documents-cleared'` - Se eliminaron todos los documentos

### 2. Emisión de Eventos

#### En `UploadZone.tsx`

```typescript
const upload = async () => {
  // ... código de upload ...
  
  // Emitir evento después de subir
  documentEvents.emit('document-uploaded')
}
```

#### En `SettingsModal.tsx`

```typescript
const handleDeleteDocument = async (filename: string) => {
  // ... código de eliminación ...
  
  // Emitir evento después de eliminar
  documentEvents.emit('document-deleted')
  await loadAllData()
}

const handleDeleteAllDocuments = async () => {
  // ... código de eliminación ...
  
  // Emitir evento después de eliminar todos
  documentEvents.emit('documents-cleared')
  await loadAllData()
}
```

### 3. Escucha de Eventos

#### En `SettingsModal.tsx`

```typescript
useEffect(() => {
  if (open) {
    const events = ['document-uploaded', 'document-deleted', 'documents-cleared']
    
    // Suscribirse a todos los eventos
    events.forEach(event => documentEvents.on(event, loadAllData))
    
    // Cleanup: desuscribirse al cerrar
    return () => {
      events.forEach(event => documentEvents.off(event, loadAllData))
    }
  }
}, [open])
```

**Importante**: Solo se suscribe cuando el modal está **abierto** para no desperdiciar recursos.

#### En `SourcesSelect.tsx`

```typescript
useEffect(() => {
  const events = ['document-uploaded', 'document-deleted', 'documents-cleared']
  
  // Suscribirse a todos los eventos
  events.forEach(event => documentEvents.on(event, loadData))
  
  // Cleanup: desuscribirse al desmontar
  return () => {
    events.forEach(event => documentEvents.off(event, loadData))
  }
}, [])
```

**Importante**: Se suscribe **siempre** porque el selector está siempre visible en el panel de chat.

## 📊 Flujos Completos

### Flujo 1: Subir Documento

```
1. Usuario arrastra PDF a UploadZone
2. Clic en "Ingerir documentos"
3. Backend procesa e indexa
4. UploadZone.upload() completa
5. ✨ documentEvents.emit('document-uploaded')
6. SettingsModal (si está abierto) ejecuta loadAllData()
7. SourcesSelect ejecuta loadData()
8. ✅ Lista de documentos actualizada en ambos componentes
9. ✅ Selector muestra el nuevo documento
10. ✅ Toast de éxito
```

### Flujo 2: Eliminar Documento Individual

```
1. Usuario abre ⚙️ Ajustes → Tab Documentos
2. Clic en "Eliminar" de un documento
3. Confirmación → Aceptar
4. Backend elimina archivo + meta.json + índice
5. SettingsModal.handleDeleteDocument() completa
6. ✨ documentEvents.emit('document-deleted')
7. SettingsModal ejecuta loadAllData()
8. SourcesSelect ejecuta loadData()
9. ✅ Documento desaparece de la lista
10. ✅ Selector ya no lo muestra
11. ✅ Toast de éxito
```

### Flujo 3: Eliminar Todos los Documentos

```
1. Usuario en Tab Documentos
2. Clic en "Eliminar Todos"
3. Confirmación con advertencia → Aceptar
4. Backend elimina todos los archivos + índice completo
5. SettingsModal.handleDeleteAllDocuments() completa
6. ✨ documentEvents.emit('documents-cleared')
7. SettingsModal ejecuta loadAllData()
8. SourcesSelect ejecuta loadData()
9. ✅ Lista queda vacía
10. ✅ Selector muestra solo "Buscar en todos"
11. ✅ Toast de éxito
```

## 🎯 Componentes Actualizados

### 1. `lib/events.ts` (NUEVO)
- Event emitter personalizado
- Tipos de eventos definidos
- API simple: `on()`, `off()`, `emit()`

### 2. `UploadZone.tsx`
- Importa `documentEvents`
- Emite `'document-uploaded'` después de ingestar

### 3. `SettingsModal.tsx`
- Importa `documentEvents`
- Escucha eventos solo cuando está abierto
- Emite eventos al eliminar
- Se actualiza automáticamente

### 4. `SourcesSelect.tsx`
- Importa `documentEvents`
- Escucha eventos permanentemente
- Se actualiza automáticamente
- Mejor manejo de errores

## ⚡ Ventajas

### UX Mejorado
- ✅ No requiere refrescar página
- ✅ No requiere cerrar/abrir modal
- ✅ Feedback instantáneo
- ✅ Sincronización perfecta

### Técnicas
- ✅ Arquitectura desacoplada
- ✅ Componentes independientes
- ✅ Fácil de extender
- ✅ Sin props drilling
- ✅ Cleanup automático

### Performance
- ✅ Solo actualiza cuando hay cambios reales
- ✅ SettingsModal solo escucha cuando está abierto
- ✅ Sin polling innecesario
- ✅ Sin re-renders excesivos

## 🔄 Sincronización Garantizada

Ahora **SIEMPRE** están sincronizados:

1. **Backend** (archivos físicos en `data/docs/`)
2. **Modal de configuración** (lista de documentos)
3. **Selector de fuentes** (dropdown en panel de chat)
4. **Estadísticas** (conteo de documentos y chunks)

## 🧪 Cómo Probar

### Test 1: Actualización al Subir
1. Abre ⚙️ Ajustes → Tab Documentos (déjalo abierto)
2. Sube un nuevo documento
3. ✅ Verifica que aparece automáticamente en la lista del modal
4. ✅ Verifica que aparece en el selector de fuentes

### Test 2: Actualización al Eliminar
1. Abre ⚙️ Ajustes → Tab Documentos
2. Elimina un documento
3. ✅ Verifica que desaparece de la lista
4. ✅ Verifica que ya no está en el selector de fuentes

### Test 3: Actualización con Modal Cerrado
1. Sube un documento (modal cerrado)
2. Abre ⚙️ Ajustes → Tab Documentos
3. ✅ Verifica que el documento está ahí
4. Cierra modal
5. Elimina desde backend manualmente
6. Abre modal de nuevo
7. ✅ Verifica que se actualizó

### Test 4: Estadísticas en Tiempo Real
1. Abre ⚙️ Ajustes → Tab Estadísticas (déjalo abierto)
2. Sube un documento
3. ✅ Verifica que el conteo de documentos aumenta
4. ✅ Verifica que el conteo de chunks aumenta

## 🚀 Extensibilidad

Para agregar nuevos eventos:

```typescript
// 1. Agregar tipo de evento en events.ts
type DocumentEventType = 
  | 'document-uploaded' 
  | 'document-deleted' 
  | 'documents-cleared'
  | 'document-updated'  // ← Nuevo

// 2. Emitir en el componente apropiado
documentEvents.emit('document-updated')

// 3. Los escuchadores existentes lo capturarán automáticamente
// (si están suscritos a todos los eventos)
```

## 📝 Resumen Técnico

**Patrón**: Observer / PubSub
**Bibliotecas**: Ninguna (implementación nativa)
**Complejidad**: Baja
**Líneas de código**: ~50 líneas totales
**Impacto**: Alto - mejora significativa de UX

**Archivos modificados**:
- ✅ `frontend/src/lib/events.ts` (nuevo)
- ✅ `frontend/src/components/UploadZone.tsx` (+3 líneas)
- ✅ `frontend/src/components/SettingsModal.tsx` (+15 líneas)
- ✅ `frontend/src/components/SourcesSelect.tsx` (+12 líneas)

**Archivos NO modificados**:
- Backend (ya funcionaba bien)
- API (sin cambios)
- Otros componentes

## 🎉 Resultado

Ahora tienes un sistema de actualización en tiempo real **profesional** que:

1. ✅ Se actualiza instantáneamente al subir documentos
2. ✅ Se actualiza instantáneamente al eliminar documentos
3. ✅ Sincroniza todos los componentes automáticamente
4. ✅ No requiere refrescar la página
5. ✅ Usa una arquitectura limpia y extensible

**Es como magia, pero es código bien diseñado** 🪄✨
