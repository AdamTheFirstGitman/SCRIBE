'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { FolderOpen } from 'lucide-react'
import { ProtectedRoute } from '../../components/auth/ProtectedRoute'
import { Navigation } from '../../components/layout/Navigation'
import { Card, CardContent } from '../../components/ui/card'
import { EmptyState } from '../../components/ui/empty-state'
import { Conversation } from '../../lib/types'
import { getConversations } from '../../lib/api/client'
import { getErrorMessage } from '../../lib/api/error-handler'
import { toast } from 'sonner'
import { formatRelativeDate } from '../../lib/utils'

function WorksPage() {
  const router = useRouter()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const data = await getConversations()
      setConversations(data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen">
          <Navigation />
          <div className="max-w-4xl mx-auto p-4">
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-200"></div>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="max-w-4xl mx-auto p-4">
        <h1 className="text-2xl font-bold mb-6">Conversations</h1>

        {conversations.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="Aucune conversation"
            description="Vos conversations apparaîtront ici"
          />
        ) : (
          <div className="space-y-3">
            {conversations.map(conv => (
              <Card
                key={conv.id}
                onClick={() => router.push(`/works/${conv.id}`)}
                className="cursor-pointer hover:border-plume-500/50 transition-all hover:shadow-lg"
              >
                <CardContent className="p-4">
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-lg mb-1 truncate">
                        {conv.title}
                      </h3>
                      <p className="text-sm text-gray-400 truncate">
                        {conv.note_titles.slice(0, 3).join(', ')}
                        {conv.note_titles.length > 3 && '...'}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      <span className="text-sm text-gray-500">
                        {formatRelativeDate(conv.updated_at)}
                      </span>
                      <span className="text-xs text-gray-600">
                        {conv.message_count} messages
                      </span>
                    </div>
                  </div>
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
      <WorksPage />
    </ProtectedRoute>
  )
}
