import { useEffect, useState } from 'react'
import { getBaseUrl, setBaseUrl } from '@/lib/storage'
import { toast } from 'sonner'
import { getStats, getCacheStats, clearCache, getDocuments, type StatsResponse, type CacheStatsResponse, type DocumentsResponse } from '@/lib/api'
import { RefreshCw, Trash2, FileText, Database, Zap } from 'lucide-react'

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [url, setUrl] = useState('')
  const [activeTab, setActiveTab] = useState<'general' | 'stats' | 'cache' | 'documents'>('general')
  
  // Stats state
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [cacheStats, setCacheStats] = useState<CacheStatsResponse | null>(null)
  const [documents, setDocuments] = useState<DocumentsResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open) {
      setUrl(getBaseUrl())
      loadAllData()
    }
  }, [open])

  const loadAllData = async () => {
    try {
      setLoading(true)
      const [statsData, cacheData, docsData] = await Promise.all([
        getStats(),
        getCacheStats(),
        getDocuments(),
      ])
      setStats(statsData)
      setCacheStats(cacheData)
      setDocuments(docsData)
    } catch (e: any) {
      toast.error('Error cargando estadísticas: ' + (e?.message || 'Unknown'))
    } finally {
      setLoading(false)
    }
  }

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

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-3xl max-h-[90vh] rounded-2xl bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="border-b p-6">
          <h2 className="text-xl font-semibold">Configuración y Estadísticas</h2>
        </div>

        {/* Tabs */}
        <div className="border-b px-6">
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
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL del backend
                </label>
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8000"
                  className="w-full rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Cambia la URL si tu backend está en otro puerto o servidor
                </p>
              </div>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Estadísticas del Sistema</h3>
                <button
                  onClick={loadAllData}
                  disabled={loading}
                  className="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  Actualizar
                </button>
              </div>

              {stats && (
                <div className="rounded-lg border p-4 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">📄 Documentos totales</span>
                    <span className="font-mono font-semibold">{stats.total_documents ?? 0}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">🧩 Chunks indexados</span>
                    <span className="font-mono font-semibold">{(stats.total_chunks ?? 0).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">📏 Tamaño promedio de chunk</span>
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
                <h3 className="text-lg font-semibold">Documentos Indexados</h3>
                <div className="text-sm text-gray-600">
                  {documents && (
                    <span>
                      {documents.total_documents ?? 0} docs · {(documents.total_chunks ?? 0).toLocaleString()} chunks
                    </span>
                  )}
                </div>
              </div>

              {documents?.documents && documents.documents.length > 0 ? (
                <div className="space-y-2">
                  {documents.documents.map((doc) => (
                    <div
                      key={doc.name}
                      className="rounded-lg border p-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{doc.name}</div>
                          <div className="flex gap-4 mt-1 text-xs text-gray-500">
                            <span>🧩 {doc.chunks} chunks</span>
                            <span>📝 {(doc.total_chars / 1000).toFixed(1)}k caracteres</span>
                            {doc.has_pages && <span>📄 PDF con páginas</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
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
