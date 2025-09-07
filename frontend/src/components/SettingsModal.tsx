import { useEffect, useState } from 'react'
import { getBaseUrl, setBaseUrl } from '@/lib/storage'

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [baseUrl, setUrl] = useState('')

  useEffect(() => {
    if (open) setUrl(getBaseUrl())
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold">Ajustes</h2>
        <p className="mt-1 text-sm text-gray-500">Configura la URL del backend (FastAPI).</p>

        <label className="mt-4 block text-sm font-medium text-gray-700">Base URL</label>
        <input
          className="mt-1 w-full rounded-xl border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
          value={baseUrl}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="http://127.0.0.1:8000"
        />

        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-xl border px-4 py-2 text-sm">Cerrar</button>
          <button
            onClick={() => {
              setBaseUrl(baseUrl)
              onClose()
            }}
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  )
}
