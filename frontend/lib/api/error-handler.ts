/**
 * API Error Handling
 * Provides centralized error handling for API requests
 */

export class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

/**
 * Handle API response and throw APIError if not ok
 */
export async function handleResponse<T = any>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = response.statusText
    let errorDetails = null

    try {
      const errorData = await response.json()
      errorMessage = errorData.detail || errorData.message || errorMessage
      errorDetails = errorData
    } catch (e) {
      // Failed to parse error JSON, use statusText
    }

    throw new APIError(response.status, errorMessage, errorDetails)
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return {} as T
  }

  try {
    return await response.json()
  } catch (e) {
    throw new APIError(500, 'Failed to parse response JSON')
  }
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof APIError) {
    switch (error.status) {
      case 400:
        return `Requête invalide: ${error.message}`
      case 401:
        return 'Session expirée. Veuillez vous reconnecter.'
      case 403:
        return 'Accès refusé.'
      case 404:
        return 'Ressource introuvable.'
      case 500:
        return 'Erreur serveur. Réessayez plus tard.'
      default:
        return error.message
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Une erreur est survenue'
}
