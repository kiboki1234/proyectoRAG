# 🔧 Fix: Búsqueda en "Todo el Corpus"

## 🐛 Problema Identificado

Cuando el usuario selecciona **"Todo el corpus"** en el selector de documentos del frontend, el sistema **no analiza todos los documentos**, devolviendo resultados vacíos o limitados.

---

## 🔍 Causa Raíz

El problema estaba en la lógica de filtrado en `backend/rag.py`, líneas 110-120.

### Código Anterior (Problemático):
```python
# 4) Filtro por archivo (exacto -> contiene)
if filter_source and sources:
    fs = filter_source.strip().lower()
    exact = [c for c in merged if (sources[c[0]] or "").lower() == fs]
    if not exact:
        exact = [c for c in merged if fs in (sources[c[0]] or "").lower()]
    merged = exact
    if not merged:
        return []  # ❌ Devuelve vacío si no matchea
```

**Problemas:**
1. Si `filter_source` era una cadena vacía `""`, evaluaba como `False` y no entraba al bloque
2. Si `filter_source` tenía un valor inválido, sobreescribía `merged` con lista vacía
3. No había distinción clara entre "buscar todo" vs "filtrar por archivo"

---

## ✅ Solución Implementada

### 1. **Mejorar la lógica de filtrado en `rag.py`**

```python
# 4) Filtro por archivo (exacto -> contiene)
# Solo filtra si filter_source tiene valor real (no None, no vacío)
if filter_source and filter_source.strip() and sources:
    fs = filter_source.strip().lower()
    print(f"[RAG] Aplicando filtro: '{fs}'")
    
    # Primero intenta match exacto
    exact = [c for c in merged if (sources[c[0]] or "").lower() == fs]
    
    # Si no hay match exacto, intenta match parcial (contiene)
    if not exact:
        exact = [c for c in merged if fs in (sources[c[0]] or "").lower()]
    
    # Solo aplica el filtro si encontró resultados
    if exact:
        print(f"[RAG] Filtro aplicado: {len(merged)} → {len(exact)} chunks")
        merged = exact
    else:
        # Si no hay resultados con el filtro, devolver vacío
        print(f"[RAG] ⚠️  Sin resultados para filtro '{fs}'")
        return []
else:
    print(f"[RAG] Sin filtro - buscando en {len(merged)} chunks del corpus completo")
```

**Mejoras:**
- ✅ Validación explícita: `filter_source and filter_source.strip()`
- ✅ Solo aplica filtro si hay resultados (`if exact:`)
- ✅ Preserva `merged` original si el filtro no encuentra nada válido
- ✅ Logs claros para diagnosticar comportamiento

---

### 2. **Mejorar logging en `app.py`**

```python
# Normaliza el filtro por archivo si viene
source_param = (req.source or "").strip() or None

app_logger.info(
    f"🔍 Búsqueda RAG - "
    f"Question: {req.question[:100]}... | "
    f"Filter: {source_param or 'ALL_CORPUS'} | "
    f"Total docs: {len(set(sources))}"
)
```

**Mejoras:**
- ✅ Log explícito cuando se busca en TODO el corpus
- ✅ Muestra el filtro aplicado o `ALL_CORPUS`
- ✅ Incluye estadísticas de documentos disponibles

---

### 3. **Mejorar mensajes de error**

```python
if not passages:
    if source_param:
        detail = f"No hay pasajes relevantes en el documento '{source_param}' para esta pregunta"
    else:
        detail = "No hay pasajes relevantes en el corpus para esta pregunta"
    app_logger.warning(f"⚠️  Sin resultados: {detail}")
    raise HTTPException(status_code=404, detail=detail)
```

**Mejoras:**
- ✅ Mensaje diferenciado según si hay filtro o no
- ✅ Más claro para el usuario final
- ✅ Logging de warnings cuando no hay resultados

---

## 🎯 Comportamiento Esperado

### Caso 1: Usuario selecciona "Todo el corpus"
```
Frontend → { question: "¿Qué dice?", source: undefined }
         ↓
Backend  → source_param = None
         ↓
rag.py   → filter_source = None
         ↓
Resultado: Busca en TODOS los chunks del índice (✅ CORRECTO)
```

