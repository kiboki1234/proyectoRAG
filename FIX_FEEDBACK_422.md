# 🔧 Fix Aplicado - Error 422 en Feedback

## Problema Identificado

En los logs del backend vi:
```
INFO: 127.0.0.1:61897 - "POST /feedback HTTP/1.1" 422 Unprocessable Entity
```

## Causa

El endpoint `/feedback` en el backend esperaba parámetros como query parameters:
```python
async def submit_feedback(
    message_id: str,  # ← FastAPI busca esto como ?message_id=...
    feedback: str,    # ← FastAPI busca esto como ?feedback=...
    ...
)
```

Pero el frontend enviaba un JSON body:
```json
{
  "message_id": "xxx",
  "feedback": "positive"
}
```

## Solución Aplicada

### 1. Creado modelo Pydantic en `backend/models.py`
```python
class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str  # 'positive' o 'negative'
    question: Optional[str] = None
    answer: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ['positive', 'negative']:
            raise ValueError("feedback debe ser 'positive' o 'negative'")
        return v
```

### 2. Actualizado endpoint en `backend/app.py`
```python
@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):  # ← Ahora acepta JSON
    feedback_manager.save_feedback(
        request.message_id,
        request.feedback,
        request.question,
        request.answer,
        request.metadata
    )
    return {
        "status": "ok",
        "message_id": request.message_id,
        "feedback": request.feedback
    }
```

### 3. Añadido import en `backend/app.py`
```python
from models import (
    ...,
    FeedbackRequest  # ← Nuevo
)
```

## Resultado

Ahora el endpoint `/feedback` acepta correctamente el JSON body que envía el frontend.

---

## ⚠️ Problema Principal Pendiente

El error 422 era **secundario**. El problema principal sigue siendo:

**NO se están generando respuestas del asistente**

### Síntomas:
- Las conversaciones se guardan cada 5s ✅
- Pero NO aparece ninguna llamada a `/ask/stream` en logs ❌
- La respuesta nunca se genera ❌

### Próximos pasos de debugging:

1. **Recarga el frontend** (el backend ya está actualizado)
2. **Abre DevTools** (F12) → Tab **Console**
3. **Haz una pregunta**
4. **Copia TODOS los logs** que aparezcan en la consola

Los logs mostrarán:
```
[ChatPanel] submit called { question: "...", source: ..., useStreaming: true }
[ChatPanel] Using streaming mode
[ChatPanel] Calling askStreaming...
[askStreaming] Starting request { url: "...", question: "...", source: ... }
```

Si NO ves esos logs, significa que hay un problema antes de llegar a `askStreaming()`.

---

## Test Rápido

Si quieres probar si el problema es el streaming, prueba:

### Opción 1: Desactivar streaming en la UI
Haz clic en el botón "**Stream**" (⚡) en el header del chat para cambiarlo a "**Normal**".

### Opción 2: Probar el endpoint manualmente
Abre una terminal y ejecuta:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hola"}'
```

Si esto funciona, el problema es específico del streaming en el frontend.

---

**Próxima acción:** Necesito ver los logs de la consola del navegador para diagnosticar el problema principal.
