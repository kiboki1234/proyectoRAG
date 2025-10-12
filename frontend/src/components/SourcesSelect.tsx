import { useEffect, useMemo, useState } from 'react'
import { getSources, getDocuments, type DocumentsResponse } from '@/lib/api'
import { FileText, Loader2 } from 'lucide-react'
import { documentEvents } from '@/lib/events'

export default function SourcesSelect({
  value,
  onChange,
}: {
  value?: string
  onChange: (v?: string) => void
}) {
  const [remote, setRemote] = useState<string[]>([])
  const [docsInfo, setDocsInfo] = useState<DocumentsResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      setLoading(true)
      const [sources, docs] = await Promise.all([
        getSources(),
        getDocuments(),
      ])
      setRemote(sources)
      setDocsInfo(docs)
    } catch (e) {
      // Fallback si falla
      getSources().then(list => setRemote(list)).catch(() => {})
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Suscribirse a eventos de documentos para actualización en tiempo real
  useEffect(() => {
    const events: Array<'document-uploaded' | 'document-deleted' | 'documents-cleared'> = 
      ['document-uploaded', 'document-deleted', 'documents-cleared']
    
    events.forEach(event => documentEvents.on(event, loadData))
    
    return () => {
      events.forEach(event => documentEvents.off(event, loadData))
    }
  }, [])

  // 🔧 FIX: Solo usar documentos del backend (remote)
  // No usar localStorage para evitar mostrar docs borrados
  const options = useMemo(() => {
    return remote.filter(Boolean).sort()
  }, [remote])

  const getDocInfo = (docName: string) => {
    if (!docsInfo) return null
    return docsInfo.documents.find(d => d.name === docName)
  }

  return (
    <div>
      <label className="text-sm text-gray-700">Documento</label>
      
      {loading ? (
        <div className="mt-1 w-full rounded-xl border bg-gray-50 px-3 py-2 text-sm flex items-center gap-2 text-gray-500">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>Cargando documentos...</span>
        </div>
      ) : (
        <>
          <select
            className="mt-1 w-full rounded-xl border bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={value ?? (options.length ? options[0] : '')}
            onChange={e => onChange(e.target.value || undefined)}
          >
            {/* Opción para buscar en todo el corpus */}
            <option value="">📚 Buscar en todos los documentos</option>
            
            {/* Documentos individuales */}
            {options.map(name => {
              const info = getDocInfo(name)
              const label = info 
                ? `📄 ${name} (${info.chunks} chunks, ${(info.total_chars / 1000).toFixed(1)}k chars)`
                : `📄 ${name}`
              return (
                <option key={name} value={name}>
                  {label}
                </option>
              )
            })}
          </select>

          {/* Info del documento seleccionado */}
          {value && docsInfo && (
            <div className="mt-2 rounded-lg bg-blue-50 border border-blue-200 p-2 text-xs text-blue-800">
              <div className="flex items-start gap-2">
                <FileText className="h-3 w-3 mt-0.5 flex-shrink-0" />
                <div>
                  {(() => {
                    const info = getDocInfo(value)
                    if (info) {
                      return (
                        <>
                          <strong>{info.name}</strong>
                          <div className="mt-1 space-y-0.5">
                            <div>🧩 {info.chunks} fragmentos indexados</div>
                            <div>📝 {(info.total_chars / 1000).toFixed(1)}k caracteres totales</div>
                            {info.has_pages && <div>📄 PDF con información de páginas</div>}
                          </div>
                        </>
                      )
                    }
                    return <span>{value}</span>
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* Info de búsqueda multi-documento */}
          {!value && docsInfo && (
            <div className="mt-2 rounded-lg bg-purple-50 border border-purple-200 p-2 text-xs text-purple-800">
              <div className="flex items-start gap-2">
                <span className="text-base">🔍</span>
                <div>
                  <strong>Modo búsqueda global</strong>
                  <div className="mt-1">
                    Buscará en los {docsInfo.total_documents} documentos ({docsInfo.total_chunks.toLocaleString()} chunks)
                    con diversificación balanceada entre fuentes.
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
