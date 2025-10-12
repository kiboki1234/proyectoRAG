# 🔧 FIX: Limpiar LocalStorage del Navegador

## 🚨 Problema Identificado

Los documentos siguen apareciendo porque están guardados en el **localStorage del navegador**, no vienen del backend.

### Código Responsable

```tsx
// SourcesSelect.tsx
const locals = getLocalSources()  // ← Lee de localStorage
const remote = getSources()       // ← Lee del backend

// Combina ambos
const options = [...locals, ...remote]
```

---

## ✅ Solución: Limpiar localStorage

### Opción 1: Desde la Consola del Navegador (RÁPIDO)

1. **Abre DevTools**: Presiona `F12`
2. **Ve a la pestaña "Console"**
3. **Ejecuta este comando**:
   ```javascript
   localStorage.removeItem('local_sources')
   location.reload()
   ```

### Opción 2: Desde Application/Storage

1. **Abre DevTools**: `F12`
2. **Ve a "Application"** (o "Almacenamiento" en español)
3. **Expand "Local Storage"** → `http://localhost:5173` (o tu puerto)
4. **Encuentra la clave** `local_sources`
5. **Clic derecho** → **Delete**
6. **Recarga la página** (`F5`)

### Opción 3: Limpiar Todo el localStorage

```javascript
// En consola del navegador
localStorage.clear()
location.reload()
```

⚠️ **Nota**: Esto también borrará la URL del backend si la tenías personalizada.

---

## 🎯 Verificación

Después de limpiar localStorage:

1. **Recarga la página** (F5)
2. **Abre el select de documentos**
3. **Debe mostrar**: Solo "📚 Buscar en todos los documentos" (sin documentos individuales)

---

## 🔍 ¿Por Qué Pasó Esto?

Cuando subes documentos por primera vez, el frontend los guarda en `localStorage` para:
- Recordar qué archivos has subido
- Mostrarlos aunque el backend se reinicie
- Persistencia entre sesiones

Pero cuando **borras documentos del servidor**, el `localStorage` del navegador **NO se limpia automáticamente**.

---

## 🚀 Solución Permanente (Futuro)

### Opción A: No Usar localStorage para Documentos

Eliminar la funcionalidad de `getLocalSources()` y solo usar el backend:

```tsx
// SourcesSelect.tsx
const options = useMemo(() => {
  return remote.sort()  // Solo del backend
}, [remote])
```

### Opción B: Sincronizar localStorage con Backend

Cuando el backend devuelve documentos, actualizar el localStorage:

```tsx
useEffect(() => {
  const sources = await getSources()
  setRemote(sources)
  
  // Actualizar localStorage
  localStorage.setItem('local_sources', JSON.stringify(sources))
}, [])
```

### Opción C: Botón de "Sincronizar"

Agregar un botón en el frontend para refrescar la lista:

```tsx
<button onClick={async () => {
  const sources = await getSources()
  localStorage.setItem('local_sources', JSON.stringify(sources))
  setRemote(sources)
}}>
  🔄 Actualizar lista
</button>
```

---

## 📋 Comando Rápido

Copia y pega en la consola del navegador (F12):

```javascript
localStorage.removeItem('local_sources'); location.reload();
```

---

**Próximo paso**: Abre la consola del navegador y ejecuta el comando para limpiar `local_sources` 🧹
