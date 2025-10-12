# ✅ FIX: Documentos Borrados Ya No Aparecen en el Frontend

## 🎯 Problema Resuelto

**Síntoma**: Borrabas documentos de `backend/data/docs/` pero seguían apareciendo en la lista del frontend.

**Causa**: El endpoint `/sources` incluía documentos del índice FAISS (`meta.json`) aunque hubieran sido borrados físicamente.

---

## 🔧 Solución Implementada

### 1. Fix en el Backend (`app.py`)

**Antes**:
```python
@app.get("/sources")
def list_sources():
    names = set()
    
    # 1) Archivos en docs/
    for pattern in ("*.pdf", "*.md", "*.txt"):
        for p in settings.docs_dir.glob(pattern):
            names.add(p.name)
    
    # 2) Archivos en el índice (meta.json)
    _, _, sources, _ = ingest.load_index()
    for s in sources:
        names.add(s)  # ⚠️ Incluye borrados!
    
    return {"sources": sorted(names)}
```

**Después**:
```python
@app.get("/sources")
def list_sources():
    """Lista SOLO archivos que existen físicamente en docs/"""
    names = set()
    
    # Solo archivos del filesystem
    for pattern in ("*.pdf", "*.md", "*.txt"):
        for p in settings.docs_dir.glob(pattern):
            if p.is_file():
                names.add(p.name)
    
    # 🔧 FIX: NO incluir archivos del índice
    
    return {"sources": sorted(names)}
```

### 2. Script de Limpieza (`clean_deleted_docs.py`)

Para limpiar el índice de documentos ya borrados:

```bash
# Ejecutar desde la raíz del proyecto
python clean_deleted_docs.py
```

**Qué hace**:
1. Lee `meta.json`
2. Compara con archivos en `docs/`
3. Identifica documentos borrados
4. Elimina sus chunks del índice
5. Guarda `meta.json` actualizado

---

## 📋 Pasos para Aplicar

### Paso 1: Reiniciar Backend

El cambio en `app.py` ya está aplicado, solo necesitas reiniciar:

```powershell
# En el terminal "uvicorn", presiona Ctrl+C y luego:
cd backend
python run_dev.py
```

Con uvicorn en modo `--reload`, debería detectar el cambio automáticamente.

### Paso 2: (Opcional) Limpiar Índice

Si ya tienes documentos borrados en el índice:

```powershell
# Ejecutar el script de limpieza
python clean_deleted_docs.py

# Confirmar cuando pregunte (s/N)
```

### Paso 3: (Opcional) Reconstruir FAISS

Si limpiaste el índice con el script:

```powershell
# Opción A: Eliminar índice FAISS (se reconstruirá auto)
cd backend\data\store
del faiss.index

# Opción B: Usar endpoint rebuild (si existe)
# En PowerShell:
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/rebuild"
```

---

## 🎯 Resultado

### Antes (Problema)

```
📂 backend/data/docs/
├── biblia.txt           ✅
├── reglamento.pdf       ✅
└── (factura.pdf borrado)

📋 Frontend muestra:
├── biblia.txt           ✅
├── factura.pdf          ❌ BORRADO pero aparece
└── reglamento.pdf       ✅
```

### Después (Fix)

```
📂 backend/data/docs/
├── biblia.txt           ✅
└── reglamento.pdf       ✅

📋 Frontend muestra:
├── biblia.txt           ✅
└── reglamento.pdf       ✅
```

---

## 📊 Comportamiento Nuevo

| Acción | Antes | Después |
|--------|-------|---------|
| Borras documento de `docs/` | ❌ Sigue en lista | ✅ Desaparece inmediatamente |
| Documento solo en índice | ❌ Aparece en lista | ✅ NO aparece |
| Subes nuevo documento | ✅ Aparece | ✅ Aparece |

---

## 🚀 Mejora Futura: Endpoint de Eliminación

Para eliminar documentos correctamente (archivo + índice):

```python
# backend/app.py - FUTURO

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Elimina documento completamente:
    1. Archivo físico de docs/
    2. Chunks del índice (meta.json)
    3. Reconstruye FAISS
    """
    # 1. Eliminar archivo
    doc_path = settings.docs_dir / filename
    doc_path.unlink()
    
    # 2. Limpiar índice
    meta = json.load(...)
    meta['chunks'] = [c for i, c in enumerate(meta['chunks']) 
                      if meta['sources'][i] != filename]
    # ... (guardar)
    
    # 3. Reconstruir FAISS
    rebuild_faiss_index()
    
    return {"success": True}
```

Y en el frontend:

```tsx
<button onClick={() => deleteDocument(doc.name)}>
  🗑️ Eliminar
</button>
```

---

## 📚 Archivos Modificados

- ✅ `backend/app.py` (líneas ~420-442)
- ✅ `clean_deleted_docs.py` (script nuevo)
- ✅ `PROBLEMA_DOCUMENTOS_BORRADOS.md` (documentación)
- ✅ Este archivo: `FIX_DOCUMENTOS_BORRADOS.md`

---

## ✅ Checklist de Validación

- [x] Modificado endpoint `/sources` en `app.py`
- [x] Creado script de limpieza `clean_deleted_docs.py`
- [x] Documentación completa del problema y fix
- [ ] Backend reiniciado (⏳ pendiente del usuario)
- [ ] Script de limpieza ejecutado (⏳ opcional si hay docs borrados)
- [ ] Verificar que lista solo muestra docs existentes (⏳ pendiente)

---

**Próximo paso**: Reinicia el backend (Ctrl+C + `python run_dev.py`) y verifica que ahora solo aparecen documentos que existen en `docs/` 🎉
