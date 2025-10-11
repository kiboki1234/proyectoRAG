import { useState, KeyboardEvent } from 'react'
import { ask, Citation } from '@/lib/api'
import { validateQuestion, validateSource, VALIDATION } from '@/lib/validation'
import { toast } from 'sonner'
import { SendHorizonal, Sparkles, AlertCircle } from 'lucide-react'
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
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleQuestionChange = (value: string) => {
    setQuestion(value)
    
    // Validación en tiempo real (solo mostrar error si el usuario ya escribió algo)
    if (value.trim().length > 0) {
      const validation = validateQuestion(value)
      setValidationError(validation.valid ? null : validation.error || null)
    } else {
      setValidationError(null)
    }
  }

  const submit = async () => {
    const q = question.trim()
    
    // Validar pregunta
    if (!q) {
      toast.info('Escribe una pregunta')
      return
    }

    const questionValidation = validateQuestion(q)
    if (!questionValidation.valid) {
      toast.error(questionValidation.error)
      setValidationError(questionValidation.error || null)
      return
    }

    // Validar source si existe
    if (source) {
      const sourceValidation = validateSource(source)
      if (!sourceValidation.valid) {
        toast.error(sourceValidation.error)
        return
      }
    }

    try {
      setLoading(true)
      // Limpia el estado para evitar arrastre de textos antiguos
      setAnswer('')
      setCitations([])
      setValidationError(null)

      const res = await ask(q, source)
      setAnswer(res.answer)
      setCitations(res.citations)
      
      // Opcional: Limpiar la pregunta después de una respuesta exitosa
      // setQuestion('')
    } catch (e: any) {
      setAnswer('')
      setCitations([])
      
      // Mejorar el manejo de errores del backend
      const errorMessage = e?.message || 'Error al preguntar'
      toast.error(errorMessage)
      
      // Si el error es de validación, mostrarlo también en el input
      if (errorMessage.includes('debe tener al menos') || errorMessage.includes('no puede exceder')) {
        setValidationError(errorMessage)
      }
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
    if (c.source && c.source !== source) onSourceChange(c.source)
    if (typeof c.page === 'number') onJumpToPage(c.page, c.source ?? source, c.text)
  }

  const charCount = question.length
  const isNearLimit = charCount > VALIDATION.QUESTION_MAX_LENGTH * 0.9
  const isOverLimit = charCount > VALIDATION.QUESTION_MAX_LENGTH

  return (
    <div className="flex h-[72vh] flex-col rounded-2xl border bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2 text-sm text-gray-600">
        <Sparkles className="h-4 w-4 text-brand-600" />
        Haz preguntas sobre tus documentos. Respuesta en el idioma de la pregunta.
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="md:col-span-2">
          <label className="text-sm text-gray-700">Pregunta</label>
          <textarea
            value={question}
            onChange={(e) => handleQuestionChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder="¿Cuál es el RUC, la fecha de autorización y el total?"
            className={`mt-1 w-full resize-y rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
              validationError || isOverLimit
                ? 'border-red-300 focus:ring-red-500'
                : 'focus:ring-brand-500'
            }`}
            rows={3}
          />
          
          <div className="mt-1 flex items-center justify-between text-xs">
            <div className="text-gray-400">
              Sugerencia: Ctrl/⌘ + Enter para enviar
            </div>
            <div className={`font-mono ${
              isOverLimit ? 'text-red-600 font-semibold' : 
              isNearLimit ? 'text-yellow-600' : 
              'text-gray-400'
            }`}>
              {charCount}/{VALIDATION.QUESTION_MAX_LENGTH}
            </div>
          </div>

          {validationError && (
            <div className="mt-1 flex items-center gap-1 text-xs text-red-600">
              <AlertCircle className="h-3 w-3" />
              <span>{validationError}</span>
            </div>
          )}
        </div>
        <div>
          <SourcesSelect value={source} onChange={onSourceChange} />
        </div>
      </div>

      <div className="mt-3 flex justify-end">
        <button
          onClick={submit}
          disabled={loading || !!validationError || isOverLimit}
          className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60 disabled:cursor-not-allowed"
          title={validationError || undefined}
        >
          {loading ? <Spinner /> : <SendHorizonal className="h-4 w-4" />}
          Preguntar
        </button>
      </div>

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
