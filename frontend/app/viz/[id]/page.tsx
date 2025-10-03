'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, MessageSquare, Loader2 } from 'lucide-react'
import { ProtectedRoute } from '../../../components/auth/ProtectedRoute'
import { Navigation } from '../../../components/layout/Navigation'
import { Button } from '../../../components/ui/button'
import { Note } from '../../../lib/types'
import { getNote, convertToHTML } from '../../../lib/api/client'
import { getErrorMessage } from '../../../lib/api/error-handler'
import { cn } from '../../../lib/utils'
import { toast } from 'sonner'

type ViewMode = 'text' | 'html'

function VizPage() {
  const router = useRouter()
  const params = useParams()
  const noteId = params['id'] as string

  const [note, setNote] = useState<Note | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('html')
  const [isLoading, setIsLoading] = useState(true)
  const [isConverting, setIsConverting] = useState(false)

  useEffect(() => {
    loadNote()
  }, [noteId])

  const loadNote = async () => {
    try {
      const data = await getNote(noteId)
      setNote(data)

      // Si pas de HTML, commencer en mode text
      if (!data.html_content) {
        setViewMode('text')
      }
    } catch (error) {
      console.error('Failed to load note:', error)
      toast.error(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleHTML = async () => {
    if (viewMode === 'text') {
      // Switch to HTML
      if (!note?.html_content) {
        // Need to convert - trigger conversion then poll
        setIsConverting(true)

        try {
          // Trigger conversion
          await convertToHTML(noteId)

          // Poll every 2s for HTML content
          const startTime = Date.now()
          const timeout = 30000 // 30s timeout

          const pollInterval = setInterval(async () => {
            try {
              const updatedNote = await getNote(noteId)

              if (updatedNote.html_content) {
                // Conversion complete!
                setNote(updatedNote)
                setViewMode('html')
                setIsConverting(false)
                clearInterval(pollInterval)
                toast.success('Conversion HTML terminée')
              } else if (Date.now() - startTime > timeout) {
                // Timeout
                clearInterval(pollInterval)
                setIsConverting(false)
                toast.error('Timeout: conversion HTML trop longue')
              }
            } catch (error) {
              clearInterval(pollInterval)
              setIsConverting(false)
              toast.error(getErrorMessage(error))
            }
          }, 2000)

        } catch (error) {
          console.error('HTML conversion failed:', error)
          toast.error(getErrorMessage(error))
          setIsConverting(false)
        }
      } else {
        setViewMode('html')
      }
    } else {
      // Switch to text
      setViewMode('text')
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

  if (!note) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen">
          <Navigation />
          <div className="max-w-4xl mx-auto p-4 text-center">
            <p className="text-gray-400">Note introuvable</p>
            <Button
              variant="outline"
              onClick={() => router.push('/archives')}
              className="mt-4"
            >
              Retour aux archives
            </Button>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <div className="min-h-screen pb-24">
      <Navigation />

      {/* Header sticky */}
      <div className="sticky top-0 bg-gray-900/95 backdrop-blur border-b border-gray-800 p-3 flex items-center justify-between z-10">
        {/* Left: Back button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>

        {/* Center: Title */}
        <h1 className="font-semibold truncate max-w-md mx-4">
          {note.title}
        </h1>

        {/* Right: Toggle + loader */}
        <div className="flex items-center gap-2">
          {/* Toggle TEXT/HTML */}
          <div className="flex items-center bg-gray-800 rounded-lg p-1">
            <button
              className={cn(
                'px-3 py-1 rounded text-sm transition-colors',
                viewMode === 'text' ? 'bg-gray-700 text-white' : 'text-gray-400'
              )}
              onClick={() => setViewMode('text')}
            >
              TEXT
            </button>
            <button
              className={cn(
                'px-3 py-1 rounded text-sm transition-colors',
                viewMode === 'html' ? 'bg-gray-700 text-white' : 'text-gray-400'
              )}
              onClick={handleToggleHTML}
              disabled={isConverting}
            >
              HTML
            </button>
          </div>

          {/* Loader */}
          {isConverting && (
            <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
          )}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-4xl mx-auto p-6">
        {isConverting && (
          <div className="flex items-center gap-2 text-sm text-gray-400 mb-4 p-3 bg-gray-800 rounded-lg">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Conversion HTML en cours...</span>
          </div>
        )}

        {viewMode === 'text' ? (
          <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-900 p-4 rounded-lg">
            {note.text_content}
          </pre>
        ) : (
          <div
            className="prose prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: note.html_content }}
          />
        )}
      </main>

      {/* Floating Chat Button */}
      <Button
        size="icon"
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
        onClick={() => router.push(`/?context=note:${note.id}`)}
        title="Discuter de cette note avec les agents"
      >
        <MessageSquare className="h-6 w-6" />
      </Button>
    </div>
  )
}

export default function Page() {
  return (
    <ProtectedRoute>
      <VizPage />
    </ProtectedRoute>
  )
}
