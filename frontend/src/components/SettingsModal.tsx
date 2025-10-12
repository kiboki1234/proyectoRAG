import { useEffect, useState } from 'react'
import { getBaseUrl, setBaseUrl } from '@/lib/storage'
import { toast } from 'sonner'
import { getStats, getCacheStats, clearCache, getDocuments, deleteDocument, deleteAllDocuments, type StatsResponse, type CacheStatsResponse, type DocumentsResponse } from '@/lib/api'
import { RefreshCw, Trash2, FileText, Database, Zap, AlertTriangle } from 'lucide-react'
import { documentEvents } from '@/lib/events'

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [url, setUrl] = useState('')
  const [activeTab, setActiveTab] = useState<'general' | 'stats' | 'cache' | 'documents'>('general')
  
  // Stats state
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [cacheStats, setCacheStats] = useState<CacheStatsResponse | null>(null)
  const [documents, setDocuments] = useState<DocumentsResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const loadAllData = async () => {
    try {
      setLoading(true)
      const [statsData, cacheData, docsData] = await Promise.all([
        getStats().catch(e => {
          console.error('Error loading stats:', e)
          // Devolver datos vacíos si falla
          return {
            total_documents: 0,
            total_chunks: 0,
            avg_chunk_size: 0,
            index_dimension: null,
            embedder_model: 'unknown'
          }
        }),
        getCacheStats().catch(e => {
          console.error('Error loading cache stats:', e)
          return {
            size: 0,
            max_size: 0,
            hit_rate: 0,
            total_hits: 0,
            total_misses: 0
          }
        }),
        getDocuments().catch(e => {
          console.error('Error loading documents:', e)
          return {
            total_documents: 0,
            total_chunks: 0,
            documents: []
          }
        }),
      ])
      setStats(statsData)
      setCacheStats(cacheData)
      setDocuments(docsData)
    } catch (e: any) {
      // Este catch solo debería ejecutarse si hay un error muy grave
      console.error('Error crítico cargando datos:', e)
      toast.error('Error cargando estadísticas: ' + (e?.message || 'Unknown'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open) {
      setUrl(getBaseUrl())
      loadAllData()
    }
  }, [open])

  // Suscribirse a eventos de documentos cuando el modal está abierto
  useEffect(() => {
    if (open) {
      const events: Array<'document-uploaded' | 'document-deleted' | 'documents-cleared'> = 
        ['document-uploaded', 'document-deleted', 'documents-cleared']
      
      events.forEach(event => documentEvents.on(event, loadAllData))
      
      return () => {
        events.forEach(event => documentEvents.off(event, loadAllData))
      }
    }
  }, [open])

  const save = () => {
    setBaseUrl(url)
    toast.success('URL del backend guardada')
    onClose()
  }

  const handleClearCache = async () => {
    if (!confirm('¿Limpiar todo el caché de queries?')) return
    try {
      await clearCache()
      toast.success('Caché limpiado')
      await loadAllData()
    } catch (e: any) {
      toast.error('Error: ' + (e?.message || 'Unknown'))
    }
  }

  const handleDeleteDocument = async (filename: string) => {
    if (!confirm(`¿Eliminar el documento "${filename}"?\n\nEsto eliminará el archivo y sus chunks del índice.`)) return
    try {
      const result = await deleteDocument(filename)
      toast.success(result.message || 'Documento eliminado')
      documentEvents.emit('document-deleted')
      // No llamar loadAllData() aquí, el evento lo hará
    } catch (e: any) {
      toast.error('Error al eliminar: ' + (e?.message || 'Unknown'))
    }
  }

  const handleDeleteAllDocuments = async () => {
    if (!documents?.documents || documents.documents.length === 0) {
      toast.info('No hay documentos para eliminar')
      return
    }

    const docCount = documents.documents.length
    const chunkCount = documents.total_chunks ?? 0

    if (!confirm(
      `⚠️ ADVERTENCIA: Vas a eliminar TODOS los documentos\n\n` +
      `• ${docCount} documentos\n` +
      `• ${chunkCount} chunks\n\n` +
      `Esta acción NO se puede deshacer.\n\n` +
      `¿Estás seguro?`
    )) return

    try {
      const result = await deleteAllDocuments()
      toast.success(result.message || 'Todos los documentos eliminados')
      documentEvents.emit('documents-cleared')
      // No llamar loadAllData() aquí, el evento lo hará
    } catch (e: any) {
      toast.error('Error al eliminar: ' + (e?.message || 'Unknown'))
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 dark:bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-3xl max-h-[90vh] rounded-2xl bg-white dark:bg-gray-900 shadow-xl flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-800 p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Configuración y Estadísticas</h2>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-800 px-6">
          <div className="flex gap-1">
            {[
              { id: 'general', label: '⚙️ General' },
              { id: 'stats', label: '📊 Estadísticas' },
              { id: 'cache', label: '💾 Caché' },
              { id: 'documents', label: '📚 Documentos' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-brand-600 dark:border-brand-500 text-brand-600 dark:text-brand-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'general' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  URL del backend
                </label>
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8000"
                  className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-600 placeholder:text-gray-400 dark:placeholder:text-gray-600"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Cambia la URL si tu backend está en otro puerto o servidor
                </p>
              </div>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Estadísticas del Sistema</h3>
                <button
                  onClick={loadAllData}
                  disabled={loading}
                  className="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-700 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  Actualizar
                </button>
              </div>

              {stats && (
                <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 p-4 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">📄 Documentos totales</span>
                    <span className="font-mono font-semibold text-gray-900 dark:text-gray-100">{stats.total_documents ?? 0}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">🧩 Chunks indexados</span>
                    <span className="font-mono font-semibold text-gray-900 dark:text-gray-100">{(stats.total_chunks ?? 0).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">📏 Tamaño promedio de chunk</span>
                    <span className="font-mono font-semibold">{(stats.avg_chunk_size ?? 0).toFixed(0)} caracteres</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">🎯 Dimensión de embeddings</span>
                    <span className="font-mono font-semibold">{stats.index_dimension ?? 'N/A'}</span>
                  </div>
                  <div className="border-t pt-3 mt-3">
                    <span className="text-xs text-gray-500">Modelo de embeddings:</span>
                    <code className="block mt-1 text-xs bg-gray-100 p-2 rounded">{stats.embedder_model ?? 'N/A'}</code>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'cache' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Caché de Queries</h3>
                <button
                  onClick={handleClearCache}
                  className="flex items-center gap-2 rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                  Limpiar Caché
                </button>
              </div>

              {cacheStats && (
                <div className="space-y-4">
                  <div className="rounded-lg border p-4 space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">📦 Entradas actuales</span>
                      <span className="font-mono font-semibold">
                        {cacheStats.size ?? 0} / {cacheStats.max_size ?? 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">🎯 Tasa de aciertos</span>
                      <span className="font-mono font-semibold text-green-600">
                        {((cacheStats.hit_rate ?? 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">✅ Total hits</span>
                      <span className="font-mono font-semibold text-green-600">
                        {(cacheStats.total_hits ?? 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">❌ Total misses</span>
                      <span className="font-mono font-semibold text-red-600">
                        {(cacheStats.total_misses ?? 0).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-2">
                      <span>Uso del caché</span>
                      <span>{(((cacheStats.size ?? 0) / (cacheStats.max_size ?? 1)) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-brand-600 h-3 rounded-full transition-all"
                        style={{ width: `${((cacheStats.size ?? 0) / (cacheStats.max_size ?? 1)) * 100}%` }}
                      />
                    </div>
                  </div>

                  {(cacheStats.hit_rate ?? 0) > 0 && (
                    <div className="rounded-lg bg-green-50 border border-green-200 p-3 flex items-start gap-2">
                      <Zap className="h-4 w-4 text-green-600 mt-0.5" />
                      <div className="text-xs text-green-800">
                        <strong>Caché funcionando bien!</strong> Estás ahorrando {(cacheStats.total_hits ?? 0).toLocaleString()} llamadas al LLM.
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Documentos Indexados</h3>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {documents && (
                      <span>
                        {documents.total_documents ?? 0} documentos · {(documents.total_chunks ?? 0).toLocaleString()} chunks
                      </span>
                    )}
                  </div>
                </div>
                {documents?.documents && documents.documents.length > 0 && (
                  <button
                    onClick={handleDeleteAllDocuments}
                    className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 transition-colors"
                  >
                    <AlertTriangle className="h-4 w-4" />
                    Eliminar Todos
                  </button>
                )}
              </div>

              {documents?.documents && documents.documents.length > 0 ? (
                <div className="space-y-2">
                  {documents.documents.map((doc) => (
                    <div
                      key={doc.name}
                      className={`rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${
                        !doc.indexed 
                          ? 'border-orange-300 dark:border-orange-700 bg-orange-50/50 dark:bg-orange-900/10' 
                          : 'border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <FileText className={`h-5 w-5 mt-0.5 flex-shrink-0 ${
                          !doc.indexed 
                            ? 'text-orange-500 dark:text-orange-400' 
                            : 'text-gray-400 dark:text-gray-500'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">{doc.name}</div>
                          <div className="flex gap-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                            {doc.indexed ? (
                              <>
                                <span>🧩 {doc.chunks} chunks</span>
                                <span>📝 {(doc.total_chars / 1000).toFixed(1)}k caracteres</span>
                                {doc.has_pages && <span>📄 PDF con páginas</span>}
                              </>
                            ) : (
                              <span className="text-orange-600 dark:text-orange-400 font-medium">
                                ⚠️ Archivo huérfano (no indexado)
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteDocument(doc.name)}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded border border-red-200 dark:border-red-800 transition-colors flex-shrink-0"
                          title="Eliminar documento"
                        >
                          <Trash2 className="h-3 w-3" />
                          Eliminar
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400 dark:text-gray-500">
                  <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No hay documentos indexados aún</p>
                  <p className="text-xs mt-1">Sube documentos para empezar</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-6 flex justify-end gap-2">
          <button
            className="rounded-xl border px-4 py-2 text-sm hover:bg-gray-50"
            onClick={onClose}
          >
            Cerrar
          </button>
          {activeTab === 'general' && (
            <button
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700"
              onClick={save}
            >
              Guardar
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
