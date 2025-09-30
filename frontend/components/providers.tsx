'use client'

import React from 'react'
import { Toaster } from 'sonner'
import { ThemeProvider, useTheme } from './theme/ThemeProvider'
import { CommandPalette } from './layout/CommandPalette'
import { KeyboardShortcuts } from './layout/KeyboardShortcuts'

interface ProvidersProps {
  children: React.ReactNode
}

function ToasterWithTheme() {
  const { resolvedTheme } = useTheme()

  return (
    <Toaster
      position="top-right"
      theme={resolvedTheme}
      toastOptions={{
        style:
          resolvedTheme === 'dark'
            ? {
                background: 'rgba(31, 41, 55, 0.95)',
                border: '1px solid rgba(75, 85, 99, 0.3)',
                color: '#f9fafb',
              }
            : {
                background: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid rgba(229, 231, 235, 1)',
                color: '#111827',
              },
      }}
    />
  )
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      {children}
      <KeyboardShortcuts />
      <CommandPalette />
      <ToasterWithTheme />
    </ThemeProvider>
  )
}