# 🔍 Análisis Completo: "Sin resultados" para factura-sitio-web-manabivial.pdf

## ✅ Diagnóstico Final

### El Problema Real NO es lo que pensábamos

**Creencia inicial**: ❌ El documento no tiene chunks  
**Realidad**: ✅ **El documento SÍ tiene 2 chunks procesados correctamente**

```
Chunk 58 (Página 1): Encabezado de factura (RUC, autorización, dirección)
Chunk 59 (Página 1): Factura completa con detalles del servicio
```

### El Problema Real

**El filtro funciona correctamente**, pero los chunks del documento **NO aparecen en los resultados de búsqueda vectorial/BM25** porque:

1. **Pregunta del usuario**: "de que trata este documento"
2. **Contenido del documento**: Factura con datos técnicos (RUC, fechas, servicios, precios)
3. **Relevancia semántica**: BAJA ❌
4. **Resultado**: Los chunks 58 y 59 no están en el `top_k` inicial de búsqueda vectorial

---

## 📊 Flujo del Problema

```
1. Usuario pregunta: "de que trata este documento"
   + Selecciona: factura-sitio-web-manabivial.pdf

2. Sistema genera embedding de la pregunta
   ↓
3. Búsqueda vectorial (FAISS)
   → Encuentra chunks más similares semánticamente
   → top_k=50 candidatos
   → ⚠️ Chunks 58 y 59 NO están en el top 50 (baja similitud)

4. Búsqueda BM25 (keyword matching)
   → Busca palabras clave: "trata", "documento"
   → ⚠️ Chunks 58 y 59 no contienen esas palabras

5. Merge (vectorial + BM25)
   → merged = [lista de chunks encontrados]
   → ⚠️ NO incluye chunks 58 y 59

6. Filtro por documento
   → filter_source = 'factura-sitio-web-manabivial.pdf'
   → Filtra merged para solo chunks de ese documento
   → ⚠️ merged NO contiene chunks 58 y 59
   → Resultado: [] (vacío)

7. Output: "⚠️ Sin resultados para filtro 'factura-sitio-web-manabivial.pdf'"
```

---

## 🎯 Solución

### Opción 1: Modificar el Flujo de Búsqueda (RECOMENDADO)

Cuando `filter_source` está presente, **primero filtrar, luego buscar**:

```python
# En rag.py, función search()

def search(
    index,
    chunks: List[str],
    query: str,
    k: int = TOP_K,
    *,
    sources: Optional[List[str]] = None,
    filter_source: Optional[str] = None,
    diversify: bool = True,
) -> List[Tuple[int, float, str]]:
    """..."""
    
    # 🔧 NUEVO: Si hay filtro, pre-filtrar chunks e índices
    if filter_source and filter_source.strip() and sources:
        fs = filter_source.strip().lower()
        print(f"[RAG] Pre-filtro: buscando solo en '{fs}'")
        
        # Índices de chunks que pertenecen al documento filtrado
        filtered_indices = [
            i for i, s in enumerate(sources)
            if s and (s.lower() == fs or fs in s.lower())
        ]
        
        if not filtered_indices:
            print(f"[RAG] ⚠️ Documento '{fs}' no encontrado en el índice")
            return []
        
        print(f"[RAG] Documento tiene {len(filtered_indices)} chunks")
        
        # Crear sub-índice FAISS temporal solo con esos chunks
        filtered_chunks = [chunks[i] for i in filtered_indices]
        filtered_index = _create_temp_index(index, filtered_indices)
        
        # Buscar SOLO en ese sub-índice
        # (resto de la función search pero con filtered_chunks y filtered_index)
        ...
    else:
        # Búsqueda normal sin filtro
        ...
```

### Opción 2: Forzar Inclusión de Chunks del Documento Filtrado

Cuando hay filtro, **incluir TODOS los chunks del documento** en los candidatos iniciales:

```python
# Después de merge (línea ~247)

if filter_source and filter_source.strip() and sources:
    fs = filter_source.strip().lower()
    
    # Índices de TODOS los chunks del documento
    doc_indices = [
        i for i, s in enumerate(sources)
        if s and (s.lower() == fs or fs in s.lower())
    ]
    
    if not doc_indices:
        print(f"[RAG] ⚠️ Sin chunks para documento '{fs}'")
        return []
    
    print(f"[RAG] Documento '{fs}' tiene {len(doc_indices)} chunks")
    
    # 🔧 AGREGAR todos los chunks del documento a merged
    # (aunque no estén en top_k de búsqueda)
    for idx in doc_indices:
        if idx not in seen:
            # Score bajo pero los incluimos
            merged.append((idx, 0.0, chunks[idx]))
            seen.add(idx)
    
    # Ahora filtrar por documento (ya están incluidos)
    merged = [c for c in merged if sources[c[0]].lower() == fs or fs in sources[c[0]].lower()]
    print(f"[RAG] Filtrado: {len(merged)} chunks del documento")
```

### Opción 3: Búsqueda Híbrida con Fallback

Si búsqueda vectorial + BM25 devuelve 0 resultados para un documento específico, hacer fallback a **devolver los primeros N chunks del documento**:

