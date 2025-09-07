import { useEffect, useState } from 'react'
import { getSources } from '@/lib/api'
import { RotateCw } from 'lucide-react'
import Spinner from './Spinner'

export default function SourcesSelect({
  value,
  onChange,
}: {
  value?: string
  onChange: (v?: string) => void
}) {
  const [options, setOptions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    try {
      setLoading(true)
      const list = await getSources()
      setOptions(Array.isArray(list) ? list : [])
    } catch {
      setOptions([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div>
      <label className="text-sm text-gray-700">Documento</label>
      <div className="mt-1 flex items-center gap-2">
        <select
          className="w-full rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value || undefined)}
        >
          <option value="">Todos los documentos</option>
          {options.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <button
          type="button"
          onClick={load}
          title="Actualizar lista"
          className="rounded-lg border p-2 hover:bg-gray-50"
        >
          {loading ? <Spinner /> : <RotateCw className="h-4 w-4" />}
        </button>
      </div>

      {!!value && (
        <button
          onClick={() => onChange(undefined)}
          className="mt-1 text-xs text-gray-500 hover:underline"
        >
          Limpiar filtro
        </button>
      )}
    </div>
  )
}
