'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Archive } from 'lucide-react'
import { ProtectedRoute } from '../../../components/auth/ProtectedRoute'
import { Navigation } from '../../../components/layout/Navigation'
import { Card, CardContent } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { EmptyState } from '../../../components/ui/empty-state'
import { Note } from '../../../lib/types'
import { getAllNotes } from '../../../lib/api/client'
import { toast } from 'sonner'

function AllNotesPage() {
  const router = useRouter()
  const [notes, setNotes] = useState<Note[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAllNotes()
  }, [])

  const loadAllNotes = async () => {
    try {
      const data = await getAllNotes()
      setNotes(data)
    } catch (error) {
      console.error('Failed to load notes:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen">
          <Navigation />
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-200"></div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="max-w-4xl mx-auto p-4">
        <div className="flex items-center gap-3 mb-6">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/archives')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">Toutes les notes</h1>
        </div>

        {notes.length === 0 ? (
          <EmptyState
            icon={Archive}
            title="Aucune note"
            description="Créez votre première note depuis la page Archives"
          />
        ) : (
          <div className="space-y-2">
            {notes.map(note => (
              <Card
                key={note.id}
                onClick={() => router.push(`/viz/${note.id}`)}
                className="cursor-pointer hover:border-plume-500/50 transition-all hover:shadow-lg"
              >
                <CardContent className="p-3 flex justify-between items-center">
                  <span className="font-medium truncate">{note.title}</span>
                  <span className="text-sm text-gray-500 ml-4 flex-shrink-0">
                    {note.updated_at > note.created_at
                      ? `Modifié le ${note.updated_at.toLocaleDateString('fr-FR')}`
                      : `Créé le ${note.created_at.toLocaleDateString('fr-FR')}`
                    }
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default function Page() {
  return (
    <ProtectedRoute>
      <AllNotesPage />
    </ProtectedRoute>
  )
}