```python
if filter_source and filter_source.strip() and sources:
    fs = filter_source.strip().lower()
    exact = [c for c in merged if (sources[c[0]] or "").lower() == fs or fs in (sources[c[0]] or "").lower()]
    
    if exact:
        merged = exact
    else:
        # 🔧 FALLBACK: devolver primeros N chunks del documento
        print(f"[RAG] ⚠️ Sin match semántico, usando fallback...")
        doc_indices = [
            i for i, s in enumerate(sources)
            if s and (s.lower() == fs or fs in s.lower())
        ]
        
        if doc_indices:
            # Tomar primeros k chunks del documento
            fallback_chunks = doc_indices[:min(k, len(doc_indices))]
            merged = [(i, 0.5, chunks[i]) for i in fallback_chunks]
            print(f"[RAG] Fallback: devolviendo {len(merged)} chunks del documento")
        else:
            print(f"[RAG] ⚠️ Documento no encontrado: '{fs}'")
            return []
```

---

## 🚀 Implementación Recomendada

### **Opción 2 + Opción 3** (Híbrido)

1. **Forzar inclusión** de chunks del documento en candidatos
2. **Si aún así no hay match**, usar fallback de primeros N chunks

```python
def search(...):
    # ... búsqueda vectorial y BM25 ...
    
    # 4) Filtro por archivo
    if filter_source and filter_source.strip() and sources:
        fs = filter_source.strip().lower()
        print(f"[RAG] Aplicando filtro: '{fs}'")
        
        # 🔧 PASO 1: Identificar todos los chunks del documento
        doc_indices = [
            i for i, s in enumerate(sources)
            if s and (s.lower() == fs or fs in s.lower())
        ]
        
        if not doc_indices:
            print(f"[RAG] ⚠️ Documento '{fs}' no existe en el índice")
            return []
        
        print(f"[RAG] Documento tiene {len(doc_indices)} chunks totales")
        
        # 🔧 PASO 2: Agregar todos los chunks del documento a merged
        for idx in doc_indices:
            if idx not in seen:
                merged.append((idx, 0.1, chunks[idx]))  # Score bajo
                seen.add(idx)
        
        # 🔧 PASO 3: Filtrar merged por documento
        exact = [c for c in merged if sources[c[0]].lower() == fs or fs in sources[c[0]].lower()]
        
        if exact:
            print(f"[RAG] Filtro aplicado: {len(merged)} → {len(exact)} chunks")
            merged = exact
        else:
            # 🔧 PASO 4: Fallback (no debería llegar aquí si PASO 2 funciona)
            print(f"[RAG] ⚠️ Fallback: devolviendo primeros {min(k, len(doc_indices))} chunks")
            merged = [(i, 0.5, chunks[i]) for i in doc_indices[:min(k, len(doc_indices))]]
    
    # ... resto del código (diversificación, rerank) ...
```

---

## 📝 Ejemplo de Uso

### Antes (problema):
```
Usuario: "de que trata este documento"
Documento: factura-sitio-web-manabivial.pdf

[RAG] Búsqueda: filter_source='factura-sitio-web-manabivial.pdf', total_chunks=8231
[RAG] Aplicando filtro: 'factura-sitio-web-manabivial.pdf'
[RAG] ⚠️ Sin resultados para filtro 'factura-sitio-web-manabivial.pdf'
```

### Después (fix):
```
Usuario: "de que trata este documento"
Documento: factura-sitio-web-manabivial.pdf

[RAG] Búsqueda: filter_source='factura-sitio-web-manabivial.pdf', total_chunks=8231
[RAG] Aplicando filtro: 'factura-sitio-web-manabivial.pdf'
[RAG] Documento tiene 2 chunks totales
[RAG] Filtro aplicado: 52 → 2 chunks
[RAG] Reranking 2 chunks...
```

**Respuesta del LLM**:
```
Este documento es una FACTURA electrónica emitida por ESPINOZA YUNGAN JAVIER JHOSUE 
a la EMPRESA PUBLICA DE INFRAESTRUCTURA Y VIALIDAD DE MANABI (MANABI VIAL EP), 
con fecha 15/09/2025. El documento detalla:

- Servicio: MANTENIMIENTO Y REESTRUCTURACIÓN DEL DISEÑO DE LA PÁGINA WEB DE MANABÍ VIAL EP
- Valor del servicio: $5,200.00
- IVA 15%: $780.00
- Valor total: $5,980.00
- Número de autorización: 1509202501172417764500120011000000000103369126211
- Guía: 001-100-000000010
```

---

## 🎯 Resumen

| Aspecto | Estado |
|---------|--------|
| Documento tiene chunks | ✅ SÍ (2 chunks) |
| Chunks procesados correctamente | ✅ SÍ |
| Problema con ingesta | ❌ NO |
| Problema con búsqueda semántica | ✅ SÍ (chunks no en top_k) |
| Solución | 🔧 Forzar inclusión de chunks del documento filtrado |

---

**Próximos pasos**: Implementar Opción 2 + Opción 3 en `backend/rag.py`
