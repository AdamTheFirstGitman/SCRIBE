/**
 * Upload API Client
 * Handles document upload and processing requests
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface DocumentResponse {
  id: string
  filename: string
  title: string
  content_text: string
  content_html: string
  file_type: string
  file_size: number
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  upload_source: string
  created_at: string
  updated_at?: string
  tags: string[]
  metadata: {
    word_count: number
    char_count: number
    links: string[]
    headers: string[]
    topics: string[]
    has_code: boolean
    has_links: boolean
    has_structure: boolean
  }
  is_deleted: boolean
}

export interface DocumentPreview {
  id: string
  filename: string
  title: string
  file_type: string
  file_size: number
  processing_status: string
  created_at: string
  tags: string[]
  word_count?: number
  has_links: boolean
  has_structure: boolean
}

export interface UploadStats {
  total_documents: number
  total_size_bytes: number
  total_size_mb: number
  by_file_type: Record<string, number>
  by_processing_status: Record<string, number>
  recent_uploads: DocumentPreview[]
  average_file_size?: number
}

class UploadAPIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'UploadAPIError'
  }
}

/**
 * Upload a document for processing
 */
export async function uploadDocument(formData: FormData): Promise<DocumentResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/document`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let browser set it with boundary
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new UploadAPIError(
        response.status,
        errorData?.detail || `Upload failed: ${response.statusText}`,
        errorData
      )
    }

    const data = await response.json()
    return data

  } catch (error) {
    if (error instanceof UploadAPIError) {
      throw error
    }

    throw new UploadAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Get a document by ID
 */
export async function getDocument(documentId: string): Promise<DocumentResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/document/${documentId}`)

    if (!response.ok) {
      if (response.status === 404) {
        throw new UploadAPIError(404, 'Document not found')
      }

      const errorData = await response.json().catch(() => null)
      throw new UploadAPIError(
        response.status,
        errorData?.detail || `Failed to get document: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof UploadAPIError) {
      throw error
    }

    throw new UploadAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * List documents with optional filtering and pagination
 */
export async function listDocuments(
  options: {
    limit?: number
    offset?: number
    tag?: string
  } = {}
): Promise<DocumentResponse[]> {
  try {
    const params = new URLSearchParams()
    if (options.limit) params.set('limit', options.limit.toString())
    if (options.offset) params.set('offset', options.offset.toString())
    if (options.tag) params.set('tag', options.tag)

    const url = `${API_BASE_URL}/upload/documents?${params}`
    const response = await fetch(url)

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new UploadAPIError(
        response.status,
        errorData?.detail || `Failed to list documents: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof UploadAPIError) {
      throw error
    }

    throw new UploadAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Delete a document
 */
export async function deleteDocument(documentId: string): Promise<{ message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/document/${documentId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      if (response.status === 404) {
        throw new UploadAPIError(404, 'Document not found')
      }

      const errorData = await response.json().catch(() => null)
      throw new UploadAPIError(
        response.status,
        errorData?.detail || `Failed to delete document: ${response.statusText}`,
        errorData
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof UploadAPIError) {
      throw error
    }

    throw new UploadAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Get upload service health status
 */
export async function getUploadHealth(): Promise<{
  status: string
  service: string
  max_file_size_mb: number
  supported_formats: string[]
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/health`)

    if (!response.ok) {
      throw new UploadAPIError(
        response.status,
        `Health check failed: ${response.statusText}`
      )
    }

    return await response.json()

  } catch (error) {
    if (error instanceof UploadAPIError) {
      throw error
    }

    throw new UploadAPIError(
      0,
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

/**
 * Upload multiple files with progress tracking
 */
export async function uploadMultipleDocuments(
  files: File[],
  options: {
    onProgress?: (completed: number, total: number) => void
    onFileComplete?: (file: File, result: DocumentResponse) => void
    onFileError?: (file: File, error: Error) => void
  } = {}
): Promise<DocumentResponse[]> {
  const results: DocumentResponse[] = []
  let completed = 0

  for (const file of files) {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const result = await uploadDocument(formData)
      results.push(result)

      completed++
      options.onProgress?.(completed, files.length)
      options.onFileComplete?.(file, result)

    } catch (error) {
      const uploadError = error instanceof UploadAPIError ? error : new UploadAPIError(
        0,
        `Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`
      )

      options.onFileError?.(file, uploadError)

      // Continue with other files instead of failing completely
      completed++
      options.onProgress?.(completed, files.length)
    }
  }

  return results
}

/**
 * Utility function to validate file before upload
 */
export function validateFile(file: File): { valid: boolean; error?: string } {
  const maxSize = 10 * 1024 * 1024 // 10MB
  const allowedTypes = ['text/plain', 'text/markdown', 'application/json']
  const allowedExtensions = ['.txt', '.md', '.markdown', '.json']

  // Check file size
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large. Maximum size: ${maxSize / 1024 / 1024}MB`
    }
  }

  // Check file type
  const fileName = file.name.toLowerCase()
  const hasValidType = allowedTypes.includes(file.type)
  const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext))

  if (!hasValidType && !hasValidExtension) {
    return {
      valid: false,
      error: `Unsupported file type. Allowed: ${allowedTypes.join(', ')}`
    }
  }

  return { valid: true }
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

/**
 * Extract filename without extension
 */
export function getFileBaseName(filename: string): string {
  const lastDotIndex = filename.lastIndexOf('.')
  if (lastDotIndex === -1) return filename
  return filename.substring(0, lastDotIndex)
}

// Export error class for external use
export { UploadAPIError }