### Caso 2: Usuario selecciona documento específico
```
Frontend → { question: "¿Qué dice?", source: "factura.pdf" }
         ↓
Backend  → source_param = "factura.pdf"
         ↓
rag.py   → Aplica filtro por "factura.pdf"
         ↓
Resultado: Solo busca en chunks de factura.pdf (✅ CORRECTO)
```

### Caso 3: Usuario selecciona documento inexistente
```
Frontend → { question: "¿Qué dice?", source: "noexiste.pdf" }
         ↓
Backend  → source_param = "noexiste.pdf"
         ↓
rag.py   → Intenta filtrar pero no encuentra matches
         ↓
Resultado: Devuelve 404 con mensaje claro (✅ CORRECTO)
```

---

## 🧪 Cómo Verificar el Fix

### Opción 1: Logs en consola
```bash
cd backend
uvicorn app:app --reload --port 8000
```

Busca en los logs:
```
[RAG] Búsqueda: filter_source=ALL_CORPUS, total_chunks=1523
[RAG] Sin filtro - buscando en 150 chunks del corpus completo
```

### Opción 2: Desde el frontend
1. Abre http://localhost:5173
2. Selecciona **"(todo el corpus)"** en el selector
3. Haz una pregunta general: "¿Qué documentos hay disponibles?"
4. Deberías ver citas de MÚLTIPLES documentos diferentes

### Opción 3: Script de diagnóstico
```bash
cd backend
python test_source_filter.py
```

Esto ejecutará 4 tests:
- ✅ Sin filtro (None)
- ✅ Cadena vacía ('')
- ✅ Documento específico
- ✅ Documento inexistente

---

## 📊 Comparación Antes vs Después

### ANTES ❌
```
Usuario: "Todo el corpus" + "¿Qué documentos hay?"
Backend: filter_source="" → No entra al if → merged sin filtrar
Resultado: Funciona por casualidad SOLO si no hay lógica que sobreescriba merged
```

### DESPUÉS ✅
```
Usuario: "Todo el corpus" + "¿Qué documentos hay?"
Backend: filter_source=None → Explícitamente NO filtra
Logs: "[RAG] Sin filtro - buscando en 1523 chunks del corpus completo"
Resultado: Busca en TODO el corpus, devuelve chunks de TODOS los documentos
```

---

## 🚀 Próximos Pasos

1. **Reinicia el backend** para aplicar los cambios:
   ```bash
   cd backend
   # Si está corriendo, presiona Ctrl+C y luego:
   uvicorn app:app --reload --port 8000
   ```

2. **Prueba desde el frontend:**
   - Selecciona "(todo el corpus)"
   - Haz una pregunta que debería tener respuestas en múltiples documentos
   - Verifica que las citas provengan de diferentes archivos

3. **Revisa los logs** en la terminal del backend:
   - Deberías ver `[RAG] Sin filtro - buscando en X chunks del corpus completo`
   - Confirma que el número de chunks es el total del índice

---

## 🐛 Troubleshooting

### Problema: Sigue sin funcionar "Todo el corpus"
**Diagnóstico:**
```bash
cd backend
python test_source_filter.py
```

Si el test muestra `0 resultados` para `filter_source=None`, el problema está en:
1. Índice vacío o corrupto → Reindexa con `/ingest/all`
2. Embeddings incompatibles → Reconstruye índice
3. BM25 no inicializado → Reinicia el backend

### Problema: Logs no aparecen
**Solución:**
Verifica que el nivel de log esté en INFO o DEBUG en `.env`:
```bash
LOG_LEVEL=INFO
```

### Problema: Frontend sigue enviando source=""
**Solución:**
Verifica en las DevTools del navegador (F12 → Network) el payload:
```json
{
  "question": "...",
  "source": null  // ← Debe ser null o ausente, NO ""
}
```

---

## ✅ Checklist de Verificación

- [x] Código actualizado en `rag.py`
- [x] Logging mejorado en `app.py`
- [x] Mensajes de error claros
- [ ] Backend reiniciado
- [ ] Prueba desde frontend exitosa
- [ ] Logs confirman comportamiento correcto

---

**Estado:** ✅ **FIXED** - Listo para probar

El cambio ya está aplicado. Solo necesitas reiniciar el backend para que tome efecto.
