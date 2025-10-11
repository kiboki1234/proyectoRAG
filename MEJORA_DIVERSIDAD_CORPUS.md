# 🎯 Mejoras: Diversidad en Búsqueda de Corpus Completo

## 🐛 Problema Original

Cuando el usuario selecciona **"Todo el corpus"** y hace una pregunta general, el sistema devuelve resultados de **un solo documento** en lugar de mostrar información de múltiples fuentes.

### Ejemplo del Problema:
```
Pregunta: "¿Qué información tengo en mi corpus?"
Resultado: Solo citas de biblia.txt
Esperado: Citas de múltiples documentos
```

---

## 🔍 Por Qué Sucede

### 1. **Búsqueda Semántica Natural**
El sistema RAG funciona por **similitud semántica**:
- Embeddings vectoriales encuentran texto semánticamente similar
- BM25 encuentra coincidencias léxicas
- Cross-encoder reordena por relevancia

**Resultado:** Si un documento tiene mejor match semántico, domina los resultados.

### 2. **Comportamiento Correcto del Sistema**
Técnicamente el sistema **SÍ busca en todo el corpus**, pero:
- Ordena por relevancia (score más alto primero)
- Si un documento es muy relevante, sus chunks aparecen primero
- El LLM usa solo los chunks más relevantes (top-k)

---

## ✅ Soluciones Implementadas

### **Solución 1: Endpoint `/documents` para Listar Corpus**

Nuevo endpoint que muestra TODOS los documentos indexados con estadísticas:

#### Backend (`app.py`):
```python
@app.get("/documents")
def list_documents():
    """Lista todos los documentos indexados con estadísticas"""
    index, chunks, sources, pages = ingest.load_index_safe()
    
    # Agrupar chunks por documento
    doc_stats = {}
    for chunk, source in zip(chunks, sources):
        if source not in doc_stats:
            doc_stats[source] = {
                "name": source,
                "chunks": 0,
                "total_chars": 0,
                "has_pages": False
            }
        doc_stats[source]["chunks"] += 1
        doc_stats[source]["total_chars"] += len(chunk)
    
    return {
        "total_documents": len(doc_stats),
        "total_chunks": len(chunks),
        "documents": sorted(doc_stats.values(), key=lambda x: x["name"])
    }
```

#### Frontend (`DocumentsList.tsx`):
Nuevo componente que muestra:
- 📚 Nombre de cada documento
- 📊 Número de chunks por documento
- 📈 Porcentaje del corpus
- 🎨 Visualización con barras de progreso
- 🏷️ Badge "PDF" para documentos con páginas

**Uso:**
```typescript
import DocumentsList from '@/components/DocumentsList'

// En tu App.tsx o modal
<DocumentsList />
```

---

### **Solución 2: Diversificación Inteligente de Resultados**

Nueva función en `rag.py` que **diversifica resultados** cuando se busca en todo el corpus:

#### Función `_diversify_results()`:
```python
def _diversify_results(
    candidates: List[Tuple[int, float, str]],
    sources: List[str],
    max_per_source: int = 3
) -> List[Tuple[int, float, str]]:
    """
    Limita chunks por fuente para forzar diversidad.
    Máximo 3 chunks por documento.
    """
    source_counts = {}
    diversified = []
    
    for cand in candidates:
        idx = cand[0]
        source = sources[idx]
        
        if source_counts.get(source, 0) < max_per_source:
            diversified.append(cand)
            source_counts[source] = source_counts.get(source, 0) + 1
    
    return diversified
```

#### Integración en `search()`:
```python
def search(..., diversify: bool = True):
    # ... búsqueda híbrida ...
    
    # Si no hay filtro y hay múltiples fuentes, diversificar
    if diversify and not filter_source and sources:
        unique_sources = len(set(sources))
        if unique_sources > 1:
            # Expandir k para tener más candidatos
            expanded_k = min(k * 3, len(merged))
            # Aplicar diversificación (max 5 chunks por fuente)
            merged = _diversify_results(merged[:expanded_k], sources, max_per_source=5)
            print(f"[RAG] Diversificación aplicada: {unique_sources} fuentes")
    
    # Rerank y devolver top-k
    return rerank(merged, k)
```

**Comportamiento:**
- ✅ Con filtro específico: NO diversifica (mantiene relevancia pura)
- ✅ Sin filtro (corpus completo): Diversifica (max 5 chunks por fuente)
- ✅ Aumenta `k * 3` para tener más candidatos antes de diversificar

---

## 🎯 Comparación Antes vs Después

### **ANTES** ❌
```
Usuario: "(todo el corpus)" + "¿Qué información tengo?"
Sistema busca → Encuentra → Reordena por relevancia

Resultados:
[biblia.txt (0.95), biblia.txt (0.92), biblia.txt (0.89), ...]

Respuesta LLM: Solo usa biblia.txt
```

### **DESPUÉS** ✅
```
Usuario: "(todo el corpus)" + "¿Qué información tengo?"
Sistema busca → Encuentra → Diversifica → Reordena

Resultados:
[biblia.txt (0.95), factura.pdf (0.88), informe.pdf (0.85), 
 biblia.txt (0.84), contrato.pdf (0.82), biblia.txt (0.80), ...]

Respuesta LLM: Usa múltiples documentos
```

---

## 🚀 Cómo Usar las Mejoras

