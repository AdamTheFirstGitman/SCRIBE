'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Switch } from '../../components/ui/switch'
import {
  Upload,
  FileText,
  Eye,
  Code,
  Loader2,
  CheckCircle,
  AlertCircle,
  X
} from 'lucide-react'
import { uploadDocument } from '../../lib/api/upload'
import { OfflineUtils } from '../../lib/offline'
import { toast } from 'sonner'

interface ProcessedDocument {
  id: string
  title: string
  filename: string
  content_text: string
  content_html: string
  file_size: number
  processing_status: string
  metadata: {
    word_count: number
    char_count: number
    has_links: boolean
    has_structure: boolean
    topics: string[]
  }
  tags: string[]
}

export default function UploadPage() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [processedDocs, setProcessedDocs] = useState<ProcessedDocument[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<ProcessedDocument | null>(null)
  const [viewMode, setViewMode] = useState<'text' | 'html'>('text')
  const [customTitle, setCustomTitle] = useState('')
  const [customTags, setCustomTags] = useState('')
  const [isOnline, setIsOnline] = useState(true)

  // Handle network status changes - SSR safe
  React.useEffect(() => {
    // Set initial value after component mounts (client-side only)
    setIsOnline(navigator.onLine)

    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Drag & drop handling
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setUploadedFiles(prev => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md', '.markdown'],
      'application/json': ['.json']
    },
    maxFiles: 5,
    maxSize: 10 * 1024 * 1024 // 10MB
  })

  // Remove file from upload queue
  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Upload and process files
  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return

    setIsUploading(true)

    try {
      if (!isOnline) {
        // Handle offline upload
        for (const file of uploadedFiles) {
          const title = customTitle || file.name.replace(/\.[^/.]+$/, '')
          const tags = customTags.split(',').map(tag => tag.trim()).filter(Boolean)

          await OfflineUtils.handleOfflineUpload(file, title, tags)
        }

        // Clear upload queue
        setUploadedFiles([])
        setCustomTitle('')
        setCustomTags('')

        toast.success(`${uploadedFiles.length} fichier(s) sauvé(s) pour synchronisation`)
        return
      }

      // Handle online upload
      const results = await Promise.all(
        uploadedFiles.map(async (file) => {
          const formData = new FormData()
          formData.append('file', file)

          if (customTitle) formData.append('title', customTitle)
          if (customTags) formData.append('tags', customTags)

          return uploadDocument(formData)
        })
      )

      // Add processed documents to state
      setProcessedDocs(prev => [...prev, ...results])

      // Clear upload queue
      setUploadedFiles([])
      setCustomTitle('')
      setCustomTags('')

      toast.success(`${results.length} fichier(s) traité(s) avec succès`)

      // Auto-select first document for preview
      if (results.length > 0 && !selectedDoc) {
        setSelectedDoc(results[0] as ProcessedDocument)
      }

    } catch (error) {
      console.error('Upload failed:', error)
      toast.error("Échec de l'upload")
    } finally {
      setIsUploading(false)
    }
  }

  // Toggle between text and HTML view
  const toggleViewMode = () => {
    setViewMode(prev => prev === 'text' ? 'html' : 'text')
  }

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="min-h-screen bg-gray-950 p-4">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-50">📄 Upload de Documents</h1>
          <p className="text-gray-400">
            Uploadez vos notes texte pour alimenter Mimir
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Upload Section */}
          <div className="space-y-4">

            {/* Drag & Drop Zone */}
            <Card className="border-gray-800 bg-gray-900">
              <CardHeader>
                <CardTitle className="text-gray-50 flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Zone d'Upload
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  {...getRootProps()}
                  className={`
                    border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                    ${isDragActive
                      ? 'border-plume-500 bg-plume-500/10'
                      : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'
                    }
                  `}
                >
                  <input {...getInputProps()} />
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />

                  {isDragActive ? (
                    <p className="text-plume-400 text-lg font-medium">
                      Déposez vos fichiers ici...
                    </p>
                  ) : (
                    <>
                      <p className="text-gray-300 text-lg font-medium mb-2">
                        Glissez & déposez vos fichiers texte
                      </p>
                      <p className="text-gray-500 text-sm">
                        Formats: .txt, .md, .json • Max 10MB
                      </p>
                      <Button variant="outline" className="mt-4">
                        Parcourir les fichiers
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Upload Queue */}
            {uploadedFiles.length > 0 && (
              <Card className="border-gray-800 bg-gray-900">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-gray-50">
                    Fichiers à traiter ({uploadedFiles.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">

                  {/* Custom metadata inputs */}
                  <div className="grid grid-cols-1 gap-3 p-4 bg-gray-800 rounded-lg">
                    <div>
                      <Label className="text-gray-300">Titre personnalisé (optionnel)</Label>
                      <Input
                        value={customTitle}
                        onChange={(e) => setCustomTitle(e.target.value)}
                        placeholder="Titre du document..."
                        className="bg-gray-700 border-gray-600 text-gray-100"
                      />
                    </div>
                    <div>
                      <Label className="text-gray-300">Tags (séparés par des virgules)</Label>
                      <Input
                        value={customTags}
                        onChange={(e) => setCustomTags(e.target.value)}
                        placeholder="hackathon, AI, notes..."
                        className="bg-gray-700 border-gray-600 text-gray-100"
                      />
                    </div>
                  </div>

                  {/* File list */}
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="h-4 w-4 text-blue-400" />
                        <div>
                          <p className="text-gray-200 text-sm font-medium">{file.name}</p>
                          <p className="text-gray-500 text-xs">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}

                  {/* Offline indicator */}
                  {!isOnline && (
                    <div className="p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
                      <div className="flex items-center gap-2 text-yellow-400">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm font-medium">Mode hors ligne</span>
                      </div>
                      <p className="text-yellow-300 text-xs mt-1">
                        Les fichiers seront sauvegardés et synchronisés automatiquement lors de la reconnexion.
                      </p>
                    </div>
                  )}

                  <Button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className={`w-full ${
                      isOnline
                        ? 'bg-plume-600 hover:bg-plume-700'
                        : 'bg-yellow-600 hover:bg-yellow-700'
                    }`}
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        {isOnline ? 'Traitement en cours...' : 'Sauvegarde...'}
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        {isOnline ? 'Traiter les fichiers' : 'Sauvegarder pour plus tard'}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Processed Documents List */}
            {processedDocs.length > 0 && (
              <Card className="border-gray-800 bg-gray-900">
                <CardHeader>
                  <CardTitle className="text-gray-50 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    Documents traités ({processedDocs.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {processedDocs.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className={`
                        p-3 rounded-lg cursor-pointer transition-colors
                        ${selectedDoc?.id === doc.id
                          ? 'bg-plume-600/20 border border-plume-500'
                          : 'bg-gray-800 hover:bg-gray-700'
                        }
                      `}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-gray-200 font-medium text-sm">{doc.title}</p>
                          <p className="text-gray-500 text-xs">{doc.filename}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            {doc.metadata.word_count} mots
                          </Badge>
                          {doc.metadata.has_links && (
                            <Badge variant="outline" className="text-xs">
                              Liens
                            </Badge>
                          )}
                        </div>
                      </div>
                      {doc.tags.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {doc.tags.map((tag, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Preview Section */}
          <div className="space-y-4">
            {selectedDoc ? (
              <Card className="border-gray-800 bg-gray-900">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-gray-50">{selectedDoc.title}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Label className="text-gray-400 text-sm">HTML</Label>
                      <Switch
                        checked={viewMode === 'html'}
                        onCheckedChange={toggleViewMode}
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={toggleViewMode}
                        className="ml-2"
                      >
                        {viewMode === 'text' ? (
                          <>
                            <Code className="h-4 w-4 mr-1" />
                            HTML
                          </>
                        ) : (
                          <>
                            <FileText className="h-4 w-4 mr-1" />
                            TEXT
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Document stats */}
                  <div className="flex gap-4 text-sm text-gray-400">
                    <span>{selectedDoc.metadata.word_count} mots</span>
                    <span>{selectedDoc.metadata.char_count} caractères</span>
                    <span>{formatFileSize(selectedDoc.file_size)}</span>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="max-h-96 overflow-y-auto">
                    {viewMode === 'text' ? (
                      <pre className="text-gray-300 text-sm whitespace-pre-wrap font-mono bg-gray-800 p-4 rounded-lg">
                        {selectedDoc.content_text}
                      </pre>
                    ) : (
                      <div
                        className="prose prose-invert prose-sm max-w-none"
                        dangerouslySetInnerHTML={{ __html: selectedDoc.content_html }}
                      />
                    )}
                  </div>

                  {/* Topics/Keywords */}
                  {selectedDoc.metadata.topics.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <p className="text-gray-400 text-sm mb-2">Sujets détectés:</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedDoc.metadata.topics.map((topic, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center text-gray-500">
                    <Eye className="h-12 w-12 mx-auto mb-4" />
                    <p>Sélectionnez un document pour le prévisualiser</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}