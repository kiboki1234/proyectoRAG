import { useEffect, useState } from 'react';
import { getHealth, getStats, getCacheStats, type HealthResponse, type StatsResponse, type CacheStatsResponse } from '../lib/api';

export default function SystemStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [cacheStats, setCacheStats] = useState<CacheStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [healthData, statsData, cacheData] = await Promise.all([
        getHealth(),
        getStats(),
        getCacheStats(),
      ]);
      setHealth(healthData);
      setStats(statsData);
      setCacheStats(cacheData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Actualizar cada 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-4 text-gray-500">Cargando estado del sistema...</div>;
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-700">❌ Error: {error}</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok': return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Estado del Sistema</h2>
        <button
          onClick={loadData}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          🔄 Actualizar
        </button>
      </div>

      {/* Health Status */}
      {health && (
        <div className={`p-4 rounded-lg border ${getStatusColor(health.status)}`}>
          <h3 className="font-semibold mb-2">🏥 Estado de Salud</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>Estado: <strong>{health.status.toUpperCase()}</strong></div>
            <div>Versión: <strong>{health.version}</strong></div>
            <div>LLM Cargado: {health.llm_loaded ? '✅' : '❌'}</div>
            <div>Índice Existe: {health.index_exists ? '✅' : '❌'}</div>
            <div className="col-span-2">
              Chunks Indexados: <strong>{health.chunks_count.toLocaleString()}</strong>
            </div>
          </div>
        </div>
      )}

      {/* System Stats */}
      {stats && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold mb-2">📊 Estadísticas del Sistema</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>Documentos Totales:</div>
            <div className="font-mono">{stats.total_documents}</div>
            
            <div>Chunks Totales:</div>
            <div className="font-mono">{stats.total_chunks.toLocaleString()}</div>
            
            <div>Tamaño Promedio Chunk:</div>
            <div className="font-mono">{stats.avg_chunk_size.toFixed(0)} chars</div>
            
            <div>Dimensión Embeddings:</div>
            <div className="font-mono">{stats.index_dimension || 'N/A'}</div>
            
            <div className="col-span-2">
              Modelo: <code className="text-xs bg-white px-1 py-0.5 rounded">{stats.embedder_model}</code>
            </div>
          </div>
        </div>
      )}

      {/* Cache Stats */}
      {cacheStats && (
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <h3 className="font-semibold mb-2">💾 Estadísticas del Caché</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>Entradas Actuales:</div>
            <div className="font-mono">{cacheStats.size} / {cacheStats.max_size}</div>
            
            <div>Tasa de Aciertos:</div>
            <div className="font-mono">{(cacheStats.hit_rate * 100).toFixed(1)}%</div>
            
            <div>Total Hits:</div>
            <div className="font-mono text-green-600">{cacheStats.total_hits}</div>
            
            <div>Total Misses:</div>
            <div className="font-mono text-red-600">{cacheStats.total_misses}</div>
          </div>
          
          {/* Progress bar */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>Uso del caché</span>
              <span>{((cacheStats.size / cacheStats.max_size) * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all"
                style={{ width: `${(cacheStats.size / cacheStats.max_size) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
