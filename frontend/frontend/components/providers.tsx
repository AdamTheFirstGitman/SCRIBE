'use client'

import React from 'react'
import { Toaster } from 'sonner'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  return (
    <>
      {children}
      <Toaster
        position="top-right"
        theme="dark"
        toastOptions={{
          style: {
            background: 'rgba(31, 41, 55, 0.95)',
            border: '1px solid rgba(75, 85, 99, 0.3)',
            color: '#f9fafb',
          },
        }}
      />
    </>
  )
}