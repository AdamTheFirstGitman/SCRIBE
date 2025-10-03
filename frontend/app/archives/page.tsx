'use client'

import { useState, useEffect, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Upload as UploadIcon, Mic, Loader2 } from 'lucide-react'
import { ProtectedRoute } from '../../components/auth/ProtectedRoute'
import { Navigation } from '../../components/layout/Navigation'
import { Card, CardHeader, CardContent } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Button } from '../../components/ui/button'
import { Textarea } from '../../components/ui/textarea'
import { Note, NoteSearchResult } from '../../lib/types'
import { getRecentNotes, searchNotes, uploadText, uploadAudio } from '../../lib/api/client'
import { getErrorMessage } from '../../lib/api/error-handler'
import { debounce } from '../../lib/utils'
import { toast } from 'sonner'

type UploadMode = 'text' | 'audio'

function ArchivesPage() {
  const router = useRouter()

  // State
  const [recentNotes, setRecentNotes] = useState<Note[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<NoteSearchResult[]>([])
  const [uploadMode, setUploadMode] = useState<UploadMode>('text')

  // Text upload
  const [textContent, setTextContent] = useState('')
  const [textContext, setTextContext] = useState('')
  const [textContextAudio, setTextContextAudio] = useState<File | null>(null)

  // Audio upload
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [audioContext, setAudioContext] = useState('')
  const [audioContextAudio, setAudioContextAudio] = useState<File | null>(null)

  const [isUploading, setIsUploading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSearching, setIsSearching] = useState(false)

  useEffect(() => {
    loadRecentNotes()
  }, [])

  const loadRecentNotes = async () => {
    try {
      const notes = await getRecentNotes()
      setRecentNotes(notes)
    } catch (error) {
      console.error('Failed to load recent notes:', error)
      toast.error(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  // Debounced search
  const performSearch = debounce(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([])
      setIsSearching(false)
      return
    }

    setIsSearching(true)
    try {
      const results = await searchNotes(query)
      setSearchResults(results)
    } catch (error) {
      console.error('Search failed:', error)
      toast.error(getErrorMessage(error))
    } finally {
      setIsSearching(false)
    }
  }, 300)

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
    performSearch(value)
  }

  const handleTextUpload = async () => {
    if (!textContent.trim()) return

    setIsUploading(true)
    try {
      const note = await uploadText(textContent, textContext || undefined)
      toast.success(`Note créée: ${note.title}`)
      router.push(`/viz/${note.id}`)
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(getErrorMessage(error))
      setIsUploading(false)
    }
  }

  const handleAudioFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setAudioFile(file)
    }
  }

  const handleAudioUpload = async () => {
    if (!audioFile) return

    setIsUploading(true)
    try {
      const result = await uploadAudio(
        audioFile,
        audioContext || undefined,
        audioContextAudio || undefined
      )

      toast.success(`Note créée: ${result.title}`)
      router.push(`/viz/${result.note_id}`)
    } catch (error) {
      console.error('Audio upload failed:', error)
      toast.error(getErrorMessage(error))
      setIsUploading(false)
    }
  }

  const handleContextAudioRecord = () => {
    // TODO: Implement context audio recording in Phase 2
    console.log('Context audio recording not yet implemented')
    // Placeholder to use state
    if (uploadMode === 'text') {
      setTextContextAudio(null)
    } else {
      setAudioContextAudio(null)
    }
  }

  const handleContextAudioUpload = () => {
    // TODO: Implement context audio upload in Phase 2
    console.log('Context audio upload not yet implemented')
  }

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen">
          <Navigation />
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-200"></div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="max-w-4xl mx-auto p-4 space-y-6">
        {/* Section 1: Recent Notes */}
        <section>
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-50">Notes récentes</h2>
          <div className="space-y-2">
            {recentNotes.map(note => (
              <Card
                key={note.id}
                onClick={() => router.push(`/viz/${note.id}`)}
                className="cursor-pointer hover:border-plume-500/50 transition-all hover:shadow-lg"
              >
                <CardContent className="p-3 flex justify-between items-center">
                  <span className="font-medium truncate">{note.title}</span>
                  <span className="text-sm text-gray-600 dark:text-gray-500 ml-4 flex-shrink-0">
                    {note.updated_at > note.created_at
                      ? `Modifié le ${note.updated_at.toLocaleDateString('fr-FR')}`
                      : `Créé le ${note.created_at.toLocaleDateString('fr-FR')}`
                    }
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
          <Button
            variant="outline"
            className="w-full mt-3"
            onClick={() => router.push('/archives/all')}
          >
            Voir tout
          </Button>
        </section>

        {/* Section 2: Search */}
        <section>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500 dark:text-gray-400" />
            <Input
              type="search"
              placeholder="Rechercher dans vos notes..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>

          {isSearching && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mt-3">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Recherche en cours...</span>
            </div>
          )}

          {searchResults.length > 0 && (
            <div className="mt-3 space-y-2">
              {searchResults.map(note => (
                <Card
                  key={note.id}
                  onClick={() => router.push(`/viz/${note.id}`)}
                  className="cursor-pointer hover:border-mimir-500/50 transition-all"
                >
                  <CardContent className="p-3">
                    <h3 className="font-medium mb-1">{note.title}</h3>
                    {note.snippet && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {note.snippet}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Section 3: Upload */}
        <section>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <h2 className="text-lg font-semibold">
                {uploadMode === 'text' ? 'Upload text' : 'Upload audio'}
              </h2>
              <div className="flex">
                <Button
                  variant={uploadMode === 'text' ? 'default' : 'outline'}
                  onClick={() => setUploadMode('text')}
                  className="rounded-r-none border-r-0"
                  size="sm"
                >
                  Texte
                </Button>
                <Button
                  variant={uploadMode === 'audio' ? 'default' : 'outline'}
                  onClick={() => setUploadMode('audio')}
                  className="rounded-l-none"
                  size="sm"
                >
                  Audio
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {uploadMode === 'text' ? (
                <>
                  <Textarea
                    placeholder="Collez votre texte ici..."
                    rows={8}
                    value={textContent}
                    onChange={(e) => setTextContent(e.target.value)}
                  />

                  <div>
                    <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">
                      Informations contextuelles (optionnel)
                    </label>
                    <div className="flex gap-2">
                      <Textarea
                        placeholder="Ajoutez du contexte..."
                        rows={2}
                        value={textContext}
                        onChange={(e) => setTextContext(e.target.value)}
                        className="flex-1"
                      />
                      <div className="flex flex-col gap-2">
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={handleContextAudioRecord}
                          title="Enregistrer contexte audio"
                        >
                          <Mic className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={handleContextAudioUpload}
                          title="Upload fichier audio contexte"
                        >
                          <UploadIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={handleTextUpload}
                    disabled={!textContent.trim() || isUploading}
                    className="w-full"
                  >
                    {isUploading ? 'Création...' : 'Créer la note'}
                  </Button>
                </>
              ) : (
                <>
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center">
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleAudioFileSelect}
                    className="hidden"
                    id="audio-upload"
                  />
                  <label htmlFor="audio-upload" className="cursor-pointer">
                    <UploadIcon className="h-8 w-8 mx-auto mb-2 text-gray-500 dark:text-gray-400" />
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {audioFile ? audioFile.name : 'Cliquez ou glissez un fichier audio'}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-500 mt-1">
                      Formats : mp3, wav, m4a, webm, ogg
                    </p>
                  </label>
                </div>

                <div>
                  <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">
                    Informations contextuelles (optionnel)
                  </label>
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Ajoutez du contexte..."
                      rows={2}
                      value={audioContext}
                      onChange={(e) => setAudioContext(e.target.value)}
                      className="flex-1"
                    />
                    <div className="flex flex-col gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={handleContextAudioRecord}
                        title="Enregistrer contexte audio"
                      >
                        <Mic className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={handleContextAudioUpload}
                        title="Upload fichier audio contexte"
                      >
                        <UploadIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={handleAudioUpload}
                  disabled={!audioFile || isUploading}
                  className="w-full"
                >
                  {isUploading ? 'Création...' : 'Créer la note'}
                </Button>

                {isUploading && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Transcription et traitement en cours...</span>
                  </div>
                )}
              </>
            )}
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
      <ArchivesPage />
    </ProtectedRoute>
  )
}
