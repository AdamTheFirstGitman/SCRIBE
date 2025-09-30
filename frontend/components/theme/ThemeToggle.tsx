'use client'

import { useTheme } from './ThemeProvider'
import { Moon, Sun, Monitor } from 'lucide-react'
import { motion } from 'framer-motion'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const themes = [
    { value: 'light' as const, icon: Sun, label: 'Light' },
    { value: 'dark' as const, icon: Moon, label: 'Dark' },
    { value: 'system' as const, icon: Monitor, label: 'System' },
  ]

  return (
    <div className="flex items-center gap-1 p-1 rounded-lg bg-gray-800/50 dark:bg-gray-800/50 light:bg-gray-100">
      {themes.map(({ value, icon: Icon, label }) => {
        const isActive = theme === value

        return (
          <button
            key={value}
            onClick={() => setTheme(value)}
            className={`relative flex items-center justify-center w-9 h-9 rounded-md transition-colors ${
              isActive
                ? 'text-plume-400 dark:text-plume-400 light:text-plume-600'
                : 'text-gray-400 hover:text-gray-200 dark:text-gray-400 dark:hover:text-gray-200 light:text-gray-600 light:hover:text-gray-900'
            }`}
            aria-label={`Switch to ${label} theme`}
            aria-pressed={isActive}
          >
            {isActive && (
              <motion.div
                layoutId="theme-indicator"
                className="absolute inset-0 bg-plume-500/20 dark:bg-plume-500/20 light:bg-plume-100 rounded-md"
                transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
              />
            )}
            <Icon className="relative w-4 h-4" />
          </button>
        )
      })}
    </div>
  )
}