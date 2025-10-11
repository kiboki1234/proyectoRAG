import { useEffect, useMemo, useState } from 'react'
import { getSources } from '@/lib/api'
import { getLocalSources } from '@/lib/storage'

export default function SourcesSelect({
  value,
  onChange,
}: {
  value?: string
  onChange: (v?: string) => void
}) {
  const [remote, setRemote] = useState<string[]>([])
  const locals = getLocalSources()

  useEffect(() => {
    let alive = true
    getSources().then(list => { if (alive) setRemote(list) })
    return () => { alive = false }
  }, [])

  const options = useMemo(() => {
    const set = new Set<string>([...locals, ...remote].filter(Boolean))
    return Array.from(set).sort()
  }, [locals, remote])

  return (
    <div>
      <label className="text-sm text-gray-700">Documento</label>
      <select
        className="mt-1 w-full rounded-xl border bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        value={value ?? (options.length ? options[0] : '')}
        onChange={e => onChange(e.target.value || undefined)}
      >
        {options.map(name => (
          <option key={name} value={name}>{name}</option>
        ))}
      </select>
      <div className="mt-1 text-[11px] text-gray-400">Si eliges un documento, el filtro será estricto por ese archivo.</div>
    </div>
  )
}
