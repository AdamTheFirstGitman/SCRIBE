'use client'

import { useState, useEffect } from 'react'
import { FileText, MessageSquare, Coins, Zap } from 'lucide-react'
import { ProtectedRoute } from '../../components/auth/ProtectedRoute'
import { Navigation } from '../../components/layout/Navigation'
import { Card, CardContent } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ThemeToggle } from '../../components/theme/ThemeToggle'
import { useSession } from '../../lib/hooks/useSession'
import { Metrics } from '../../lib/types'
import { getMetrics } from '../../lib/api/client'
import { getErrorMessage } from '../../lib/api/error-handler'
import { toast } from 'sonner'

function SettingsPage() {
  const { logout } = useSession()
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [])

  const loadMetrics = async () => {
    try {
      const data = await getMetrics()
      setMetrics(data)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    if (confirm('Voulez-vous vraiment vous déconnecter ?')) {
      logout()
    }
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="max-w-4xl mx-auto p-4 space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-50">Paramètres</h1>

        {/* Section 1: Metrics Dashboard */}
        <section>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-50">Statistiques</h2>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-200"></div>
            </div>
          ) : metrics ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <FileText className="h-6 w-6 mx-auto mb-2 text-plume-500" />
                  <p className="text-3xl font-bold text-plume-500">
                    {metrics.total_notes}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Notes</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 text-center">
                  <MessageSquare className="h-6 w-6 mx-auto mb-2 text-mimir-500" />
                  <p className="text-3xl font-bold text-mimir-500">
                    {metrics.total_conversations}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Conversations</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 text-center">
                  <Zap className="h-6 w-6 mx-auto mb-2 text-yellow-500" />
                  <p className="text-3xl font-bold text-yellow-500">
                    {(metrics.total_tokens ?? 0).toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Tokens</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 text-center">
                  <Coins className="h-6 w-6 mx-auto mb-2 text-green-500" />
                  <p className="text-3xl font-bold text-green-500">
                    {(metrics.total_cost_eur ?? 0).toFixed(2)} €
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Coût total</p>
                </CardContent>
              </Card>
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 text-center py-8">
              Impossible de charger les statistiques
            </p>
          )}
        </section>

        {/* Section 2: Preferences */}
        <section>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-50">Préférences</h2>
          <Card>
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Thème</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Clair, sombre ou automatique
                  </p>
                </div>
                <ThemeToggle />
              </div>

              <div className="border-t border-gray-200 dark:border-gray-800 pt-4">
                <p className="font-medium mb-2">Raccourcis clavier</p>
                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <p>⌘ K - Palette de commandes</p>
                  <p>⌘ / - Aide</p>
                  <p>⌘ B - Toggle sidebar</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Section 3: Account */}
        <section>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-50">Compte</h2>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="font-medium">Utilisateur</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">king_001</p>
                </div>
              </div>

              <Button
                variant="destructive"
                onClick={handleLogout}
                className="w-full"
              >
                Se déconnecter
              </Button>
            </CardContent>
          </Card>
        </section>

        {/* Section 4: About */}
        <section>
          <Card>
            <CardContent className="p-4 text-center text-sm text-gray-600 dark:text-gray-400">
              <p className="mb-1">
                <span className="font-semibold bg-gradient-to-r from-plume-500 to-mimir-500 bg-clip-text text-transparent">
                  SCRIBE
                </span>{' '}
                - Phase 2.2
              </p>
              <p>Plume & Mimir - Système de gestion de connaissances</p>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}

export default function Page() {
  return (
    <ProtectedRoute>
      <SettingsPage />
    </ProtectedRoute>
  )
}