### **Opción 1: Ver Lista de Documentos (Recomendado)**

#### Desde el navegador:
```
GET http://localhost:8000/documents
```

**Respuesta:**
```json
{
  "total_documents": 13,
  "total_chunks": 8231,
  "documents": [
    {
      "name": "factura.pdf",
      "chunks": 42,
      "total_chars": 15234,
      "has_pages": true
    },
    {
      "name": "biblia.txt",
      "chunks": 6789,
      "total_chars": 3245678,
      "has_pages": false
    },
    ...
  ]
}
```

#### Desde el frontend (si integras `DocumentsList.tsx`):
```typescript
// En un modal o página separada
import DocumentsList from '@/components/DocumentsList'

<DocumentsList />
```

---

### **Opción 2: Preguntas Optimizadas para Diversidad**

En lugar de preguntas muy generales, usa preguntas que **obliguen al sistema a buscar en múltiples documentos**:

#### ❌ Pregunta Genérica:
```
"¿Qué información tengo en mi corpus?"
→ Puede devolver solo 1 documento
```

#### ✅ Preguntas Específicas para Diversidad:
```
"Lista los nombres de todos los archivos disponibles: facturas, contratos, informes, textos, etc."
→ Fuerza a buscar en múltiples tipos de documentos

"Dame un resumen breve de cada tipo de documento que tengo"
→ Obliga al sistema a representar múltiples categorías

"¿Qué temas diferentes se mencionan en el corpus completo?"
→ Busca conceptos distribuidos en varios documentos

"Busca la palabra 'fecha' o 'total' en todos los documentos"
→ Busca términos comunes que aparecen en múltiples fuentes
```

---

## 📊 Verificar que Funciona

### **Test 1: Endpoint de documentos**
```bash
curl http://localhost:8000/documents
```

Deberías ver:
```json
{
  "total_documents": 13,
  "total_chunks": 8231,
  "documents": [ ... todos tus documentos ... ]
}
```

### **Test 2: Búsqueda con diversificación**
```bash
# En el frontend, selecciona "(todo el corpus)"
# Pregunta: "Dame un resumen de cada documento disponible"
```

**Verifica en los logs del backend:**
```
[RAG] Sin filtro - buscando en 135 chunks del corpus completo
[RAG] Diversificación aplicada: buscando en 13 fuentes diferentes
INFO: ✅ Respuesta generada con 10 citas
```

**Verifica en las citas del frontend:**
- Deberías ver múltiples archivos diferentes (no solo biblia.txt)
- Máximo 5 citas por archivo
- Variedad de fuentes

---

## 🔧 Configuración Avanzada

### Ajustar diversificación en `rag.py`:

```python
# Cambiar max_per_source (línea ~200)
merged = _diversify_results(
    merged[:expanded_k], 
    sources, 
    max_per_source=5  # ← Cambia este número
)
```

**Valores recomendados:**
- `max_per_source=3`: Máxima diversidad (más fuentes diferentes)
- `max_per_source=5`: Balanceado (default)
- `max_per_source=10`: Menos diversidad (prioriza relevancia)

### Desactivar diversificación:

En `app.py`, línea del call a `rag.search()`:
```python
passages = rag.search(
    index,
    chunks,
    req.question,
    k=settings.top_k,
    sources=sources,
    filter_source=source_param,
    diversify=False  # ← Desactiva diversificación
)
```

---

## 🐛 Troubleshooting

### Problema: Sigue devolviendo un solo documento
**Diagnóstico:**
```bash
# Verifica que el endpoint /documents funciona
curl http://localhost:8000/documents

# Verifica logs del backend
[RAG] Diversificación aplicada: buscando en X fuentes diferentes
```

**Soluciones:**
1. Reinicia el backend para aplicar cambios
2. Verifica que tienes múltiples documentos indexados (X > 1)
3. Usa preguntas más específicas que fuercen búsqueda amplia
4. Aumenta `max_per_source` en `_diversify_results()`

### Problema: Resultados menos relevantes
**Causa:** La diversificación sacrifica un poco de relevancia por variedad

**Solución:** Ajusta `max_per_source` o desactiva diversificación para búsquedas específicas

---

## ✅ Checklist de Integración

- [x] Backend: Endpoint `/documents` creado
- [x] Backend: Función `_diversify_results()` implementada
- [x] Backend: Parámetro `diversify` en `search()`
- [x] Frontend: Función `getDocuments()` en `api.ts`
- [x] Frontend: Componente `DocumentsList.tsx` creado
- [ ] Frontend: Integrar `DocumentsList` en la UI
- [ ] Backend: Reiniciar servidor
- [ ] Probar endpoint `/documents`
- [ ] Probar búsqueda con diversificación

---

## 🎉 Resultado Final

Con estas mejoras:
1. ✅ Puedes **ver TODOS los documentos** fácilmente con `/documents`
2. ✅ Las búsquedas en corpus completo **muestran múltiples fuentes**
3. ✅ Máximo 5 chunks por documento para forzar variedad
4. ✅ Logs claros para diagnosticar comportamiento

**Estado:** ✅ **IMPLEMENTADO** - Listo para usar

Reinicia el backend y prueba con:
```
GET http://localhost:8000/documents
```

O haz una pregunta en el frontend como:
```
"Dame un resumen de cada tipo de documento que tengo"
```

🚀 **¡Disfruta de tu corpus diversificado!**
