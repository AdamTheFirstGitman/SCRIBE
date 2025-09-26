"""
Comprehensive Error Handling and Recovery System
Production-ready error handling with logging, recovery, and user-friendly responses
"""

import logging
import traceback
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    INTERNAL = "internal"
    NETWORK = "network"
    TIMEOUT = "timeout"

@dataclass
class ErrorContext:
    """Error context with recovery information"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    user_message: str
    recovery_suggestions: List[str]
    timestamp: datetime
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.error_counts = {}
        self.circuit_breakers = {}

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, 'request_id', 'unknown')

        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            return await self._handle_http_exception(e, request, request_id)

        except asyncio.TimeoutError:
            return await self._handle_timeout_error(request, request_id)

        except Exception as e:
            return await self._handle_unexpected_error(e, request, request_id)

    async def _handle_http_exception(self, exc: HTTPException, request: Request, request_id: str):
        """Handle known HTTP exceptions"""

        error_context = self._create_error_context(
            error_id=f"http_{exc.status_code}_{request_id}",
            category=self._categorize_http_error(exc.status_code),
            severity=self._assess_severity(exc.status_code),
            message=str(exc.detail),
            details={"status_code": exc.status_code, "headers": dict(exc.headers or {})},
            user_message=self._get_user_friendly_message(exc.status_code, str(exc.detail)),
            recovery_suggestions=self._get_recovery_suggestions(exc.status_code),
            request_id=request_id,
            endpoint=request.url.path
        )

        await self._log_error(error_context)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "id": error_context.error_id,
                    "message": error_context.user_message,
                    "category": error_context.category,
                    "suggestions": error_context.recovery_suggestions,
                    "timestamp": error_context.timestamp.isoformat()
                },
                "request_id": request_id
            },
            headers=exc.headers
        )

    async def _handle_timeout_error(self, request: Request, request_id: str):
        """Handle timeout errors"""

        error_context = self._create_error_context(
            error_id=f"timeout_{request_id}",
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            message="Request timeout",
            details={"endpoint": request.url.path, "method": request.method},
            user_message="La requête a pris trop de temps. Veuillez réessayer.",
            recovery_suggestions=[
                "Réessayez dans quelques secondes",
                "Vérifiez votre connexion internet",
                "Contactez le support si le problème persiste"
            ],
            request_id=request_id,
            endpoint=request.url.path
        )

        await self._log_error(error_context)

        return JSONResponse(
            status_code=408,
            content={
                "error": {
                    "id": error_context.error_id,
                    "message": error_context.user_message,
                    "category": error_context.category,
                    "suggestions": error_context.recovery_suggestions,
                    "timestamp": error_context.timestamp.isoformat()
                },
                "request_id": request_id
            }
        )

    async def _handle_unexpected_error(self, exc: Exception, request: Request, request_id: str):
        """Handle unexpected errors"""

        error_context = self._create_error_context(
            error_id=f"internal_{request_id}",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            message=str(exc),
            details={
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "endpoint": request.url.path,
                "method": request.method
            },
            user_message="Une erreur inattendue s'est produite. Notre équipe a été notifiée.",
            recovery_suggestions=[
                "Réessayez dans quelques instants",
                "Vérifiez que vos données sont correctes",
                "Contactez le support si le problème persiste"
            ],
            request_id=request_id,
            endpoint=request.url.path
        )

        await self._log_error(error_context)
        await self._notify_critical_error(error_context)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "id": error_context.error_id,
                    "message": error_context.user_message,
                    "category": error_context.category,
                    "suggestions": error_context.recovery_suggestions,
                    "timestamp": error_context.timestamp.isoformat()
                },
                "request_id": request_id
            }
        )

    def _create_error_context(self, **kwargs) -> ErrorContext:
        """Create error context with defaults"""
        defaults = {
            'timestamp': datetime.now(),
            'details': {},
            'recovery_suggestions': []
        }
        defaults.update(kwargs)
        return ErrorContext(**defaults)

    def _categorize_http_error(self, status_code: int) -> ErrorCategory:
        """Categorize HTTP error by status code"""
        categories = {
            400: ErrorCategory.VALIDATION,
            401: ErrorCategory.AUTHENTICATION,
            403: ErrorCategory.AUTHORIZATION,
            429: ErrorCategory.RATE_LIMIT,
            500: ErrorCategory.INTERNAL,
            502: ErrorCategory.EXTERNAL_API,
            503: ErrorCategory.EXTERNAL_API,
            504: ErrorCategory.TIMEOUT
        }
        return categories.get(status_code, ErrorCategory.INTERNAL)

    def _assess_severity(self, status_code: int) -> ErrorSeverity:
        """Assess error severity"""
        if status_code < 400:
            return ErrorSeverity.LOW
        elif status_code < 500:
            return ErrorSeverity.MEDIUM
        elif status_code < 600:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.CRITICAL

    def _get_user_friendly_message(self, status_code: int, detail: str) -> str:
        """Get user-friendly error message"""
        messages = {
            400: "Les données envoyées ne sont pas valides.",
            401: "Authentification requise.",
            403: "Vous n'avez pas l'autorisation d'accéder à cette ressource.",
            404: "La ressource demandée n'a pas été trouvée.",
            429: "Trop de requêtes. Veuillez patienter avant de réessayer.",
            500: "Erreur interne du serveur.",
            502: "Service temporairement indisponible.",
            503: "Service en maintenance.",
            504: "Le service met trop de temps à répondre."
        }
        return messages.get(status_code, detail)

    def _get_recovery_suggestions(self, status_code: int) -> List[str]:
        """Get recovery suggestions by error type"""
        suggestions = {
            400: ["Vérifiez le format de vos données", "Consultez la documentation API"],
            401: ["Vérifiez vos identifiants", "Reconnectez-vous"],
            403: ["Contactez l'administrateur pour obtenir les permissions"],
            404: ["Vérifiez l'URL", "La ressource a peut-être été supprimée"],
            429: ["Attendez quelques minutes", "Réduisez la fréquence de vos requêtes"],
            500: ["Réessayez dans quelques instants", "Contactez le support"],
            502: ["Réessayez dans quelques minutes", "Le service externe est indisponible"],
            503: ["Le service est en maintenance", "Réessayez plus tard"],
            504: ["Le service est lent", "Réessayez avec une requête plus simple"]
        }
        return suggestions.get(status_code, ["Réessayez plus tard", "Contactez le support"])

    async def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level"""
        log_data = {
            'error_id': error_context.error_id,
            'category': error_context.category,
            'severity': error_context.severity,
            'endpoint': error_context.endpoint,
            'request_id': error_context.request_id,
            'user_id': error_context.user_id,
            'message': error_context.message,
            'timestamp': error_context.timestamp.isoformat()
        }

        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error", extra=log_data)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error("High severity error", extra=log_data)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error", extra=log_data)
        else:
            logger.info("Low severity error", extra=log_data)

    async def _notify_critical_error(self, error_context: ErrorContext):
        """Notify team of critical errors"""
        # In production, integrate with alerting systems
        # (Slack, email, PagerDuty, etc.)
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.critical(f"ALERT: Critical error {error_context.error_id}")

