# 🎯 Quick Start - Nuevas Features

## ✨ ¿Qué cambió?

Tu sistema RAG pasó de **MVP** a **production-ready**. Aquí las 8 mejoras críticas implementadas:

---

## 🔧 Backend (3 mejoras)

### 1. **Búsqueda Multi-Documento** 
```python
# Antes: Solo 1 documento
ask(question="...", source="doc1.pdf")

# Ahora: TODO el corpus o 1 doc
ask(question="...", source=None)  # Busca en TODOS con balanceo
ask(question="...", source="doc1.pdf")  # Solo ese doc
```

### 2. **Temperatura Inteligente**
```python
# Auto-detecta según tipo de pregunta:
"¿Cuál es el RUC?" → temp=0.0 (factual)
"Resume el contrato" → temp=0.3 (balanceado)  
"Sugiere ideas" → temp=0.7 (creativo)

# O manual:
ask(question="...", temperature=0.5)
```

### 3. **Streaming (SSE)**
```python
# Nuevo endpoint
POST /ask/stream
# Responde token por token (tipo ChatGPT)
```

---

## 🎨 Frontend (5 mejoras)

### 4. **Chat con Historial**
- ✅ Mensajes persistentes (usuario + asistente)
- ✅ Export a Markdown
- ✅ Limpiar historial

### 5. **Markdown Rendering**
- ✅ Listas, **negrita**, `código`
- ✅ Tablas, bloques de código
- ✅ Enlaces

### 6. **SystemStatus Badge**
- 🟢 **Operativo** / 🟡 **Degradado** / 🔴 **Error**
- ✅ LLM, Índice, Chunks
- En el header, siempre visible

### 7. **Dashboard Completo**
- **📊 Stats**: Docs, chunks, modelo
- **💾 Caché**: Hit rate, limpiar caché
- **📚 Docs**: Lista con info detallada

### 8. **Selector Mejorado**
```
📚 Buscar en todos los documentos
📄 doc1.pdf (50 chunks, 12.5k chars)
📄 doc2.pdf (120 chunks, 30k chars)
```
Con info contextual según selección

---

## 🚀 Cómo usar

### Backend
```bash
cd backend
# Asegúrate de tener las dependencias
pip install -r requirements.txt

# Inicia el servidor
python run_dev.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Probar las nuevas features

1. **Búsqueda global**: 
   - Selector: "📚 Buscar en todos los documentos"
   - Pregunta: "¿Qué dicen todos los docs sobre X?"

2. **Temperatura auto**:
   - Pregunta factual: "¿Cuál es el RUC?"
   - Pregunta analítica: "Resume el contrato"

3. **Historial**:
   - Haz varias preguntas
   - Exporta con botón ⬇️

4. **Dashboard**:
   - Clic en "Ajustes"
   - Tabs: Stats, Caché, Documentos

5. **System Status**:
   - Mira el badge en header (arriba derecha)

---

## 📝 Endpoints nuevos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/ask` | POST | Ahora soporta `source=None`, `temperature`, `search_mode` |
| `/ask/stream` | POST | **NUEVO** - Streaming SSE |
| `/health` | GET | Ya existía |
| `/stats` | GET | Ya existía |
| `/cache/stats` | GET | Ya existía |
| `/documents` | GET | Ya existía |

---

## 🎯 Testing rápido

### Test 1: Búsqueda global
```json
POST /ask
{
  "question": "¿Qué documentos hablan de facturas?",
  "source": null,
  "search_mode": "multi"
}
```

### Test 2: Temperatura manual
```json
POST /ask
{
  "question": "Dame un resumen creativo",
  "source": "doc1.pdf",
  "temperature": 0.7
}
```

### Test 3: Streaming
```bash
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Hola", "source":"doc1.pdf"}' \
  --no-buffer
```

---

## ⚠️ Notas importantes

1. **Compatibilidad hacia atrás**: Todo lo viejo sigue funcionando
2. **Caché**: Respuestas se cachean automáticamente
3. **Performance**: Streaming mejora percepción de velocidad
4. **Modelos**: Temperatura se auto-ajusta, pero puedes override

---

## 🐛 Troubleshooting

### Backend no inicia
```bash
# Verifica dependencias
pip list | grep fastapi

# Reinstala si falta algo
pip install -r requirements.txt --upgrade
```

### Frontend no compila
```bash
# Limpia y reinstala
rm -rf node_modules package-lock.json
npm install
```

### No se ven las estadísticas
```bash
# Verifica que el backend esté corriendo
curl http://localhost:8000/health
```

---

## 📚 Documentación completa

Ver: `MEJORAS_CRITICAS_2025.md` para detalles técnicos completos.

---

*Quick start guide - Octubre 2025*
