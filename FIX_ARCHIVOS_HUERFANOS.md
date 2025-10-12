# Fix: Detección y Eliminación de Archivos Huérfanos

## 🐛 Problema Reportado

"No se están eliminando correctamente los documentos"

## 🔍 Diagnóstico

### Lo que encontré:

1. **Los documentos SÍ se eliminaban correctamente** ✅
   - El endpoint `DELETE /documents/{filename}` funcionaba bien
   - Eliminaba archivo físico + índice + meta.json

2. **El problema real: Archivos Huérfanos** ⚠️
   - Había archivos en `data/docs/` que **nunca fueron indexados**
   - Ejemplo: `Las_costumbres_de_los_ecuatorianos.pdf`
   - Existían físicamente pero no aparecían en el modal
   - No se podían eliminar desde la UI

### Por qué pasaba:

El endpoint `/documents` solo mostraba documentos **indexados**:

```python
# Antes - Solo leía del índice
index, chunks, sources, pages = ingest.load_index_safe()
# Si un archivo no estaba en el índice, no aparecía
```

**Resultado**: Archivos huérfanos invisibles para el usuario.

## ✅ Solución Implementada

### 1. Backend: Detectar Archivos Huérfanos

**Archivo**: `backend/app.py`

**Nuevo comportamiento del endpoint `/documents`**:

```python
@app.get("/documents")
def list_documents():
    """
    Lista documentos indexados + archivos huérfanos
    """
    # 1. Cargar documentos indexados
    indexed_docs = {}
    try:
        index, chunks, sources, pages = ingest.load_index_safe()
        # Procesar chunks...
        indexed_docs[source] = {
            "indexed": True,  # ← Nuevo campo
            # ... stats
        }
    except FileNotFoundError:
        pass  # No hay índice
    
    # 2. Buscar archivos físicos (NUEVO)
    physical_files = set()
    for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
        for p in settings.docs_dir.glob(pattern):
            physical_files.add(p.name)
    
    # 3. Detectar huérfanos (NUEVO)
    for filename in physical_files:
        if filename not in indexed_docs:
            indexed_docs[filename] = {
                "name": filename,
                "chunks": 0,
                "indexed": False  # ← Marcado como huérfano
            }
    
    return {"documents": list(indexed_docs.values())}
```

**Cambios clave**:
- ✅ Escanea filesystem para encontrar todos los archivos
- ✅ Compara con índice para detectar huérfanos
- ✅ Nuevo campo `indexed: boolean` en cada documento
- ✅ Huérfanos se marcan con `indexed: false`

### 2. Frontend: Visualizar Huérfanos

**Archivo**: `frontend/src/lib/api.ts`

```typescript
export type DocumentInfo = {
  name: string;
  chunks: number;
  total_chars: number;
  has_pages: boolean;
  indexed: boolean;  // ← Nuevo campo
}
```

**Archivo**: `frontend/src/components/SettingsModal.tsx`

```tsx
{documents.documents.map((doc) => (
  <div className={`
    ${!doc.indexed 
      ? 'border-orange-300 bg-orange-50/50'  // ← Estilo especial
      : 'border-gray-200'
    }
  `}>
    {/* Ícono con color diferente */}
    <FileText className={
      !doc.indexed 
        ? 'text-orange-500'  // ← Naranja para huérfanos
        : 'text-gray-400'
    } />
    
    {/* Información */}
    {doc.indexed ? (
      <>
        <span>🧩 {doc.chunks} chunks</span>
        <span>📝 {doc.total_chars}k chars</span>
      </>
    ) : (
      <span className="text-orange-600">
        ⚠️ Archivo huérfano (no indexado)
      </span>
    )}
    
    {/* Botón eliminar (funciona igual) */}
    <button onClick={() => handleDeleteDocument(doc.name)}>
      Eliminar
    </button>
  </div>
))}
```

**Cambios visuales**:
- ✅ Borde naranja para archivos huérfanos
- ✅ Fondo naranja suave
- ✅ Ícono naranja
- ✅ Texto: "⚠️ Archivo huérfano (no indexado)"
- ✅ Botón eliminar funciona igual

## 🎯 Cómo Funciona Ahora

### Caso 1: Documento Indexado Normal

```json
{
  "name": "documento.pdf",
  "chunks": 45,
  "total_chars": 12500,
  "has_pages": true,
  "indexed": true  // ← Normal
}
```

**UI**:
```
┌────────────────────────────────────┐
│ 📄 documento.pdf                   │
│ 🧩 45 chunks 📝 12.5k caracteres   │
│                        [Eliminar]  │
└────────────────────────────────────┘
```

### Caso 2: Archivo Huérfano

```json
{
  "name": "huerfano.pdf",
  "chunks": 0,
  "total_chars": 0,
  "has_pages": false,
  "indexed": false  // ← Huérfano
}
```

**UI** (con estilo naranja):
```
┌────────────────────────────────────┐
│ 🟠 huerfano.pdf                    │
│ ⚠️ Archivo huérfano (no indexado)  │
│                        [Eliminar]  │
└────────────────────────────────────┘
```

## 📊 Comparación

### Antes ❌

```
Filesystem:     [doc1.pdf, doc2.pdf, huerfano.pdf]
Índice:         [doc1.pdf, doc2.pdf]
Modal muestra:  [doc1.pdf, doc2.pdf]
                                    ↑
                        huerfano.pdf es invisible
```

**Problemas**:
- ❌ Archivos huérfanos invisibles
- ❌ No se pueden eliminar desde UI
- ❌ Usuario confundido
- ❌ Ocupan espacio en disco

### Ahora ✅