# Retry mechanism with exponential backoff
class RetryableError(Exception):
    """Exception that should be retried"""
    pass

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.0, exceptions: tuple = (Exception,)):
    """Decorator to retry function on failure"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        break

                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)

            raise last_exception

        return wrapper
    return decorator

# Circuit breaker pattern
class CircuitBreaker:
    """Circuit breaker for external services"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""

        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        if self.last_failure_time is None:
            return True

        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

# External API error handling
class ExternalAPIHandler:
    """Handle errors from external APIs (OpenAI, Perplexity, etc.)"""

    def __init__(self):
        self.circuit_breakers = {
            "openai": CircuitBreaker(),
            "perplexity": CircuitBreaker(),
            "tavily": CircuitBreaker()
        }

    @retry_on_failure(max_retries=2, exceptions=(httpx.RequestError, httpx.TimeoutException))
    async def call_openai_api(self, func, *args, **kwargs):
        """Call OpenAI API with error handling"""
        try:
            return await self.circuit_breakers["openai"].call(func, *args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RetryableError("Rate limit exceeded")
            elif e.response.status_code >= 500:
                raise RetryableError("Server error")
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"OpenAI API error: {e.response.text}"
                )

    @retry_on_failure(max_retries=2)
    async def call_perplexity_api(self, func, *args, **kwargs):
        """Call Perplexity API with error handling"""
        try:
            return await self.circuit_breakers["perplexity"].call(func, *args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RetryableError("Rate limit exceeded")
            elif e.response.status_code >= 500:
                raise RetryableError("Server error")
            else:
                raise HTTPException(
                    status_code=502,
                    detail="Perplexity search temporarily unavailable"
                )

# Error tracking and analytics
class ErrorTracker:
    """Track errors for analytics and improvements"""

    def __init__(self):
        self.errors = []
        self.error_counts = {}

    def track_error(self, error_context: ErrorContext):
        """Track error for analytics"""
        self.errors.append(error_context)

        # Keep only recent errors (last 1000)
        if len(self.errors) > 1000:
            self.errors = self.errors[-1000:]

        # Update counts
        key = f"{error_context.category}_{error_context.severity}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.errors:
            return {"total_errors": 0}

        recent_errors = [
            e for e in self.errors
            if e.timestamp > datetime.now() - timedelta(hours=24)
        ]

        categories = {}
        severities = {}

        for error in recent_errors:
            categories[error.category] = categories.get(error.category, 0) + 1
            severities[error.severity] = severities.get(error.severity, 0) + 1

        return {
            "total_errors_24h": len(recent_errors),
            "by_category": categories,
            "by_severity": severities,
            "most_common_errors": self._get_most_common_errors(recent_errors),
            "error_rate": len(recent_errors) / 24  # errors per hour
        }

    def _get_most_common_errors(self, errors: List[ErrorContext]) -> List[Dict[str, Any]]:
        """Get most common error patterns"""
        error_patterns = {}

        for error in errors:
            pattern = f"{error.category}:{error.endpoint}"
            if pattern not in error_patterns:
                error_patterns[pattern] = {
                    "pattern": pattern,
                    "count": 0,
                    "latest_message": error.message
                }
            error_patterns[pattern]["count"] += 1

        # Sort by count and return top 5
        sorted_patterns = sorted(
            error_patterns.values(),
            key=lambda x: x["count"],
            reverse=True
        )

        return sorted_patterns[:5]

# Global instances
external_api_handler = ExternalAPIHandler()
error_tracker = ErrorTracker()