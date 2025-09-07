import { Settings, Upload, Bot } from 'lucide-react'

export default function Header({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <header className="sticky top-0 z-30 w-full border-b bg-white/70 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-2xl bg-brand-600 text-white grid place-items-center shadow">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold leading-tight">RAG Offline Soberano</h1>
            <p className="text-xs text-gray-500">Privado • Local • Citable</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onOpenSettings} className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm hover:bg-gray-50">
            <Settings className="h-4 w-4" /> Ajustes
          </button>
        </div>
      </div>
    </header>
  )
}
