import { useEffect, useState } from 'react'
import { fileUrl } from '@/lib/files'
import { FileText, Loader2, AlertCircle } from 'lucide-react'

export default function TxtPreview({
  source,
  highlight,
}: {
  source?: string
  highlight?: string
}) {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!source) {
      setContent('')
      setError(null)
      return
    }

    const loadContent = async () => {
      try {
        setLoading(true)
        setError(null)
        const url = fileUrl(source)
        const res = await fetch(url)
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`)
        const text = await res.text()
        setContent(text)
      } catch (e: any) {
        setError(e?.message || 'Error al cargar el archivo')
        setContent('')
      } finally {
        setLoading(false)
      }
    }

    loadContent()
  }, [source])

  // Auto-scroll y highlight cuando hay texto destacado
  useEffect(() => {
    if (highlight && content) {
      // Buscar el texto en el contenido y hacer scroll
      const container = document.getElementById('txt-preview-content')
      if (container) {
        const highlightLower = highlight.toLowerCase()
        const contentLower = content.toLowerCase()
        const index = contentLower.indexOf(highlightLower)
        
        if (index !== -1) {
          // Calcular posición aproximada basada en caracteres
          const lines = content.substring(0, index).split('\n').length
          const lineHeight = 24 // altura aproximada de línea en px
          const scrollPos = Math.max(0, (lines - 5) * lineHeight)
          
          setTimeout(() => {
            container.scrollTo({ top: scrollPos, behavior: 'smooth' })
          }, 100)
        }
      }
    }
  }, [highlight, content])

  if (!source) {
    return (
      <div className="flex h-[72vh] items-center justify-center rounded-2xl border bg-white p-4 text-sm text-gray-500 shadow-sm">
        <div className="text-center">
          <FileText className="mx-auto mb-2 h-12 w-12 text-gray-300" />
          <p>Selecciona un documento para previsualizarlo aquí.</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex h-[72vh] items-center justify-center rounded-2xl border bg-white p-4 shadow-sm">
        <div className="text-center text-gray-500">
          <Loader2 className="mx-auto mb-2 h-8 w-8 animate-spin text-brand-600" />
          <p className="text-sm">Cargando archivo...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[72vh] items-center justify-center rounded-2xl border bg-white p-4 shadow-sm">
        <div className="text-center text-red-600">
          <AlertCircle className="mx-auto mb-2 h-8 w-8" />
          <p className="text-sm font-medium">Error al cargar el archivo</p>
          <p className="mt-1 text-xs text-gray-500">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border bg-white shadow-sm overflow-hidden">
      <div className="border-b bg-gray-50 px-4 py-2 flex items-center gap-2 text-sm text-gray-700">
        <FileText className="h-4 w-4" />
        <span className="font-medium">{source}</span>
      </div>
      
      <div 
        id="txt-preview-content"
        className="h-[calc(72vh-40px)] overflow-y-auto p-6"
      >
        <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 leading-relaxed">
          {highlight ? (
            // Resaltar texto si existe
            content.split(new RegExp(`(${highlight})`, 'gi')).map((part, i) => 
              part.toLowerCase() === highlight.toLowerCase() ? (
                <mark key={i} className="bg-yellow-200 px-1 rounded">{part}</mark>
              ) : (
                part
              )
            )
          ) : (
            content
          )}
        </pre>
      </div>
    </div>
  )
}
