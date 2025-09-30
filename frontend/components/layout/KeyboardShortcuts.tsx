'use client'

import { useRouter } from 'next/navigation'
import { useHotkeys } from 'react-hotkeys-hook'

export function KeyboardShortcuts() {
  const router = useRouter()

  // Navigation shortcuts
  useHotkeys('ctrl+h,meta+h', (e) => {
    e.preventDefault()
    router.push('/')
  })

  useHotkeys('ctrl+shift+c,meta+shift+c', (e) => {
    e.preventDefault()
    router.push('/chat')
  })

  useHotkeys('ctrl+u,meta+u', (e) => {
    e.preventDefault()
    router.push('/upload')
  })

  useHotkeys('ctrl+f,meta+f', (e) => {
    e.preventDefault()
    router.push('/search')
  })

  useHotkeys('ctrl+comma,meta+comma', (e) => {
    e.preventDefault()
    router.push('/settings')
  })

  // Agent shortcuts
  useHotkeys('ctrl+1,meta+1', (e) => {
    e.preventDefault()
    router.push('/chat?agent=plume')
  })

  useHotkeys('ctrl+2,meta+2', (e) => {
    e.preventDefault()
    router.push('/chat?agent=mimir')
  })

  // Command Palette is handled in CommandPalette.tsx (Ctrl+K)

  return null
}