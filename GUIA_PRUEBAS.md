# 🧪 Guía de Pruebas - Nuevas Funcionalidades

Esta guía te ayudará a verificar que todas las 5 mejoras implementadas funcionan correctamente.

---

## 🚀 Preparación

### 1. Arrancar el Backend
```bash
cd backend
python run_dev.py
```

### 2. Arrancar el Frontend
```bash
cd frontend
npm run dev
```

### 3. Abrir en el Navegador
```
http://localhost:5173
```

---

## ✅ Tests de Funcionalidad

### 1. 🗂️ Persistencia de Historial

**Objetivo:** Verificar que las conversaciones se guardan y persisten entre sesiones.

#### Test 1.1: Auto-guardado
1. Haz una pregunta cualquiera en el chat
2. Espera 5 segundos (auto-save)
3. Abre las DevTools del navegador → Application → Local Storage
4. Busca la key que empieza con `conversation_`
5. ✅ **Esperado:** Ver JSON con tu mensaje

#### Test 1.2: Persistencia al refrescar
1. Haz 2-3 preguntas
2. Espera 5 segundos
3. Refresca la página (F5)
4. ✅ **Esperado:** El historial se recarga automáticamente
5. ✅ **Esperado:** Ver toast "Conversación anterior recuperada"

#### Test 1.3: Exportar a Markdown
1. Después de varias preguntas
2. Haz clic en el botón de descarga (📥) en el header del chat
3. ✅ **Esperado:** Se descarga un archivo `.md`
4. Abre el archivo
5. ✅ **Esperado:** Ver conversación en formato Markdown legible

#### Test 1.4: Limpiar historial
1. Haz clic en el botón rojo con icono de basura
2. Confirma la acción
3. ✅ **Esperado:** Chat se limpia
4. ✅ **Esperado:** Ver mensaje "No hay mensajes aún"

---

### 2. 🛡️ Manejo de Errores Robusto

**Objetivo:** Verificar que los errores se manejan elegantemente.

#### Test 2.1: Backend apagado
1. Detén el backend (Ctrl+C en terminal)
2. Intenta hacer una pregunta en el frontend
3. ✅ **Esperado:** Ver toast de error con mensaje claro
4. ✅ **Esperado:** NO ver pantalla blanca
5. Vuelve a arrancar el backend

#### Test 2.2: Consulta inválida (opcional)
1. Abre DevTools → Console
2. Ejecuta:
```js
fetch('http://localhost:8000/ask', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({}) // payload vacío inválido
}).then(r => r.json()).then(console.log)
```
3. ✅ **Esperado:** Ver respuesta con estructura:
```json
{
  "code": "validation_error",
  "message": "...",
  "timestamp": "..."
}
```

#### Test 2.3: Error Boundary (test manual)
1. Si quieres probar el ErrorBoundary, temporalmente añade un error en un componente
2. Ejemplo: en `App.tsx` añade `throw new Error("Test")` dentro del return
3. ✅ **Esperado:** Ver pantalla de error con mensaje amigable
4. ✅ **Esperado:** Botones "Recargar" y "Reintentar"
5. Revierte el cambio después

---

### 3. ⚡ Streaming Token-by-Token

**Objetivo:** Verificar que el streaming funciona en tiempo real.

#### Test 3.1: Modo streaming activado (default)
1. Asegúrate de que el botón diga "Stream" (con icono ⚡)
2. Haz una pregunta larga (ej: "Explica en detalle qué es RAG")
3. ✅ **Esperado:** Ver tokens aparecer uno por uno en tiempo real
4. ✅ **Esperado:** Respuesta se construye gradualmente como ChatGPT

#### Test 3.2: Modo normal
1. Haz clic en el botón "Stream" para cambiar a "Normal"
2. Haz la misma pregunta
3. ✅ **Esperado:** Spinner de carga
4. ✅ **Esperado:** Respuesta aparece completa de golpe (no streaming)

