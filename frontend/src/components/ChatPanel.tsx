import { useState, KeyboardEvent, useRef, useEffect } from 'react'
import { ask, askStreaming, Citation } from '@/lib/api'
import { toast } from 'sonner'
import { SendHorizonal, Sparkles, Trash2, Download, Zap } from 'lucide-react'
import { Message } from '@/types/chat'
import { 
  getCurrentConversationId, 
  startNewConversation, 
  saveConversation, 
  loadConversation,
  downloadMarkdown 
} from '@/lib/conversations'
import SourcesSelect from './SourcesSelect'
import CitationsList from './CitationsList'
import Spinner from './Spinner'
import MarkdownRenderer from './MarkdownRenderer'
import { MessageFeedback } from './MessageFeedback'

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
  const [conversationId, setConversationId] = useState<string>('')
  const [useStreaming, setUseStreaming] = useState(true) // Por defecto streaming activado
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Cargar conversación al montar componente
  useEffect(() => {
    const convId = getCurrentConversationId()
    setConversationId(convId)
    
    loadConversation(convId).then(conv => {
      if (conv && conv.messages.length > 0) {
        setMessages(conv.messages)
        toast.success('Conversación anterior recuperada')
      }
    })
  }, [])

  // Auto-guardar cada 5 segundos
  useEffect(() => {
    if (messages.length === 0 || !conversationId) return
    
    const interval = setInterval(() => {
      saveConversation(conversationId, messages)
    }, 5000)
    
    return () => clearInterval(interval)
  }, [messages, conversationId])

  // Auto-scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = async () => {
    const q = question.trim()
    if (!q) return toast.info('Escribe una pregunta')
    
    // source puede ser undefined para buscar en todos los docs
    const effectiveSource = source && source.trim() ? source : undefined
    
    console.log('[ChatPanel] submit called', { question: q, source: effectiveSource, useStreaming })
    
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

      if (useStreaming) {
        console.log('[ChatPanel] Using streaming mode')
        // === MODO STREAMING ===
        const assistantId = `assistant-${Date.now()}`
        const assistantMessage: Message = {
          id: assistantId,
          role: 'assistant',
          content: '', // Se irá llenando token por token
          citations: [],
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])

        try {
          console.log('[ChatPanel] Calling askStreaming...')
          await askStreaming(
            q,
            effectiveSource,
            // onToken
            (token) => {
              setMessages(prev => {
                const lastIndex = prev.length - 1
                const last = prev[lastIndex]
                if (last.id === assistantId) {
                  const updated = [...prev]
                  updated[lastIndex] = { ...last, content: last.content + token }
                  return updated
                }
                return prev
              })
            },
            // onCitations
            (citations) => {
              setMessages(prev => {
                const lastIndex = prev.length - 1
                const last = prev[lastIndex]
                if (last.id === assistantId) {
                  const updated = [...prev]
                  updated[lastIndex] = { ...last, citations }
                  return updated
                }
                return prev
              })
            },
            // onMetadata
            (metadata) => {
              setMessages(prev => {
                const lastIndex = prev.length - 1
                const last = prev[lastIndex]
                if (last.id === assistantId) {
                  const updated = [...prev]
                  updated[lastIndex] = { 
                    ...last, 
                    cached: metadata.cached,
                    searchMode: metadata.search_mode,
                    temperature: metadata.temperature
                  }
                  return updated
                }
                return prev
              })
            },
            // onDone
            () => {
              setLoading(false)
            }
          )
        } catch (streamError: any) {
          console.error('Streaming error:', streamError)
          setLoading(false)
          throw streamError // Re-throw para que el catch exterior lo capture
        }
      } else {
        // === MODO NORMAL ===
        const res = await ask(q, effectiveSource)
        
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
      }
      
    } catch (e: any) {
      toast.error(e?.message || 'Error al preguntar')
    } finally {
      if (!useStreaming) {
        setLoading(false)
      }
    }
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      submit()
    }
  }

  const handleClearHistory = () => {
    if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
      // Crear nueva conversación
      const newConvId = startNewConversation()
      setConversationId(newConvId)
      setMessages([])
      toast.success('Historial borrado. Nueva conversación iniciada.')
    }
  }

  const handleExportMarkdown = () => {
    if (messages.length === 0) {
      toast.info('No hay mensajes para exportar')
      return
    }
    downloadMarkdown(messages, `conversacion-${conversationId}.md`)
    toast.success('Conversación exportada como Markdown')
  }
  
  const clearHistory = () => {
    handleClearHistory()
  }

  const exportChat = () => {
    handleExportMarkdown()
  }

  const handleJump = (c: Citation) => {
    if (c.source && c.source !== source) onSourceChange(c.source)
    if (typeof c.page === 'number') onJumpToPage(c.page, c.source ?? source, c.text)
  }

  return (
    <div className="flex h-[80vh] flex-col rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
      {/* Header - Solo título y controles */}
      <div className="border-b border-gray-200 dark:border-gray-800 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-500" />
            <span>Chat con tus documentos</span>
          </div>
          <div className="flex gap-2 items-center">
            {/* Toggle streaming */}
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className={`rounded-lg border px-3 py-1 text-xs flex items-center gap-1 ${
                useStreaming ? 'bg-brand-50 dark:bg-brand-900/20 border-brand-300 dark:border-brand-700 text-brand-700 dark:text-brand-400' : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 dark:text-gray-300'
              }`}
              title={useStreaming ? 'Streaming activado' : 'Streaming desactivado'}
            >
              <Zap className="h-3 w-3" />
              {useStreaming ? 'Stream' : 'Normal'}
            </button>
            
            {messages.length > 0 && (
              <>
                <button
                  onClick={exportChat}
                  className="rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-1 text-xs hover:bg-gray-50 dark:hover:bg-gray-800 dark:text-gray-300"
                  title="Exportar chat"
                >
                  <Download className="h-3 w-3" />
                </button>
                <button
                  onClick={clearHistory}
                  className="rounded-lg border border-red-300 dark:border-red-800 px-3 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                  title="Limpiar historial"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Messages - Historial de chat ARRIBA */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-gray-400 dark:text-gray-600">
            <div>
              <Sparkles className="mx-auto h-12 w-12 mb-3 text-gray-300 dark:text-gray-700" />
              <p className="text-sm">No hay mensajes aún</p>
              <p className="text-xs mt-1">Escribe tu primera pregunta abajo</p>
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
                  className={`max-w-[92%] rounded-2xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-brand-600 dark:bg-brand-700 text-white'
                      : 'bg-brand-50 dark:bg-brand-950/30 text-brand-900 dark:text-brand-100'
                  }`}
                >
                  {/* Header del mensaje */}
                  <div className="mb-1.5 flex items-center gap-2 text-xs opacity-70">
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
                      
                      {/* Feedback */}
                      <MessageFeedback 
                        messageId={msg.id} 
                        question={messages.find(m => m.role === 'user' && m.timestamp < msg.timestamp)?.content}
                        answer={msg.content}
                      />
                      
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

      {/* Input Area - ABAJO */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-3">
        <div className="space-y-3">
          {/* Selector de documentos - fila completa arriba */}
          <div>
            <SourcesSelect value={source} onChange={onSourceChange} />
          </div>
          
          {/* Input con botón integrado (estilo WhatsApp) - fila completa abajo */}
          <div className="relative">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Escribe tu pregunta aquí..."
              className="w-full resize-none rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-600 placeholder:text-gray-400 dark:placeholder:text-gray-600"
              rows={1}
              disabled={loading}
            />
            {/* Botón de enviar dentro del textarea */}
            <button
              onClick={submit}
              disabled={loading || !question.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-brand-600 dark:bg-brand-700 text-white hover:bg-brand-700 dark:hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              title="Enviar (Ctrl/⌘ + Enter)"
            >
              {loading ? (
                <Spinner />
              ) : (
                <SendHorizonal className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
