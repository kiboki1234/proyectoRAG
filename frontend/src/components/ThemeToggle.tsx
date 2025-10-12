import { useState, useEffect } from 'react'
import { Moon, Sun, Monitor } from 'lucide-react'
import { getTheme, setTheme, type Theme } from '@/lib/theme'

export function ThemeToggle() {
  const [theme, setThemeState] = useState<Theme>(getTheme())
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    // Aplicar tema al montar
    setTheme(theme)
  }, [])

  const handleThemeChange = (newTheme: Theme) => {
    setThemeState(newTheme)
    setTheme(newTheme)
    setIsOpen(false)
  }

  const icons = {
    light: Sun,
    dark: Moon,
    system: Monitor
  }

  const CurrentIcon = icons[theme]

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        title="Cambiar tema"
      >
        <CurrentIcon className="h-5 w-5 text-gray-700 dark:text-gray-300" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Menu */}
          <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 z-20">
            <div className="p-2 space-y-1">
              <button
                onClick={() => handleThemeChange('light')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                  theme === 'light' ? 'bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-400' : ''
                }`}
              >
                <Sun className="h-4 w-4" />
                <span className="text-sm">Claro</span>
              </button>
              
              <button
                onClick={() => handleThemeChange('dark')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                  theme === 'dark' ? 'bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-400' : ''
                }`}
              >
                <Moon className="h-4 w-4" />
                <span className="text-sm">Oscuro</span>
              </button>
              
              <button
                onClick={() => handleThemeChange('system')}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                  theme === 'system' ? 'bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-400' : ''
                }`}
              >
                <Monitor className="h-4 w-4" />
                <span className="text-sm">Sistema</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
