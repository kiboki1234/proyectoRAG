import { useState, KeyboardEvent, useRef, useEffect } from 'react'
import { ask, Citation } from '@/lib/api'
import { toast } from 'sonner'
import { SendHorizonal, Sparkles, Trash2, Download, Zap } from 'lucide-react'
import { Message } from '@/types/chat'
import SourcesSelect from './SourcesSelect'
import CitationsList from './CitationsList'
import Spinner from './Spinner'
import MarkdownRenderer from './MarkdownRenderer'

export default function ChatPanel({
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
  const [messages, setMessages] = useState<Message[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = async () => {
    const q = question.trim()
    if (!q) return toast.info('Escribe una pregunta')
    
    // source puede ser undefined para buscar en todos los docs
    const effectiveSource = source && source.trim() ? source : undefined
    
    try {
      setLoading(true)
      
      // Agregar mensaje del usuario
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: q,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, userMessage])
      setQuestion('') // Limpiar input

      const res = await ask(q, effectiveSource)
      
      // Agregar respuesta del asistente
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        timestamp: new Date(),
        cached: res.cached,
        searchMode: res.search_mode_used,
        temperature: res.temperature_used,
      }
      setMessages(prev => [...prev, assistantMessage])
      
    } catch (e: any) {
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

  const clearHistory = () => {
    if (confirm('¿Limpiar todo el historial de conversación?')) {
      setMessages([])
      toast.success('Historial limpiado')
    }
  }

  const exportChat = () => {
    const markdown = messages.map(m => {
      const role = m.role === 'user' ? '👤 Usuario' : '🤖 Asistente'
      const timestamp = m.timestamp.toLocaleString()
      let content = `### ${role} - ${timestamp}\n\n${m.content}\n\n`
      
      if (m.citations && m.citations.length > 0) {
        content += `**Fuentes:**\n`
        m.citations.forEach((c, i) => {
          content += `${i + 1}. ${c.source || 'Desconocido'} (p. ${c.page || '?'})\n`
        })
        content += '\n'
      }
      
      return content
    }).join('---\n\n')

    const blob = new Blob([`# Chat RAG - ${new Date().toLocaleDateString()}\n\n${markdown}`], 
      { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Chat exportado')
  }

  const handleJump = (c: Citation) => {
    if (c.source && c.source !== source) onSourceChange(c.source)
    if (typeof c.page === 'number') onJumpToPage(c.page, c.source ?? source, c.text)
  }

  return (
    <div className="flex h-[72vh] flex-col rounded-2xl border bg-white shadow-sm">
      {/* Header */}
      <div className="border-b p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Sparkles className="h-4 w-4 text-brand-600" />
            <span>Chat con tus documentos</span>
          </div>
          <div className="flex gap-2">
            {messages.length > 0 && (
              <>
                <button
                  onClick={exportChat}
                  className="rounded-lg border px-3 py-1 text-xs hover:bg-gray-50"
                  title="Exportar chat"
                >
                  <Download className="h-3 w-3" />
                </button>
                <button
                  onClick={clearHistory}
                  className="rounded-lg border px-3 py-1 text-xs text-red-600 hover:bg-red-50"
                  title="Limpiar historial"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </>
            )}
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="md:col-span-2">
            <label className="text-sm text-gray-700">Pregunta</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKey}
              placeholder="¿Qué información necesitas?"
              className="mt-1 w-full resize-y rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              rows={2}
              disabled={loading}
            />
            <div className="mt-1 text-xs text-gray-400">
              Ctrl/⌘ + Enter para enviar
            </div>
          </div>
          <div>
            <SourcesSelect value={source} onChange={onSourceChange} />
          </div>
        </div>

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
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-gray-400">
            <div>
              <Sparkles className="mx-auto h-12 w-12 mb-3 text-gray-300" />
              <p className="text-sm">No hay mensajes aún</p>
              <p className="text-xs mt-1">Escribe tu primera pregunta arriba</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-brand-600 text-white'
                      : 'bg-brand-50 text-brand-900'
                  }`}
                >
                  {/* Header del mensaje */}
                  <div className="mb-2 flex items-center gap-2 text-xs opacity-70">
                    <span>{msg.role === 'user' ? '👤 Tú' : '🤖 Asistente'}</span>
                    <span>·</span>
                    <span>{msg.timestamp.toLocaleTimeString()}</span>
                    {msg.cached && (
                      <>
                        <span>·</span>
                        <Zap className="h-3 w-3" />
                        <span className="sr-only">Respuesta desde caché</span>
                      </>
                    )}
                  </div>

                  {/* Contenido */}
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                  ) : (
                    <>
                      <MarkdownRenderer content={msg.content} />
                      
                      {/* Metadata */}
                      {(msg.searchMode || msg.temperature !== undefined) && (
                        <div className="mt-2 text-xs opacity-60 border-t border-brand-200 pt-2">
                          {msg.searchMode && (
                            <span>Modo: {msg.searchMode === 'single' ? '📄 Un doc' : '📚 Multi-doc'}</span>
                          )}
                          {msg.temperature !== undefined && (
                            <span className="ml-2">
                              🌡️ {(() => {
                                if (msg.temperature === 0) return 'Factual'
                                if (msg.temperature < 0.5) return 'Balanceado'
                                return 'Creativo'
                              })()}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Citas */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 border-t border-brand-200 pt-3">
                          <CitationsList items={msg.citations} onJump={handleJump} />
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  )
}
