'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Command } from 'cmdk'
import {
  Home,
  MessageSquare,
  Upload,
  Search,
  Settings,
  Feather,
  Brain,
  Moon,
  Sun,
  Monitor,
} from 'lucide-react'
import { useTheme } from '../theme/ThemeProvider'
import { motion, AnimatePresence } from 'framer-motion'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const router = useRouter()
  const { setTheme } = useTheme()

  // Listen for Ctrl+K / Cmd+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const runCommand = (callback: () => void) => {
    setOpen(false)
    callback()
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={() => setOpen(false)}
          />

          {/* Command Dialog */}
          <div className="fixed top-0 left-0 right-0 z-50 flex items-start justify-center p-4 pt-[20vh]">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-2xl"
            >
              <Command className="card overflow-hidden shadow-2xl">
                <div className="flex items-center border-b border-gray-800 dark:border-gray-800 light:border-gray-200 px-4">
                  <Search className="w-5 h-5 text-gray-400 dark:text-gray-400 light:text-gray-600 mr-3" />
                  <Command.Input
                    placeholder="Rechercher action..."
                    className="flex-1 bg-transparent border-0 outline-none py-4 text-gray-50 dark:text-gray-50 light:text-gray-900 placeholder:text-gray-400 dark:placeholder:text-gray-400 light:placeholder:text-gray-600"
                  />
                  <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-400 dark:text-gray-400 light:text-gray-600 bg-gray-800 dark:bg-gray-800 light:bg-gray-100 rounded">
                    ESC
                  </kbd>
                </div>

                <Command.List className="max-h-96 overflow-y-auto p-2 scrollbar-thin">
                  <Command.Empty className="py-6 text-center text-sm text-gray-400 dark:text-gray-400 light:text-gray-600">
                    Aucun résultat trouvé
                  </Command.Empty>

                  {/* Navigation Group */}
                  <Command.Group
                    heading="Navigation"
                    className="text-xs text-gray-500 dark:text-gray-500 light:text-gray-500 uppercase tracking-wider px-2 py-2"
                  >
                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Home className="w-4 h-4" />
                      <span>Accueil</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+H
                      </kbd>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/chat'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>Chat</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+Shift+C
                      </kbd>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/upload'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Upload className="w-4 h-4" />
                      <span>Upload Document</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+U
                      </kbd>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/search'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Search className="w-4 h-4" />
                      <span>Recherche</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+F
                      </kbd>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/settings'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Settings className="w-4 h-4" />
                      <span>Paramètres</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+,
                      </kbd>
                    </Command.Item>
                  </Command.Group>

                  <Command.Separator className="h-px bg-gray-800 dark:bg-gray-800 light:bg-gray-200 my-2" />

                  {/* Agents Group */}
                  <Command.Group
                    heading="Agents"
                    className="text-xs text-gray-500 dark:text-gray-500 light:text-gray-500 uppercase tracking-wider px-2 py-2"
                  >
                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/chat?agent=plume'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Feather className="w-4 h-4 text-plume-500" />
                      <span>Parler à Plume</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+1
                      </kbd>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => router.push('/chat?agent=mimir'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Brain className="w-4 h-4 text-mimir-500" />
                      <span>Parler à Mimir</span>
                      <kbd className="ml-auto text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
                        Ctrl+2
                      </kbd>
                    </Command.Item>
                  </Command.Group>

                  <Command.Separator className="h-px bg-gray-800 dark:bg-gray-800 light:bg-gray-200 my-2" />

                  {/* Theme Group */}
                  <Command.Group
                    heading="Thème"
                    className="text-xs text-gray-500 dark:text-gray-500 light:text-gray-500 uppercase tracking-wider px-2 py-2"
                  >
                    <Command.Item
                      onSelect={() => runCommand(() => setTheme('light'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Sun className="w-4 h-4" />
                      <span>Mode clair</span>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => setTheme('dark'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Moon className="w-4 h-4" />
                      <span>Mode sombre</span>
                    </Command.Item>

                    <Command.Item
                      onSelect={() => runCommand(() => setTheme('system'))}
                      className="flex items-center gap-3 px-3 py-3 rounded-lg cursor-pointer aria-selected:bg-plume-500/10 dark:aria-selected:bg-plume-500/10 light:aria-selected:bg-plume-50 text-gray-200 dark:text-gray-200 light:text-gray-900 aria-selected:text-plume-400 dark:aria-selected:text-plume-400 light:aria-selected:text-plume-600"
                    >
                      <Monitor className="w-4 h-4" />
                      <span>Système</span>
                    </Command.Item>
                  </Command.Group>
                </Command.List>
              </Command>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}