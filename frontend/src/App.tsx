import { useState } from 'react'
import Header from '@/components/Header'
import SettingsModal from '@/components/SettingsModal'
import UploadZone from '@/components/UploadZone'
import AskPanel from '@/components/AskPanel'
import DocumentPreview from '@/components/DocumentPreview'

export default function App() {
  const [openSettings, setOpenSettings] = useState(false)
  const [selectedSource, setSelectedSource] = useState<string | undefined>(undefined)
  const [selectedPage, setSelectedPage] = useState<number | undefined>(undefined)
  const [highlight, setHighlight] = useState<string | undefined>(undefined)

  const changeSource = (v?: string) => {
    setSelectedSource(v)
    setSelectedPage(undefined)
    setHighlight(undefined)
  }

  const handleJumpToPage = (page: number, src?: string, text?: string) => {
    if (src && src !== selectedSource) setSelectedSource(src)
    setSelectedPage(page)
    setHighlight(text) // ⬅️ este texto se usará en search=
  }

  return (
    <div className="min-h-full">
      <Header onOpenSettings={() => setOpenSettings(true)} />

      <main className="mx-auto max-w-6xl px-4 py-6 space-y-6">
        <UploadZone />

        <div className="grid gap-6 md:grid-cols-2">
          <DocumentPreview source={selectedSource} page={selectedPage} highlight={highlight} />
          <AskPanel source={selectedSource} onSourceChange={changeSource} onJumpToPage={handleJumpToPage} />
        </div>

        <p className="text-center text-xs text-gray-400">
          Hecho con ❤️ y Software Libre · Funciona 100% local
        </p>
      </main>

      <SettingsModal open={openSettings} onClose={() => setOpenSettings(false)} />
    </div>
  )
}