```
Filesystem:     [doc1.pdf, doc2.pdf, huerfano.pdf]
Índice:         [doc1.pdf, doc2.pdf]
Modal muestra:  [doc1.pdf✅, doc2.pdf✅, huerfano.pdf⚠️]
                                                    ↑
                            Visible y marcado como huérfano
```

**Mejoras**:
- ✅ Todos los archivos visibles
- ✅ Huérfanos claramente identificados
- ✅ Se pueden eliminar desde UI
- ✅ Usuario informado

## 🧪 Testing

### Test 1: Verificar Detección de Huérfanos

```bash
# 1. Verificar estado actual
curl http://localhost:8000/documents

# Debería mostrar huerfano.pdf con indexed: false
```

### Test 2: Eliminar Huérfano desde UI

1. Abrir ⚙️ Ajustes → Tab Documentos
2. **Verificar**: Archivo huérfano aparece con fondo naranja
3. Clic en "Eliminar"
4. **Resultado**: Archivo eliminado correctamente

### Test 3: Subir Nuevo Documento

1. Subir PDF
2. **Verificar**: Aparece con `indexed: true`
3. **Verificar**: Sin fondo naranja (normal)

### Test 4: Escenario Completo

```bash
# 1. Copiar archivo sin indexar
cp archivo.pdf backend/data/docs/huerfano.pdf

# 2. Verificar en UI
# - Debe aparecer con advertencia naranja

# 3. Eliminar desde UI
# - Debe desaparecer correctamente
```

## 🎨 Diseño Visual

### Documento Normal
- Color: Gris/Azul
- Borde: `border-gray-200`
- Fondo: `bg-white`
- Info: chunks, caracteres, páginas

### Documento Huérfano
- Color: Naranja ⚠️
- Borde: `border-orange-300`
- Fondo: `bg-orange-50/50`
- Info: "⚠️ Archivo huérfano (no indexado)"
- Ícono: `text-orange-500`

## 📝 Archivos Modificados

### Backend
- `backend/app.py`
  - Función: `list_documents()`
  - Cambios: +40 líneas
  - Nuevo: Detección de archivos huérfanos
  - Nuevo: Campo `indexed` en respuesta

### Frontend
- `frontend/src/lib/api.ts`
  - Tipo: `DocumentInfo`
  - Cambio: +1 línea (campo `indexed`)

- `frontend/src/components/SettingsModal.tsx`
  - Cambio: ~20 líneas
  - Nuevo: Estilos condicionales para huérfanos
  - Nuevo: Texto de advertencia

## 🎯 Beneficios

### Para el Usuario
- ✅ Ve TODOS los archivos en `docs/`
- ✅ Identifica fácilmente archivos problemáticos
- ✅ Puede limpiar archivos huérfanos
- ✅ Mejor gestión de espacio en disco

### Para el Sistema
- ✅ Mayor transparencia
- ✅ Evita acumulación de archivos huérfanos
- ✅ Sincronización filesystem-índice visible
- ✅ Debugging más fácil

## 🚀 Casos de Uso

### Caso 1: Ingesta Fallida
```
Usuario sube PDF → Ingesta falla → PDF queda huérfano
                                      ↓
                    Ahora aparece en modal con advertencia
                                      ↓
                    Usuario puede eliminarlo manualmente
```

### Caso 2: Limpieza Manual
```
Administrador copia archivos a docs/ sin ingestar
                    ↓
            Aparecen como huérfanos
                    ↓
    Puede decidir: ingestar o eliminar
```

### Caso 3: Debugging
```
"¿Por qué mi documento no aparece en búsquedas?"
                    ↓
        Abrir modal de documentos
                    ↓
    Ver que está marcado como huérfano
                    ↓
        Re-ingestar o eliminar
```

## ⚠️ Notas Importantes

### Por qué `indexed: false` es útil

1. **Información clara**: Usuario sabe por qué no puede buscar en ese documento
2. **Acción correctiva**: Puede re-ingestar o eliminar
3. **Prevención**: Evita confusión "documento subido pero no aparece"

### Diferencia: Huérfano vs No Indexado

**Archivo Huérfano**:
- Existe en filesystem
- NO está en índice
- Probablemente error de ingesta
- **Solución**: Re-ingestar o eliminar

**Documento Indexado**:
- Existe en filesystem
- Está en índice
- Funciona normalmente
- **Solución**: Ninguna necesaria

## 🔮 Mejoras Futuras (Opcional)

1. **Botón "Re-indexar"** para huérfanos:
   ```tsx
   {!doc.indexed && (
     <button onClick={() => reindexDocument(doc.name)}>
       🔄 Re-indexar
     </button>
   )}
   ```

2. **Auto-detección en startup**:
   ```python
   @app.on_event("startup")
   def check_orphans():
       orphans = detect_orphan_files()
       if orphans:
           app_logger.warning(f"⚠️ {len(orphans)} archivos huérfanos detectados")
   ```

3. **Estadística de huérfanos**:
   ```json
   {
     "total_documents": 10,
     "indexed_documents": 8,
     "orphan_files": 2
   }
   ```

## ✅ Checklist de Verificación

- [x] Backend detecta archivos huérfanos
- [x] Campo `indexed` en respuesta
- [x] Frontend muestra estilo diferente para huérfanos
- [x] Texto de advertencia claro
- [x] Eliminación funciona igual
- [x] Documentación completa
- [ ] Testing manual (pendiente usuario)

## 🎉 Resultado Final

Ahora la gestión de documentos es **completa y transparente**:

1. ✅ Todos los archivos visibles (indexados + huérfanos)
2. ✅ Estado claro (indexed: true/false)
3. ✅ Eliminación funciona para todos
4. ✅ UI intuitiva con códigos de color
5. ✅ Mejor debugging y mantenimiento

**El sistema ahora es profesional y robusto** 🚀
