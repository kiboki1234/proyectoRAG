export default function Header({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="text-lg font-semibold text-gray-800">RAG Offline · Soberano</div>
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenSettings}
            className="rounded-xl border px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            Ajustes
          </button>
        </div>
      </div>
    </header>
  )
}
