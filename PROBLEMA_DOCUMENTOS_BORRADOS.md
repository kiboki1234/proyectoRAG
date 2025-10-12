# 🗑️ Problema: Documentos Borrados Siguen Apareciendo en el Frontend

## 🚨 Problema

**Síntoma**: Borras documentos de `backend/data/docs/` pero siguen apareciendo en la lista del frontend.

**Causa**: El endpoint `/sources` combina dos fuentes de información:

```python
@app.get("/sources")
def list_sources():
    names = set()
    
    # 1️⃣ Archivos físicos en docs/
    for pattern in ("*.pdf", "*.md", "*.txt"):
        for p in settings.docs_dir.glob(pattern):
            names.add(p.name)
    
    # 2️⃣ Archivos en el índice FAISS (meta.json)
    _, _, sources, _ = ingest.load_index()
    for s in sources:
        if s:
            names.add(s)  # ⚠️ Incluye docs borrados!
    
    return {"sources": sorted(names)}
```

### Por Qué Ocurre

1. **Ingesta inicial**: Procesas documentos → se crea `meta.json` con todos los chunks
2. **Borras archivos**: Eliminas PDFs de `docs/`
3. **meta.json NO se actualiza**: Sigue teniendo los chunks de documentos borrados
4. **Frontend lista documentos**: API devuelve archivos de `docs/` + archivos de `meta.json`
5. **Resultado**: ❌ Documentos borrados siguen apareciendo

---

## 📊 Ejemplo

### Estado Inicial

```
backend/data/docs/
├── biblia.txt
├── factura.pdf
└── reglamento.pdf

backend/data/store/meta.json
├── chunks de biblia.txt
├── chunks de factura.pdf
└── chunks de reglamento.pdf
```

### Después de Borrar `factura.pdf`

```
backend/data/docs/
├── biblia.txt          ✅ Existe
└── reglamento.pdf      ✅ Existe

backend/data/store/meta.json
├── chunks de biblia.txt     ✅
├── chunks de factura.pdf    ❌ OBSOLETO (archivo no existe)
└── chunks de reglamento.pdf ✅
```

### Lista del Frontend

```
📚 Documentos disponibles:
- biblia.txt           (✅ existe en docs + índice)
- factura.pdf          (❌ NO existe en docs, pero SÍ en índice)
- reglamento.pdf       (✅ existe en docs + índice)
```

---

## ✅ Soluciones

### Opción 1: Limpiar el Índice Manualmente (RÁPIDO)

```bash
# 1. Backup del índice actual
cd backend/data/store
copy meta.json meta.json.backup
copy faiss.index faiss.index.backup

# 2. Eliminar índice completo
del meta.json
del faiss.index

# 3. Re-ingestar solo documentos actuales
# El backend detectará que no hay índice y lo reconstruirá
# O usar el endpoint /rebuild
```

### Opción 2: Usar Endpoint de Reconstrucción (RECOMENDADO)

```bash
# Si existe el endpoint /rebuild
curl -X POST http://localhost:8000/rebuild

# O desde PowerShell
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/rebuild"
```

### Opción 3: Script de Limpieza Automática

Crear un script que elimine del índice los documentos que no existen físicamente:

```python
# backend/scripts/clean_index.py
import json
from pathlib import Path
from config import STORE_DIR, DOCS_DIR

def clean_index():
    """Elimina del índice chunks de documentos que ya no existen."""
    meta_path = STORE_DIR / "meta.json"
    
    if not meta_path.exists():
        print("❌ No existe meta.json")
        return
    
    meta = json.load(meta_path.open(encoding='utf-8'))
    
    # Obtener archivos que SÍ existen
    existing_files = set()
    for pattern in ("*.pdf", "*.md", "*.txt"):
        for p in DOCS_DIR.glob(pattern):
            existing_files.add(p.name)
    
    print(f"📂 Archivos en docs/: {len(existing_files)}")
    
    # Filtrar chunks de documentos existentes
    old_count = len(meta['chunks'])
    
    indices_to_keep = [
        i for i, source in enumerate(meta['sources'])
        if source in existing_files
    ]
    
    meta['chunks'] = [meta['chunks'][i] for i in indices_to_keep]
    meta['sources'] = [meta['sources'][i] for i in indices_to_keep]
    meta['pages'] = [meta['pages'][i] for i in indices_to_keep]
    
    new_count = len(meta['chunks'])
    
    # Guardar
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    print(f"✅ Limpieza completada:")
    print(f"   Chunks antes: {old_count}")
    print(f"   Chunks después: {new_count}")
    print(f"   Eliminados: {old_count - new_count}")
    
    # También necesitas reconstruir el índice FAISS
    print("\n⚠️  IMPORTANTE: Debes reconstruir el índice FAISS:")
    print("   python -c \"from ingest import rebuild_index; rebuild_index()\"")

if __name__ == "__main__":
    clean_index()
```

### Opción 4: Modificar el Endpoint `/sources` (PREVENTIVO)

Cambiar el endpoint para que SOLO liste archivos que existen físicamente:

```python
@app.get("/sources")
def list_sources():
    """Lista solo archivos que existen físicamente."""
    try:
        names = set()
        
        # Solo archivos del filesystem
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            for p in settings.docs_dir.glob(pattern):
                if p.is_file():
                    names.add(p.name)
        
        # ⚠️ NO incluir archivos solo del índice
        # (evita mostrar documentos borrados)
        
        return {"sources": sorted(names)}
    except Exception as e:
        app_logger.error(f"Error listando fuentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Pros**: Previene el problema  
**Contras**: Si el índice tiene documentos que no están en `docs/`, no se mostrarán (pero es correcto)

---

## 🔧 Implementación Recomendada

### Fix Inmediato (para el usuario)

**Paso 1**: Crear script de limpieza

```python
# clean_deleted_docs.py (en la raíz del proyecto)
import json
from pathlib import Path

