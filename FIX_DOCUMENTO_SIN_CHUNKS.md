# 🔧 Fix: Documento Sin Chunks en el Índice

## 🚨 Problema Detectado

```
[RAG] Búsqueda: filter_source='factura-sitio-web-manabivial.pdf', total_chunks=8231, diversify=False
[RAG] Aplicando filtro: 'factura-sitio-web-manabivial.pdf'
[RAG] ⚠️  Sin resultados para filtro 'factura-sitio-web-manabivial.pdf'
```

### Diagnóstico

1. ✅ **Archivo existe físicamente**: `backend/data/docs/factura-sitio-web-manabivial.pdf`
2. ✅ **Archivo listado en sources**: Aparece en la lista de documentos disponibles
3. ❌ **Sin chunks en meta.json**: El archivo NO tiene ningún fragmento procesado
4. ❌ **Resultado**: Búsquedas en ese documento devuelven vacío

---

## 🔍 Análisis Técnico

### Estado Actual

```python
# Verificación manual:
import json
meta = json.load(open('backend/data/store/meta.json', encoding='utf-8'))

# Contar chunks del archivo
count = sum(1 for s in meta['sources'] if 'factura-sitio-web-manabivial' in s.lower())
print(f"Chunks: {count}")  # Output: 0

# El archivo está en la lista única de fuentes pero sin chunks asociados
unique_sources = set(meta['sources'])
print('factura-sitio-web-manabivial.pdf' in unique_sources)  # True
```

### ¿Por Qué Ocurrió?

Posibles causas:

1. **Fallo durante la ingesta inicial**
   - Error al leer/parsear el PDF
   - PDF corrupto o con formato no estándar
   - Error en el chunking (archivo muy pequeño/vacío)

2. **Problema con PyMuPDF/pypdf**
   - Versión incompatible
   - Límites de memoria/timeout

3. **Deduplicación excesiva**
   - Todos los chunks fueron considerados duplicados
   - Hash collision (muy improbable)

---

## ✅ Soluciones

### Opción 1: Re-ingestar Solo ese Documento (RECOMENDADO)

```bash
# 1. Eliminar el documento del índice actual
cd backend
python -c "
import json
from pathlib import Path

meta_path = Path('data/store/meta.json')
meta = json.load(meta_path.open(encoding='utf-8'))

# Filtrar todo lo que NO sea ese documento
target = 'factura-sitio-web-manabivial.pdf'
indices_to_keep = [i for i, s in enumerate(meta['sources']) if s != target]

# Actualizar meta
meta['chunks'] = [meta['chunks'][i] for i in indices_to_keep]
meta['sources'] = [meta['sources'][i] for i in indices_to_keep]
meta['pages'] = [meta['pages'][i] for i in indices_to_keep]

# Guardar
meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Eliminado {target} del índice')
"

# 2. Re-ingestar solo ese archivo
# Usando la API /rebuild (si existe)
# O eliminando el archivo, reiniciando backend, y subiéndolo de nuevo
```

### Opción 2: Verificar el Contenido del PDF

```bash
# Verificar si el PDF es legible
cd backend
python -c "
import pypdf
from pathlib import Path

pdf_path = Path('data/docs/factura-sitio-web-manabivial.pdf')

try:
    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        print(f'Páginas: {len(reader.pages)}')
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            print(f'Página {i+1}: {len(text)} caracteres')
            if text:
                print(f'Preview: {text[:200]}...')
except Exception as e:
    print(f'ERROR: {e}')
"
```

### Opción 3: Re-construir TODO el Índice (NUCLEAR)

```bash
# ⚠️ CUIDADO: Esto borrará todo y re-procesará todos los documentos

cd backend

# 1. Backup actual
cp data/store/meta.json data/store/meta.json.backup
cp data/store/faiss.index data/store/faiss.index.backup

# 2. Eliminar índice actual
rm data/store/meta.json
rm data/store/faiss.index

# 3. Re-ingestar todos los documentos
# Método A: Usar endpoint /rebuild
curl -X POST http://localhost:8000/rebuild

# Método B: Usar script de ingesta
python -c "
from ingest import build_or_update_index
from pathlib import Path
from config import DOCS_DIR

docs = list(DOCS_DIR.glob('*.pdf')) + list(DOCS_DIR.glob('*.txt')) + list(DOCS_DIR.glob('*.md'))
build_or_update_index([str(d) for d in docs])
print('Índice reconstruido')
"
```

---

## 🛠️ Solución Rápida (FRONTEND)

### Si Solo Necesitas el Archivo Específico

**Opción 1: Re-subir el archivo**

1. Descargar el PDF:
   ```bash
   # Hacer copia de seguridad
   cp backend/data/docs/factura-sitio-web-manabivial.pdf ~/Desktop/
   ```

2. En el frontend, usar el botón de "Upload" para subir el archivo de nuevo

3. El sistema debería:
   - Detectar que el archivo ya existe
   - Re-procesarlo completamente
   - Generar chunks nuevos

**Opción 2: Usar otro documento temporalmente**

Mientras se soluciona el problema, el usuario puede:
- Buscar en "Todos los documentos" (búsqueda global)
- El RAG encontrará información similar en otros documentos

