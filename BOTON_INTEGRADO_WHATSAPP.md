# 💬 Botón de Enviar Integrado (Estilo WhatsApp)

## Cambios Realizados

### Layout Reorganizado

**Antes:**
```
┌────────────────────────────────────────┐
│ [  Textarea de 2 columnas         ]   │
├────────────────────────────────────────┤
│ [Select] [Botón Enviar]                │
└────────────────────────────────────────┘
```

**Después (estilo WhatsApp):**
```
┌────────────────────────────────────────┐
│ [Select] [Textarea con botón dentro 🚀]│
└────────────────────────────────────────┘
```

---

## Detalles Técnicos

### 1. **Layout Horizontal**
```jsx
<div className="flex gap-2">
  {/* Select fijo (192px) */}
  <div className="w-48 shrink-0">
    <SourcesSelect />
  </div>
  
  {/* Input flexible */}
  <div className="flex-1 relative">
    <textarea />
    <button /> {/* Botón absoluto dentro */}
  </div>
</div>
```

### 2. **Textarea con Espacio para Botón**
```jsx
<textarea
  className="... pr-12" {/* Padding-right para el botón */}
  rows={1}
/>
```

### 3. **Botón Flotante (Posicionamiento Absoluto)**
```jsx
<button
  className="absolute right-2 top-1/2 -translate-y-1/2"
  disabled={loading || !question.trim()}
>
  <SendHorizonal />
</button>
```

**Posicionamiento:**
- `absolute` → Posicionado respecto al contenedor padre (relative)
- `right-2` → 8px desde el borde derecho
- `top-1/2` → Centro vertical
- `-translate-y-1/2` → Ajuste para centrado perfecto

---

## Características del Botón

### ✅ **Estados del Botón**

1. **Normal (Activo)**
   - Fondo: `bg-brand-600`
   - Hover: `hover:bg-brand-700`
   - Cursor: Normal

2. **Disabled (Inactivo)**
   - Cuando: `loading` o `question` vacío
   - Opacidad: `opacity-40`
   - Cursor: `cursor-not-allowed`

3. **Loading (Cargando)**
   - Muestra `<Spinner />` en lugar del icono
   - Disabled automáticamente

### ✅ **Comportamiento**

```typescript
disabled={loading || !question.trim()}
```

El botón se deshabilita cuando:
- ✅ Está cargando (`loading === true`)
- ✅ La pregunta está vacía o solo tiene espacios

### ✅ **Accesibilidad**

- `title="Enviar (Ctrl/⌘ + Enter)"` → Tooltip informativo
- `disabled` attribute → Screen readers detectan estado
- `transition-all` → Animación suave en cambios de estado

---

## Comparación Visual

### Antes:
```
┌──────────────────────────────────────────────┐
│                                              │
│  Pregunta:                                   │
│  ┌────────────────────────┐                 │
│  │ ¿Qué información...    │                 │
│  └────────────────────────┘                 │
│  Ctrl + Enter para enviar                   │
│                                              │
│  [Select docs] [Botón Preguntar]            │
│                                              │
└──────────────────────────────────────────────┘
```

### Después (estilo WhatsApp):
```
┌──────────────────────────────────────────────┐
│                                              │
│  [Select docs 📚] [Escribe tu pregunta... 🚀]│
│                                              │
└──────────────────────────────────────────────┘
```

---

## Ventajas

### 1. **Compacto** 📦
- Una sola línea horizontal
- ~30px menos de altura
- Más espacio para mensajes

### 2. **Intuitivo** 💡
- Diseño familiar (WhatsApp, Telegram, iMessage)
- Botón siempre visible en la misma posición
- Feedback visual (disabled cuando vacío)

### 3. **Eficiente** ⚡
- Menos movimiento del mouse
- Botón cerca del cursor (después de escribir)
- Icono solo (más rápido de identificar)

### 4. **Responsive** 📱
- Funciona bien en pantallas pequeñas
- Select tiene ancho fijo, textarea se adapta
- En móviles: Select puede moverse arriba si es necesario

---

## Clases CSS Importantes

```css
/* Textarea */
pr-12          /* Padding-right: 48px (espacio para botón) */
resize-none    /* No permitir resize manual */
rounded-xl     /* Bordes redondeados */

/* Botón */
absolute       /* Posicionamiento absoluto */
right-2        /* 8px desde la derecha */
top-1/2        /* Centro vertical */
-translate-y-1/2  /* Ajuste de centrado */
p-2            /* Padding interno del botón */
rounded-lg     /* Botón redondeado */
```

---

## Mejoras Adicionales Posibles

### 1. **Auto-grow Textarea**
```tsx
const [rows, setRows] = useState(1)

const handleChange = (e) => {
  setQuestion(e.target.value)
  // Ajustar altura según contenido
  const lineCount = e.target.value.split('\n').length
  setRows(Math.min(lineCount, 4)) // Máximo 4 líneas
}

<textarea rows={rows} />
```

### 2. **Animación del Botón**
```tsx
// Rotar el icono al enviar
<SendHorizonal 
  className={`h-4 w-4 transition-transform ${
    loading ? 'rotate-45' : ''
  }`}
/>
```

### 3. **Contador de Caracteres**
```tsx
<div className="absolute bottom-1 right-14 text-xs text-gray-400">
  {question.length}/500
</div>
```

### 4. **Emoji Picker**
```tsx
<button className="absolute right-14 top-1/2 -translate-y-1/2">
  😊
</button>
```

---

## Estructura Final

```
Input Area
├── Select de documentos (w-48, fijo)
└── Container del textarea (flex-1, relative)
    ├── Textarea (pr-12 para espacio)
    └── Botón (absolute, flotante) 🚀
```

---

## Resultado

Ahora el input tiene un diseño moderno y compacto, idéntico a aplicaciones de mensajería populares. El botón está siempre visible, se deshabilita inteligentemente cuando no hay texto, y usa menos espacio vertical.

**Recarga el frontend (F5)** para verlo en acción! 💬✨