#### Test 3.3: Velocidad percibida
1. Pon el botón en "Stream"
2. Haz una pregunta
3. ✅ **Esperado:** Ver primeras palabras en <1 segundo
4. Pon el botón en "Normal"
5. Haz la misma pregunta
6. ✅ **Esperado:** Esperar varios segundos antes de ver algo

---

### 4. 👍👎 Sistema de Feedback

**Objetivo:** Verificar que el feedback se guarda correctamente.

#### Test 4.1: Dar feedback positivo
1. Haz una pregunta
2. En el mensaje del asistente, haz clic en 👍
3. ✅ **Esperado:** Ver toast "Gracias por tu feedback positivo"
4. ✅ **Esperado:** Icono 👍 se pone verde
5. ✅ **Esperado:** Ambos botones se deshabilitan

#### Test 4.2: Dar feedback negativo
1. Haz otra pregunta
2. Haz clic en 👎
3. ✅ **Esperado:** Ver toast "Gracias por tu feedback"
4. ✅ **Esperado:** Icono 👎 se pone rojo
5. ✅ **Esperado:** Ambos botones se deshabilitan

#### Test 4.3: Verificar almacenamiento backend
1. Navega a `backend/data/feedback.jsonl`
2. Abre el archivo
3. ✅ **Esperado:** Ver líneas JSON con:
```json
{
  "conversation_id": "...",
  "message_id": "...",
  "rating": "positive" o "negative",
  "timestamp": "..."
}
```

#### Test 4.4: Estadísticas de feedback (API)
1. Abre http://localhost:8000/feedback/stats en el navegador
2. ✅ **Esperado:** Ver JSON con:
```json
{
  "total": 2,
  "positive": 1,
  "negative": 1,
  "satisfaction_rate": 0.5
}
```

---

### 5. 🌙 Modo Oscuro

**Objetivo:** Verificar que el tema cambia correctamente.

#### Test 5.1: Cambiar a modo oscuro
1. Busca el icono ☀️ en el header (al lado de "Ajustes")
2. Haz clic
3. Selecciona "🌙 Oscuro"
4. ✅ **Esperado:** Toda la UI cambia a colores oscuros inmediatamente
5. ✅ **Esperado:** Fondo negro/gris oscuro, texto claro

#### Test 5.2: Cambiar a modo claro
1. Haz clic en el icono (ahora debería ser 🌙)
2. Selecciona "☀️ Claro"
3. ✅ **Esperado:** UI vuelve a colores claros

#### Test 5.3: Modo sistema
1. Haz clic en el icono
2. Selecciona "🖥️ Sistema"
3. ✅ **Esperado:** UI sigue la preferencia del sistema operativo
4. Cambia la preferencia del sistema (Settings → Appearance → Dark/Light)
5. ✅ **Esperado:** UI cambia automáticamente

#### Test 5.4: Persistencia del tema
1. Selecciona "🌙 Oscuro"
2. Refresca la página (F5)
3. ✅ **Esperado:** Página carga en modo oscuro
4. Abre DevTools → Application → Local Storage
5. ✅ **Esperado:** Ver key `theme` con valor `"dark"`

#### Test 5.5: Componentes con dark mode
Verifica que estos componentes se ven bien en modo oscuro:
- ✅ Header (fondo oscuro, texto claro)
- ✅ Chat panel (mensajes con colores oscuros)
- ✅ Upload zone (fondo oscuro)
- ✅ Document preview (bordes oscuros)
- ✅ Settings modal (fondo oscuro, tabs oscuros)
- ✅ Botones y inputs (bordes y fondos oscuros)

---

## 🔍 Tests de Integración

### Test Integrado 1: Flujo completo con persistencia + streaming + feedback
1. Refresca la página (nueva conversación)
2. Activa modo streaming
3. Haz una pregunta larga
4. Observa el streaming en tiempo real
5. Da feedback 👍 o 👎
6. Espera 5 segundos (auto-save)
7. Refresca la página
8. ✅ **Esperado:** Conversación se recarga con el feedback visible