# Rutas
meta_path = Path('backend/data/store/meta.json')
docs_dir = Path('backend/data/docs')

# Cargar meta
meta = json.load(meta_path.open(encoding='utf-8'))

# Archivos existentes
existing = set()
for pattern in ['*.pdf', '*.md', '*.txt']:
    for p in docs_dir.glob(pattern):
        existing.add(p.name)

print(f"Archivos en docs/: {len(existing)}")
print(f"Documentos en índice: {len(set(meta['sources']))}")

# Filtrar
old_count = len(meta['chunks'])
keep = [i for i, s in enumerate(meta['sources']) if s in existing]

meta['chunks'] = [meta['chunks'][i] for i in keep]
meta['sources'] = [meta['sources'][i] for i in keep]
meta['pages'] = [meta['pages'][i] for i in keep]

print(f"\nChunks eliminados: {old_count - len(meta['chunks'])}")

# Guardar
meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
print("✅ Índice limpiado")
```

**Paso 2**: Ejecutar

```powershell
python clean_deleted_docs.py
```

**Paso 3**: Reconstruir índice FAISS

```powershell
# Opción A: Endpoint rebuild (si existe)
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/rebuild"

# Opción B: Borrar y re-ingestar
cd backend/data/store
del faiss.index
# Backend lo reconstruirá automáticamente
```

### Fix Permanente (modificar código)

**Cambiar el endpoint `/sources`** para solo listar archivos físicos:

```python
# backend/app.py
@app.get("/sources")
def list_sources():
    """
    Lista archivos disponibles SOLO si existen físicamente.
    No incluye documentos borrados que aún están en el índice.
    """
    try:
        names = set()
        
        # Solo del filesystem
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            for p in settings.docs_dir.glob(pattern):
                if p.is_file():
                    names.add(p.name)
        
        return {"sources": sorted(names)}
    except Exception as e:
        app_logger.error(f"Error listando fuentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎯 Mejora: Endpoint para Eliminar Documentos

Crear un endpoint dedicado para eliminar documentos correctamente:

```python
# backend/app.py

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Elimina un documento:
    1. Del filesystem (docs/)
    2. Del índice FAISS (meta.json)
    3. Reconstruye el índice FAISS
    """
    try:
        doc_path = settings.docs_dir / filename
        
        # 1. Verificar que existe
        if not doc_path.exists():
            raise HTTPException(status_code=404, detail=f"Documento {filename} no encontrado")
        
        # 2. Eliminar archivo físico
        doc_path.unlink()
        app_logger.info(f"Eliminado archivo: {filename}")
        
        # 3. Limpiar índice
        meta_path = settings.store_dir / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            
            # Filtrar chunks del documento eliminado
            old_count = len(meta['chunks'])
            keep_indices = [
                i for i, s in enumerate(meta['sources'])
                if s != filename
            ]
            
            meta['chunks'] = [meta['chunks'][i] for i in keep_indices]
            meta['sources'] = [meta['sources'][i] for i in keep_indices]
            meta['pages'] = [meta['pages'][i] for i in keep_indices]
            
            # Guardar
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            removed = old_count - len(meta['chunks'])
            app_logger.info(f"Eliminados {removed} chunks del índice")
        
        # 4. Reconstruir índice FAISS
        await rebuild_faiss_index()
        
        return {
            "success": True,
            "message": f"Documento {filename} eliminado correctamente",
            "chunks_removed": removed
        }
        
    except Exception as e:
        app_logger.error(f"Error eliminando documento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend: Botón de Eliminar

```tsx
// En DocumentsList.tsx o similar
const handleDelete = async (filename: string) => {
  if (!confirm(`¿Eliminar documento "${filename}"?`)) return
  
  try {
    await fetch(`/api/documents/${filename}`, { method: 'DELETE' })
    
    // Refrescar lista
    await refreshDocuments()
    
    toast.success(`Documento ${filename} eliminado`)
  } catch (error) {
    toast.error('Error al eliminar documento')
  }
}

// Botón
<button 
  onClick={() => handleDelete(doc.name)}
  className="text-red-600 hover:text-red-800"
>
  🗑️ Eliminar
</button>
```

---

## 📋 Checklist de Implementación

### Inmediato (Fix rápido)
- [ ] Crear `clean_deleted_docs.py`
- [ ] Ejecutar script para limpiar meta.json
- [ ] Reconstruir índice FAISS
- [ ] Verificar que documentos borrados ya no aparecen

### A Mediano Plazo
- [ ] Modificar endpoint `/sources` para solo listar archivos físicos
- [ ] Crear endpoint `DELETE /documents/{filename}`
- [ ] Agregar botón de eliminar en el frontend
- [ ] Testing de eliminación completa

---

## 🎯 Resultado Esperado

### Antes (Problema)
```
📂 docs/: biblia.txt, reglamento.pdf
📋 Frontend lista: biblia.txt, reglamento.pdf, factura.pdf (❌ borrado)
```

### Después (Fix)
```
📂 docs/: biblia.txt, reglamento.pdf
📋 Frontend lista: biblia.txt, reglamento.pdf ✅
```

---

**Resumen**: El índice FAISS (`meta.json`) es **persistente** y no se actualiza automáticamente cuando borras archivos. Necesitas limpiar el índice manualmente o modificar el endpoint `/sources` para que no incluya documentos del índice que no existen físicamente.
