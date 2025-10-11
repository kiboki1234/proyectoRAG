import { useEffect, useState } from 'react'
import { fileUrl } from '@/lib/files'
import { FileText, Loader2, AlertCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function MarkdownPreview({
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

  // Auto-scroll cuando hay texto destacado
  useEffect(() => {
    if (highlight && content) {
      const container = document.getElementById('md-preview-content')
      if (container) {
        // Buscar elementos que contengan el texto destacado
        setTimeout(() => {
          const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null
          )
          
          let node
          while ((node = walker.nextNode())) {
            const text = node.textContent || ''
            if (text.toLowerCase().includes(highlight.toLowerCase())) {
              const element = node.parentElement
              if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' })
                // Highlight temporal
                element.style.backgroundColor = '#fef3c7'
                setTimeout(() => {
                  element.style.backgroundColor = ''
                }, 2000)
                break
              }
            }
          }
        }, 100)
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
        id="md-preview-content"
        className="h-[calc(72vh-40px)] overflow-y-auto p-6"
      >
        <article className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-a:text-brand-600 prose-code:text-brand-700 prose-pre:bg-gray-50">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  )
}
