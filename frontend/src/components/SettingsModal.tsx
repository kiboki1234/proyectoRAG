import { useEffect, useState } from 'react'
import { getBaseUrl, setBaseUrl } from '@/lib/storage'
import { toast } from 'sonner'

export default function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [url, setUrl] = useState('')

  useEffect(() => {
    if (open) setUrl(getBaseUrl())
  }, [open])

  const save = () => {
    setBaseUrl(url)
    toast.success('URL del backend guardada')
    onClose()
  }

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">Ajustes</h2>
        <label className="mt-4 block text-sm text-gray-700">URL del backend</label>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="http://127.0.0.1:8000"
          className="mt-1 w-full rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <div className="mt-4 flex justify-end gap-2">
          <button className="rounded-xl border px-4 py-2 text-sm hover:bg-gray-50" onClick={onClose}>Cancelar</button>
          <button className="rounded-xl bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700" onClick={save}>Guardar</button>
        </div>
      </div>
    </div>
  )
}
