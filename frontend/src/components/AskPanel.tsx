// frontend/src/components/AskPanel.tsx
import { useState, KeyboardEvent } from 'react'
import { ask, Citation } from '@/lib/api'
import { toast } from 'sonner'
import { SendHorizonal, Sparkles } from 'lucide-react'
import SourcesSelect from './SourcesSelect'
import CitationsList from './CitationsList'
import Spinner from './Spinner'

export default function AskPanel({
  source,
  onSourceChange,
  onJumpToPage,
}: {
  source?: string
  onSourceChange: (v?: string) => void
  onJumpToPage: (page: number, src?: string, text?: string) => void
}) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string>('')
  const [citations, setCitations] = useState<Citation[]>([])

  const submit = async () => {
    const q = question.trim()
    if (!q) return toast.info('Escribe una pregunta')
    try {
      setLoading(true)
      const res = await ask(q, source)
      setAnswer(res.answer)
      setCitations(res.citations)
    } catch (e: any) {
      setAnswer('')
      setCitations([])
      toast.error(e?.message || 'Error al preguntar')
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      submit()
    }
  }

  const handleJump = (c: Citation) => {
    // Si la cita apunta a otro documento, cámbialo primero
    if (c.source && c.source !== source) {
      onSourceChange(c.source)
    }
    // Navega a la página y resalta usando el texto de la cita
    if (typeof c.page === 'number') {
      onJumpToPage(c.page, c.source ?? source, c.text)
    }
  }

  return (
    // Altura fija + layout en columnas para que solo la respuesta haga scroll
    <div className="flex h-[72vh] flex-col rounded-2xl border bg-white p-4 shadow-sm">
      {/* Encabezado */}
      <div className="mb-3 flex items-center gap-2 text-sm text-gray-600">
        <Sparkles className="h-4 w-4 text-brand-600" />
        Haz preguntas sobre tus documentos. Respuesta siempre en el idioma de la pregunta.
      </div>

      {/* Formulario */}
      <div className="grid gap-3 md:grid-cols-3">
        <div className="md:col-span-2">
          <label className="text-sm text-gray-700">Pregunta</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            placeholder="¿Cuál es el total a pagar y la fecha de emisión?"
            className="mt-1 w-full resize-y rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            rows={3}
          />
          <div className="mt-1 text-xs text-gray-400">Sugerencia: Ctrl/⌘ + Enter para enviar</div>
        </div>
        <div>
          <SourcesSelect value={source} onChange={(v) => { onSourceChange(v); }} />
        </div>
      </div>

      {/* Botón enviar */}
      <div className="mt-3 flex justify-end">
        <button
          onClick={submit}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? <Spinner /> : <SendHorizonal className="h-4 w-4" />}
          Preguntar
        </button>
      </div>

      {/* Área de respuesta: ocupa el resto y SOLO aquí hay scroll */}
      <div className="mt-4 flex-1 min-h-0">
        <div className="h-full overflow-y-auto rounded-xl border bg-brand-50 p-4 text-brand-900">
          <div className="text-sm font-semibold">Respuesta</div>
          {answer ? (
            <>
              <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">{answer}</p>
              <CitationsList items={citations} onJump={handleJump} />
            </>
          ) : (
            <p className="mt-2 text-sm text-brand-900/70">
              Aún no hay respuesta. Escribe tu pregunta y presiona <b>Preguntar</b>.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
