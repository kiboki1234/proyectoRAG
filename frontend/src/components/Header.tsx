import SystemStatusBadge from './SystemStatusBadge'
import { ThemeToggle } from './ThemeToggle'

export default function Header({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <header className="border-b bg-white dark:bg-gray-900 dark:border-gray-800">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="text-lg font-semibold text-gray-800 dark:text-gray-100">RAG Offline · Soberano</div>
        <div className="flex items-center gap-3">
          <SystemStatusBadge />
          <ThemeToggle />
          <button
            onClick={onOpenSettings}
            className="rounded-xl border border-gray-300 dark:border-gray-700 px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 dark:text-gray-200"
          >
            Ajustes
          </button>
        </div>
      </div>
    </header>
  )
}
