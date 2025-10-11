# 🧪 Testing de Nuevas Features

## Guía de Pruebas Completa

---

## ⚙️ Preparación

### 1. Iniciar Backend
```bash
cd backend
python run_dev.py
```

Verificar que esté corriendo:
```bash
curl http://localhost:8000/health
```

### 2. Iniciar Frontend
```bash
cd frontend
npm run dev
```

Abrir: http://localhost:5173

---

## ✅ Checklist de Tests

### 🔧 **Backend Tests**

#### Test 1: Búsqueda en TODO el corpus
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué documentos hablan de facturas?",
    "source": null,
    "search_mode": "multi"
  }'
```

**Esperado:**
- ✅ Responde con chunks de MÚLTIPLES documentos
- ✅ `search_mode_used: "multi"`
- ✅ `citations` con diferentes `source` values

#### Test 2: Temperatura auto-detectada
```bash
# Pregunta factual (debería usar temp=0.0)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es el RUC de la factura?",
    "source": "factura.pdf"
  }'
```

**Esperado:**
- ✅ `temperature_used: 0.0` (o muy cercano)

```bash
# Pregunta analítica (debería usar temp=0.3)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Resume el contenido principal",
    "source": "factura.pdf"
  }'
```

**Esperado:**
- ✅ `temperature_used: 0.3` (balanceado)

```bash
# Pregunta creativa (debería usar temp=0.7)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Sugiere mejoras para este documento",
    "source": "factura.pdf"
  }'
```

**Esperado:**
- ✅ `temperature_used: 0.7` (creativo)

#### Test 3: Temperatura manual (override)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es el RUC?",
    "source": "factura.pdf",
    "temperature": 0.8
  }'
```

**Esperado:**
- ✅ `temperature_used: 0.8` (respeta el override)

#### Test 4: Streaming SSE
```bash
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Hola, ¿cómo estás?",
    "source": "factura.pdf"
  }' \
  --no-buffer
```

**Esperado:**
```
event: metadata
data: {"cached": false, "search_mode_used": "single", "temperature_used": 0.0}

event: token
data: {"token": "Hola", "done": false}

event: token
data: {"token": ",", "done": false}

...

event: citations
data: [{"id": 0, "score": 0.95, ...}]

event: done
data: {"done": true}
```

#### Test 5: Caché
```bash
# Primera llamada (miss)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test de caché",
    "source": "factura.pdf"
  }'

# Segunda llamada IDÉNTICA (hit)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test de caché",
    "source": "factura.pdf"
  }'
```

**Esperado:**
- 1ra: `cached: false`
- 2da: `cached: true` (mucho más rápido)

#### Test 6: Endpoints de estadísticas
```bash
# Stats
curl http://localhost:8000/stats

# Cache stats
curl http://localhost:8000/cache/stats

# Documents
curl http://localhost:8000/documents

# Sources
curl http://localhost:8000/sources
```

**Esperado:**
- ✅ Todos responden 200 OK con JSON válido

---

### 🎨 **Frontend Tests**

#### Test 7: Historial conversacional
1. Abre http://localhost:5173
2. Haz 3 preguntas diferentes
3. Verifica:
   - ✅ Los mensajes se quedan en pantalla
   - ✅ Usuario a la derecha (azul)
   - ✅ Asistente a la izquierda (blanco)
   - ✅ Timestamps visibles
   - ✅ Auto-scroll al último mensaje

#### Test 8: Exportar chat
1. Haz al menos 2 preguntas
2. Clic en botón ⬇️ (Download)
3. Verifica:
   - ✅ Se descarga archivo `.md`
   - ✅ Contiene todo el historial
   - ✅ Formato Markdown válido
   - ✅ Incluye citas/fuentes

#### Test 9: Limpiar historial
1. Haz algunas preguntas
2. Clic en botón 🗑️ (Trash)
3. Confirma
4. Verifica:
   - ✅ Historial vacío
   - ✅ Toast de confirmación

#### Test 10: Markdown rendering
1. Haz pregunta que genere respuesta con formato:
   ```
   "Explica el contenido usando listas y negrita"
   ```
2. Verifica:
   - ✅ **Negrita** se ve en negrita
   - ✅ Listas numeradas/no numeradas formateadas
   - ✅ `Código` con fondo gris
   - ✅ No se ven símbolos Markdown crudos

#### Test 11: SystemStatus badge
1. Mira el header (arriba derecha)
2. Verifica:
   - ✅ Badge visible con color
   - ✅ 🟢 **Operativo** si todo OK
   - ✅ Iconos: Cpu, Database, Activity
   - ✅ Números de chunks (formato: 1.2k)
   - ✅ Se actualiza cada minuto

#### Test 12: Dashboard - Tab Stats
1. Clic en "Ajustes"
2. Tab "📊 Estadísticas"
3. Verifica:
   - ✅ Documentos totales
   - ✅ Chunks indexados
   - ✅ Tamaño promedio
   - ✅ Dimensión embeddings
   - ✅ Modelo mostrado
   - ✅ Botón "Actualizar" funciona

#### Test 13: Dashboard - Tab Caché
1. Clic en "Ajustes" → "💾 Caché"
2. Verifica:
   - ✅ Entradas actuales / máximo
   - ✅ Tasa de aciertos (%)
   - ✅ Total hits / misses
   - ✅ Barra de progreso visual
   - ✅ Botón "Limpiar Caché" funciona
   - ✅ Mensaje de confirmación