### Test Integrado 2: Dark mode persistente con todas las funcionalidades
1. Cambia a modo oscuro
2. Haz varias preguntas con streaming
3. Da feedback
4. Exporta el chat
5. Abre configuración
6. Refresca la página
7. ✅ **Esperado:** Todo funciona y persiste en modo oscuro

---

## 🐛 Tests de Edge Cases

### Edge Case 1: Backend cae durante streaming
1. Inicia una pregunta con streaming
2. **Mientras está streaming**, detén el backend (Ctrl+C)
3. ✅ **Esperado:** Streaming se detiene, error se muestra con toast
4. ✅ **Esperado:** No crash, UI sigue funcional

### Edge Case 2: Múltiples tabs con misma conversación
1. Abre 2 tabs con la app
2. En tab 1: haz una pregunta
3. En tab 2: refresca
4. ✅ **Esperado:** Tab 2 carga la conversación actualizada

### Edge Case 3: localStorage lleno (simulado)
1. Abre DevTools → Console
2. Ejecuta:
```js
localStorage.setItem('test_fill', 'x'.repeat(5 * 1024 * 1024))
```
3. Haz preguntas
4. ✅ **Esperado:** Si localStorage falla, backend sync continúa funcionando

---

## 📊 Checklist de Verificación Final

Marca cada item después de probarlo:

### Persistencia
- [ ] Auto-guardado cada 5s funciona
- [ ] Historial persiste al refrescar
- [ ] Exportar a Markdown funciona
- [ ] Limpiar historial funciona
- [ ] localStorage sincroniza con backend

### Errores
- [ ] Backend apagado muestra error amigable
- [ ] No hay pantallas blancas
- [ ] Errores estructurados en API
- [ ] ErrorBoundary captura crashes React

### Streaming
- [ ] Modo streaming muestra tokens en tiempo real
- [ ] Modo normal espera respuesta completa
- [ ] Toggle funciona correctamente
- [ ] Icono ⚡ visible en modo stream

### Feedback
- [ ] Botón 👍 guarda feedback positivo
- [ ] Botón 👎 guarda feedback negativo
- [ ] Toasts de confirmación aparecen
- [ ] Botones se deshabilitan después de feedback
- [ ] feedback.jsonl contiene entradas correctas
- [ ] API /feedback/stats funciona

### Dark Mode
- [ ] Cambio a oscuro funciona
- [ ] Cambio a claro funciona
- [ ] Modo sistema funciona
- [ ] Tema persiste al refrescar
- [ ] Todos los componentes se ven bien en oscuro
- [ ] ThemeToggle dropdown funciona
- [ ] localStorage guarda preferencia

---

## 🎉 Resultado Esperado

Si todos los tests pasan:
- ✅ **100% de funcionalidades implementadas**
- ✅ **Sistema listo para producción**
- ✅ **Experiencia de usuario premium**

---

## 🆘 Troubleshooting

### Problema: "No se guarda el historial"
- Verifica que el backend esté corriendo
- Chequea la consola del navegador por errores
- Mira `backend/data/conversations/` para ver si se crean archivos

### Problema: "Streaming no funciona"
- Verifica que el endpoint `/ask/stream` exista en backend
- Chequea que el botón diga "Stream" (no "Normal")
- Mira Network tab en DevTools para ver el stream

### Problema: "Dark mode no persiste"
- Chequea localStorage en DevTools
- Verifica que `initTheme()` se llame en `main.tsx`
- Asegura que Tailwind esté configurado con `darkMode: ['class']`

### Problema: "Feedback no se guarda"
- Verifica que `backend/data/` exista
- Chequea permisos de escritura en el directorio
- Mira logs del backend por errores

---

**Última actualización:** 2024-01-20  
**Versión:** 2.0 (con todas las mejoras)
