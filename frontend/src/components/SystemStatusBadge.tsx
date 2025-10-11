import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from '@/lib/api'
import { Activity, Database, Cpu, AlertCircle } from 'lucide-react'

export default function SystemStatusBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const data = await getHealth()
        setHealth(data)
        setLoading(false)
      } catch {
        setLoading(false)
      }
    }

    loadHealth()
    const interval = setInterval(loadHealth, 60000) // Actualizar cada minuto
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-gray-100 px-3 py-1.5 text-xs">
        <div className="h-2 w-2 animate-pulse rounded-full bg-gray-400" />
        <span className="text-gray-600">Cargando...</span>
      </div>
    )
  }

  if (!health) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-1.5 text-xs text-red-700 border border-red-200">
        <AlertCircle className="h-3 w-3" />
        <span>Sistema offline</span>
      </div>
    )
  }

  const statusConfig = {
    ok: {
      color: 'bg-green-100 text-green-700 border-green-200',
      dotColor: 'bg-green-500',
      label: 'Operativo',
    },
    degraded: {
      color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      dotColor: 'bg-yellow-500',
      label: 'Degradado',
    },
    error: {
      color: 'bg-red-100 text-red-700 border-red-200',
      dotColor: 'bg-red-500',
      label: 'Error',
    },
  }

  const config = statusConfig[health.status as keyof typeof statusConfig] || statusConfig.ok

  return (
    <div className={`flex items-center gap-3 rounded-lg border px-3 py-1.5 text-xs ${config.color}`}>
      {/* Status indicator */}
      <div className="flex items-center gap-1.5">
        <div className={`h-2 w-2 animate-pulse rounded-full ${config.dotColor}`} />
        <span className="font-medium">{config.label}</span>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-2 border-l pl-2 opacity-75">
        <div className="flex items-center gap-1" title="LLM cargado">
          <Cpu className="h-3 w-3" />
          <span>{health.llm_loaded ? '✓' : '✗'}</span>
        </div>
        <div className="flex items-center gap-1" title="Índice disponible">
          <Database className="h-3 w-3" />
          <span>{health.index_exists ? '✓' : '✗'}</span>
        </div>
        <div className="flex items-center gap-1" title={`${health.chunks_count.toLocaleString()} chunks`}>
          <Activity className="h-3 w-3" />
          <span>{(health.chunks_count / 1000).toFixed(1)}k</span>
        </div>
      </div>
    </div>
  )
}