---

## 🔧 Implementación del Fix

### Script de Diagnóstico

```python
# backend/scripts/check_missing_chunks.py
import json
from pathlib import Path
from collections import Counter

meta_path = Path('backend/data/store/meta.json')
meta = json.load(meta_path.open(encoding='utf-8'))

# Contar chunks por documento
chunk_counts = Counter(meta['sources'])

print("📊 Chunks por documento:")
print("=" * 60)

for source in sorted(chunk_counts.keys()):
    count = chunk_counts[source]
    status = "✅" if count > 0 else "❌ SIN CHUNKS"
    print(f"{status} {source}: {count} chunks")

# Documentos sin chunks
no_chunks = [s for s, c in chunk_counts.items() if c == 0]
if no_chunks:
    print(f"\n🚨 Documentos SIN chunks: {len(no_chunks)}")
    for doc in no_chunks:
        print(f"  - {doc}")
else:
    print("\n✅ Todos los documentos tienen chunks")
```

### Script de Reparación

```python
# backend/scripts/fix_document.py
import sys
from pathlib import Path
from ingest import build_or_update_index
from config import DOCS_DIR

def fix_document(filename: str):
    """Re-ingesta un documento específico."""
    doc_path = DOCS_DIR / filename
    
    if not doc_path.exists():
        print(f"❌ Archivo no encontrado: {doc_path}")
        return
    
    print(f"🔧 Re-ingesting: {filename}")
    
    # Eliminar del índice actual (opcional)
    # TODO: implementar eliminación selectiva
    
    # Re-ingestar
    try:
        build_or_update_index([str(doc_path)])
        print(f"✅ {filename} re-ingested successfully")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_document.py <filename>")
        sys.exit(1)
    
    fix_document(sys.argv[1])
```

---

## 📋 Plan de Acción

### Inmediato (para el usuario)

1. **Explicar el problema**:
   ```
   El documento "factura-sitio-web-manabivial.pdf" no se procesó correctamente 
   durante la ingesta inicial. Existe físicamente pero no tiene fragmentos 
   indexados en el sistema RAG.
   ```

2. **Solución temporal**:
   ```
   Por ahora, usa "Buscar en todos los documentos" (sin seleccionar archivo 
   específico) para buscar información relacionada en todo el corpus.
   ```

3. **Solución permanente**:
   ```
   Re-sube el documento usando el botón de Upload en el frontend. 
   El sistema lo re-procesará automáticamente.
   ```

### A Mediano Plazo (desarrollo)

1. ✅ **Agregar validación en ingesta**
   ```python
   # En ingest.py, después de procesar:
   if not chunks_for_doc:
       logger.warning(f"⚠️ Document {filename} produced 0 chunks!")
   ```

2. ✅ **Health check endpoint**
   ```python
   @app.get("/health/documents")
   def check_documents_health():
       """Retorna documentos sin chunks o con problemas."""
       index, chunks, sources, pages = ingest.load_index_safe()
       
       from collections import Counter
       counts = Counter(sources)
       
       no_chunks = [s for s, c in counts.items() if c == 0]
       low_chunks = [s for s, c in counts.items() if 0 < c < 5]
       
       return {
           "no_chunks": no_chunks,
           "low_chunks": low_chunks,
           "total_docs": len(counts),
           "total_chunks": len(chunks)
       }
   ```

3. ✅ **UI para re-procesar documentos**
   ```tsx
   // En frontend, botón para re-ingestar documento específico
   <button onClick={() => reprocessDocument(doc.name)}>
     🔄 Re-procesar
   </button>
   ```

---

## 🎯 Resultado Esperado

Después del fix:

```
[RAG] Búsqueda: filter_source='factura-sitio-web-manabivial.pdf', total_chunks=8231, diversify=False
[RAG] Aplicando filtro: 'factura-sitio-web-manabivial.pdf'
[RAG] Filtro aplicado: 342 → 15 chunks  ✅
```

El documento ahora tiene chunks y las búsquedas funcionan correctamente.

---

## 📚 Referencias

- `backend/ingest.py` - Función `build_or_update_index()` línea ~230
- `backend/rag.py` - Función `search()` con filtro línea ~249-263
- `backend/data/store/meta.json` - Estructura de metadatos

---

## ⚠️ Prevención Futura

### Mejoras al Proceso de Ingesta

1. **Logging detallado por archivo**
   ```python
   logger.info(f"Processing {filename}...")
   logger.info(f"  - Extracted {len(pages)} pages")
   logger.info(f"  - Generated {len(chunks)} chunks")
   logger.info(f"  - After dedup: {len(final_chunks)} chunks")
   ```

2. **Validación post-ingesta**
   ```python
   if len(final_chunks) == 0:
       logger.error(f"❌ ZERO chunks for {filename}!")
       # Opcionalmente: raise o notificar
   ```

3. **Reporte de salud automático**
   ```python
   # Al finalizar ingesta completa
   print("\n📊 Ingestion Summary:")
   for filename in processed_files:
       count = sum(1 for s in sources if s == filename)
       print(f"  - {filename}: {count} chunks")
   ```

---

**Última actualización**: 2025-10-11  
**Estado**: Documentado, pendiente de fix
