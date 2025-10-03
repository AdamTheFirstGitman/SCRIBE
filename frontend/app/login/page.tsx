'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from '../../lib/hooks/useSession'
import { Card, CardHeader, CardContent } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Button } from '../../components/ui/button'

export default function LoginPage() {
  const router = useRouter()
  const { login, isAuthenticated } = useSession()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Redirect if already authenticated
  if (isAuthenticated) {
    router.push('/')
    return null
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const success = login(username, password)

    if (success) {
      router.push('/')
    } else {
      setError('Identifiant ou mot de passe incorrect')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-2 bg-gradient-to-r from-plume-500 to-mimir-500 bg-clip-text text-transparent">
              SCRIBE - Plume & Mimir
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Accès à votre espace de connaissances
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Shkoun</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Beemet?</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="current-password"
              />
            </div>

            {error && (
              <p className="text-sm text-red-500 text-center">{error}</p>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
