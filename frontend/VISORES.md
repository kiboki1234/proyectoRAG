# 📄 Visores de Documentos - Frontend

Sistema de previsualización de documentos con soporte para múltiples formatos.

## 🎯 Componentes

### `DocumentPreview.tsx` (Componente Principal)
Wrapper inteligente que detecta automáticamente el tipo de archivo y muestra el visor apropiado.

**Props:**
- `source?: string` - Nombre del archivo a mostrar
- `page?: number` - Número de página (solo para PDFs)
- `highlight?: string` - Texto a resaltar en el documento

**Uso:**
```tsx
<DocumentPreview 
  source="documento.pdf" 
  page={3} 
  highlight="texto importante"
/>
```

### `PdfPreview.tsx` (Visor PDF)
Usa PDF.js para mostrar documentos PDF con funcionalidad de búsqueda y navegación.

**Características:**
- Renderizado completo de PDFs
- Navegación por páginas
- Búsqueda y resaltado de texto
- Zoom y herramientas de anotación

### `TxtPreview.tsx` (Visor de Texto)
Visor simple para archivos de texto plano (.txt).

**Características:**
- Carga asíncrona del contenido
- Resaltado de texto buscado
- Scroll automático al texto destacado
- Formato monoespacio preservado

### `MarkdownPreview.tsx` (Visor de Markdown)
Renderiza archivos Markdown (.md) con formato completo.

**Características:**
- Renderizado con `react-markdown`
- Soporte de GitHub Flavored Markdown (tablas, listas de tareas, etc.)
- Estilos Tailwind Typography (clase `prose`)
- Resaltado de texto buscado
- Scroll automático

## 🔧 Detección de Tipos

El componente `DocumentPreview` detecta automáticamente el tipo de archivo basándose en la extensión:

| Extensión | Componente |
|-----------|------------|
| `.pdf` | `PdfPreview` |
| `.txt` | `TxtPreview` |
| `.md`, `.markdown` | `MarkdownPreview` |
| Otros | `PdfPreview` (fallback) |

## 📦 Dependencias

```json
{
  "react-markdown": "^9.x",
  "remark-gfm": "^4.x",
  "lucide-react": "^0.x"
}
```

## 🎨 Estilos

Todos los visores usan:
- Tailwind CSS para estilos base
- Altura consistente: `h-[72vh]`
- Bordes redondeados: `rounded-2xl`
- Sombras sutiles: `shadow-sm`

Para Markdown, se usa `@tailwindcss/typography`:
```tsx
<article className="prose prose-sm max-w-none">
  {/* contenido markdown */}
</article>
```

## 🚀 Integración con Backend

Los visores obtienen el contenido mediante el endpoint `/file/{name}`:

```typescript
// lib/files.ts
export function fileUrl(fileName: string): string {
  const base = getBaseUrl().replace(/\/$/, '')
  return `${base}/file/${encodeURIComponent(fileName)}`
}
```

**Endpoint Backend:**
```python
@app.get("/file/{name:path}")
def serve_file(name: str):
    # Sirve archivos desde /backend/data/docs
    # Soporta: PDF, MD, TXT
```

## 🔍 Funcionalidad de Resaltado

### PDF
El resaltado se maneja mediante PDF.js con el parámetro `search`:
```
/pdfjs/web/viewer.html?file=doc.pdf&page=3&search=texto
```

### TXT
Resaltado inline con `<mark>`:
```tsx
<mark className="bg-yellow-200 px-1 rounded">{texto}</mark>
```

### Markdown
Resaltado temporal con background color:
```tsx
element.style.backgroundColor = '#fef3c7'
setTimeout(() => element.style.backgroundColor = '', 2000)
```

## 📱 Estados de UI

Todos los visores manejan 4 estados:

1. **Vacío** - No hay documento seleccionado
   ```tsx
   <div>Selecciona un documento para previsualizarlo aquí.</div>
   ```

2. **Cargando** - Fetching del contenido
   ```tsx
   <Loader2 className="animate-spin" />
   ```

3. **Error** - Fallo al cargar
   ```tsx
   <AlertCircle />
   <p>Error al cargar el archivo</p>
   ```

4. **Contenido** - Documento renderizado
   ```tsx
   {/* Visor específico del formato */}
   ```

## 🧪 Testing

Para probar los visores:

1. **TXT**: Sube un archivo `.txt`
2. **Markdown**: Sube un archivo `.md` con formato
3. **PDF**: Usa los PDFs existentes

Verifica:
- ✅ Carga correcta del contenido
- ✅ Resaltado de texto funcional
- ✅ Scroll automático al highlight
- ✅ Manejo de errores (archivo no existente)

## 🔄 Flujo de Navegación

```
App.tsx
  ↓
DocumentPreview (detecta tipo)
  ↓
├─ PdfPreview (si .pdf)
├─ TxtPreview (si .txt)
└─ MarkdownPreview (si .md)
```

## 🎯 Mejoras Futuras

- [ ] Visor para DOCX
- [ ] Visor para Excel/CSV
- [ ] Modo oscuro para visores
- [ ] Descarga de archivos
- [ ] Impresión de documentos
- [ ] Compartir fragmentos
