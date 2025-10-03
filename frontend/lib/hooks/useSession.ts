'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Session } from '../types'

export function useSession() {
  const router = useRouter()
  const [session, setSession] = useState<Session | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check session on mount
    const stored = localStorage.getItem('session')
    if (stored) {
      try {
        const parsed: Session = JSON.parse(stored)
        if (parsed.expires > Date.now()) {
          setSession(parsed)
        } else {
          // Session expired
          localStorage.removeItem('session')
        }
      } catch (error) {
        console.error('Failed to parse session:', error)
        localStorage.removeItem('session')
      }
    }
    setIsLoading(false)
  }, [])

  const login = (username: string, password: string): boolean => {
    if (username === 'KING' && password === 'Faire la diff') {
      const newSession: Session = {
        user_id: 'king_001',
        logged_in: true,
        expires: Date.now() + 30 * 24 * 3600 * 1000 // 30 days
      }
      localStorage.setItem('session', JSON.stringify(newSession))
      setSession(newSession)
      return true
    }
    return false
  }

  const logout = () => {
    localStorage.removeItem('session')
    setSession(null)
    router.push('/login')
  }

  return {
    session,
    login,
    logout,
    isAuthenticated: !!session,
    isLoading
  }
}
