'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function ClearCachePage() {
  const router = useRouter()
  const [status, setStatus] = useState('Nettoyage en cours...')
  const [details, setDetails] = useState<string[]>([])

  useEffect(() => {
    async function clearAll() {
      const logs: string[] = []

      try {
        // 1. Unregister Service Worker
        if ('serviceWorker' in navigator) {
          const registrations = await navigator.serviceWorker.getRegistrations()

          for (const registration of registrations) {
            await registration.unregister()
            logs.push(`✅ Service Worker désinstallé`)
          }
        }

        // 2. Clear Cache Storage
        if ('caches' in window) {
          const cacheNames = await caches.keys()

          for (const cacheName of cacheNames) {
            await caches.delete(cacheName)
            logs.push(`✅ Cache "${cacheName}" supprimé`)
          }
        }

        // 3. Clear LocalStorage (session SCRIBE uniquement)
        if (typeof window !== 'undefined') {
          localStorage.removeItem('session')
          logs.push(`✅ Session locale effacée`)
        }

        setDetails(logs)
        setStatus('✅ Nettoyage terminé !')

        // Redirect après 2 secondes
        setTimeout(() => {
          window.location.href = '/'
        }, 2000)

      } catch (error) {
        setStatus('❌ Erreur lors du nettoyage')
        logs.push(`Erreur: ${error}`)
        setDetails(logs)
      }
    }

    clearAll()
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
      <div className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
        <h1 className="text-2xl font-bold text-white text-center">
          {status}
        </h1>

        {details.length > 0 && (
          <div className="space-y-2 text-sm text-gray-300">
            {details.map((detail, i) => (
              <div key={i} className="p-2 bg-gray-800 rounded">
                {detail}
              </div>
            ))}
          </div>
        )}

        <p className="text-center text-gray-400 text-sm">
          Redirection automatique vers la home...
        </p>
      </div>
    </div>
  )
}