#### Test 14: Dashboard - Tab Documentos
1. Clic en "Ajustes" → "📚 Documentos"
2. Verifica:
   - ✅ Lista de todos los docs
   - ✅ Para cada doc:
     - Nombre completo
     - 🧩 Cantidad de chunks
     - 📝 Total de caracteres
     - 📄 Badge si es PDF

#### Test 15: Selector de docs mejorado
1. Abre selector de documentos
2. Verifica:
   - ✅ Opción "📚 Buscar en todos los documentos"
   - ✅ Cada doc muestra: `📄 nombre (X chunks, Yk chars)`
   
3. Selecciona un documento
4. Verifica:
   - ✅ Aparece card azul con info del doc
   - ✅ Muestra chunks, caracteres, tipo

5. Selecciona "Todos los documentos"
6. Verifica:
   - ✅ Aparece card morado
   - ✅ Dice "Modo búsqueda global"
   - ✅ Muestra total de docs y chunks

#### Test 16: Búsqueda global (frontend)
1. Selector: "📚 Buscar en todos los documentos"
2. Pregunta: "¿Qué dicen todos los documentos sobre X?"
3. Haz la pregunta
4. Verifica:
   - ✅ Respuesta incluye múltiples fuentes
   - ✅ Citas de diferentes documentos
   - ✅ Metadata muestra: `📚 Multi-doc`

#### Test 17: Metadata visible
1. Haz una pregunta
2. En la respuesta del asistente, verifica:
   - ✅ Modo: `📄 Un doc` o `📚 Multi-doc`
   - ✅ Temperatura: `Factual` / `Balanceado` / `Creativo`
   - ✅ Si vino del caché: ⚡ Icono de rayo

#### Test 18: Salto a página
1. Haz pregunta sobre PDF
2. Respuesta tendrá citas con páginas
3. Clic en una cita
4. Verifica:
   - ✅ Panel izquierdo cambia al documento
   - ✅ Salta a la página correcta
   - ✅ Texto se resalta (amarillo)

---

## 🐛 Tests de Edge Cases

### Edge 1: Sin documentos indexados
1. Backend recién iniciado (sin docs)
2. Intenta hacer pregunta
3. Verifica:
   - ✅ Error claro: "No hay índice"
   - ✅ No crashea

### Edge 2: Pregunta muy larga
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "'"$(python -c 'print("a" * 1000)')"'",
    "source": "doc.pdf"
  }'
```

**Esperado:**
- ✅ Error 422: "max_length 500"

### Edge 3: Temperatura inválida
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test",
    "source": "doc.pdf",
    "temperature": 5.0
  }'
```

**Esperado:**
- ✅ Error 422: "temperature must be <= 2.0"

### Edge 4: Source con path traversal
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test",
    "source": "../../../etc/passwd"
  }'
```

**Esperado:**
- ✅ Error 422: "Nombre de archivo inválido"

### Edge 5: Caché lleno
1. Haz 100+ preguntas diferentes (llenar caché)
2. Verifica:
   - ✅ LRU eviction funciona
   - ✅ No crashea
   - ✅ Cache size <= max_size

---

## 📊 Performance Tests

### Perf 1: Latencia sin caché
```bash
time curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test único '"$(date +%s)"'",
    "source": "doc.pdf"
  }'
```

**Benchmark típico:**
- 📄 Documento pequeño: 2-5s
- 📚 Corpus grande: 5-10s

### Perf 2: Latencia con caché
```bash
# Primera llamada
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Test", "source":"doc.pdf"}'

# Segunda llamada (con time)
time curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Test", "source":"doc.pdf"}'
```

**Esperado:**
- ✅ 2da llamada <100ms (caché hit)
- ✅ cached: true en respuesta

### Perf 3: Streaming vs Normal
```bash
# Normal
time curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hola", "source":"doc.pdf"}'

# Streaming (tiempo al primer token)
time curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Hola", "source":"doc.pdf"}' \
  --no-buffer | head -n 5
```

**Esperado:**
- ✅ Streaming primer token más rápido
- ✅ Mejor percepción de velocidad

---

## ✅ Checklist Final

Antes de considerar las features completas, verifica:

### Backend
- [ ] `/ask` con `source=null` funciona
- [ ] Temperatura auto-detecta correctamente
- [ ] Temperatura manual override funciona
- [ ] `/ask/stream` devuelve SSE válidos
- [ ] Caché funciona (hit/miss)
- [ ] Endpoints de stats responden

### Frontend
- [ ] Historial conversacional funciona
- [ ] Exportar chat a MD funciona
- [ ] Limpiar historial funciona
- [ ] Markdown rendering correcto
- [ ] SystemStatus badge visible y actualiza
- [ ] Dashboard con 4 tabs completos
- [ ] Selector enriquecido con info
- [ ] Búsqueda global UI funciona
- [ ] Metadata visible en mensajes
- [ ] Salto a página funciona

### Integración
- [ ] Frontend + Backend comunicación OK
- [ ] Caché funciona end-to-end
- [ ] Búsqueda multi-doc funciona completa
- [ ] No hay errores en consola
- [ ] No hay errores en logs backend

---

## 🎉 ¡Listo!

Si todos los tests pasan, tu sistema está **production-ready** con las 8 nuevas features funcionando perfectamente.

**Próximo paso**: Deploy o integración con CI/CD

---

*Testing Guide - Octubre 2025*
