# 🐛 Debugging - Problema de Respuestas

## Problema Reportado
- Las conversaciones se guardan cada 5s (se ve en logs)
- Pero NO se genera ninguna respuesta del asistente
- NO aparece ninguna llamada a `/ask` o `/ask/stream` en logs del backend

## Diagnóstico

### Logs del Backend (Actual)
```
✅ POST /conversations/... (cada 5s) - Auto-guardado funciona
❌ POST /ask/stream - NO APARECE
❌ POST /ask - NO APARECE
```

Esto indica que **el frontend NO está enviando la pregunta al backend**.

### Posibles Causas

1. **El botón "Preguntar" no está llamando a `submit()`**
2. **La función `askStreaming()` está fallando silenciosamente**
3. **Hay un error de red que no se está mostrando**
4. **El modo streaming está roto y no hay fallback**

## Solución Aplicada

He añadido logs de depuración en:

### 1. `ChatPanel.tsx` - Función `submit()`
```typescript
console.log('[ChatPanel] submit called', { question, source, useStreaming })
console.log('[ChatPanel] Using streaming mode')
console.log('[ChatPanel] Calling askStreaming...')
```

### 2. `api.ts` - Función `askStreaming()`
```typescript
console.log('[askStreaming] Starting request', { url, question, source })
console.log('[askStreaming] Request body:', body)
console.log('[askStreaming] Response received', { ok, status })
console.log('[askStreaming] Token received:', token)
console.log('[askStreaming] Done event received')
```

### 3. Manejo de errores mejorado
```typescript
try {
  await askStreaming(...)
} catch (streamError) {
  console.error('Streaming error:', streamError)
  setLoading(false)
  throw streamError // Re-throw para que el catch exterior lo capture
}
```

## Pasos para Debuggear

### 1. Abre DevTools del Navegador
- Presiona **F12**
- Ve a la tab **Console**

### 2. Recarga la Página
- Presiona **F5** o Ctrl+R

### 3. Haz una Pregunta
- Escribe cualquier pregunta
- Haz clic en "Preguntar" (o Ctrl+Enter)

### 4. Observa los Logs

Deberías ver algo como:

#### ✅ **Si funciona correctamente:**
```
[ChatPanel] submit called { question: "...", source: undefined, useStreaming: true }
[ChatPanel] Using streaming mode
[ChatPanel] Calling askStreaming...
[askStreaming] Starting request { url: "http://localhost:8000/ask/stream", question: "...", source: undefined }
[askStreaming] Request body: { question: "..." }
[askStreaming] Response received { ok: true, status: 200 }
[askStreaming] Starting to read stream...
[askStreaming] Token received: "La"
[askStreaming] Token received: " respuesta"
[askStreaming] Token received: " es..."
[askStreaming] Citations received: 3
[askStreaming] Metadata received: { cached: false, ... }
[askStreaming] Done event received
```

#### ❌ **Si NO funciona:**

**Caso A: No se llama a submit()**
```
(No hay logs en absoluto)
```
→ **Solución:** El botón no está conectado correctamente

**Caso B: Error de red**
```
[ChatPanel] submit called { ... }
[ChatPanel] Using streaming mode
[ChatPanel] Calling askStreaming...
[askStreaming] Starting request { ... }
[askStreaming] Response received { ok: false, status: 404 }
Error: Stream failed: ...
```
→ **Solución:** El endpoint no existe o la URL es incorrecta

**Caso C: Error en el parsing**
```
[ChatPanel] submit called { ... }
[askStreaming] Starting request { ... }
[askStreaming] Response received { ok: true, status: 200 }
[askStreaming] Starting to read stream...
(No hay más logs)
```
→ **Solución:** El formato del stream no se está parseando correctamente

**Caso D: Backend lento o colgado**
```
[ChatPanel] submit called { ... }
[askStreaming] Starting request { ... }
(Espera infinita, no hay respuesta)
```
→ **Solución:** El backend está tardando demasiado o se colgó

## Verificación Adicional

### 1. Tab Network en DevTools
- Ve a **Network** tab
- Haz una pregunta
- Busca el request a `/ask/stream`
- Verifica:
  - ✅ Status: 200 OK
  - ✅ Type: eventsource o application/octet-stream
  - ✅ Response: Ver el contenido SSE

### 2. Verificar que el endpoint existe
Abre en el navegador:
```
http://localhost:8000/docs
```
Busca `/ask/stream` en la lista de endpoints.

### 3. Test manual del endpoint
Ejecuta en terminal:
```bash
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Hola"}'
```

Deberías ver algo como:
```
event: token
data: {"token": "Hola"}

event: token
data: {"token": ", "}

event: done
data: {"done": true}
```

## Soluciones Rápidas

### Si el problema es el modo streaming:

**Opción 1: Desactivar streaming temporalmente**
En `ChatPanel.tsx`, cambia la línea 33:
```typescript
const [useStreaming, setUseStreaming] = useState(false) // ← cambiar a false
```

**Opción 2: Usar el toggle**
Haz clic en el botón "Stream" para cambiar a modo "Normal".

### Si el backend está lento:

**Verificar logs del backend:**
```
INFO: Received question: ...
INFO: Retrieved X chunks
INFO: Generating response...
```

Si ves que se queda en "Generating response..." por mucho tiempo:
- El modelo LLM está tardando mucho
- Falta VRAM o CPU
- El modelo no está cargado correctamente

## Rollback Temporal

Si todo falla, puedes revertir al código anterior que funcionaba:

```bash
git log --oneline -10
git checkout <commit-hash-anterior>
```

## Contacto con Logs

Cuando me respondas, incluye:
1. **Logs de la consola del navegador** (todo lo que veas en Console)
2. **Logs del backend** (lo que aparece en la terminal del backend)
3. **Screenshot del Network tab** (mostrando el request a /ask/stream)
4. **¿Ves algún toast de error?** (mensaje rojo en la esquina)

Con esa información podré diagnosticar exactamente qué está pasando.

---

**Actualizado:** 2024-01-20
**Estado:** Logs de depuración añadidos, esperando feedback del usuario
