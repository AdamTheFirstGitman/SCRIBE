"""
Plume & Mimir FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from config import settings
from utils.logger import setup_logging, get_logger
from api import chat, archive, search, health
from services.cache import cache_manager
from services.storage import supabase_client

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Plume & Mimir backend", version=settings.VERSION)

    # Initialize services
    try:
        # Test database connection
        await supabase_client.test_connection()
        logger.info("Database connection established")

        # Initialize cache
        await cache_manager.initialize()
        logger.info("Cache system initialized")

        # Warm up critical services
        # TODO: Add service warm-up if needed

        logger.info("Backend startup completed successfully")
    except Exception as e:
        logger.error("Failed to initialize backend services", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Plume & Mimir backend")
    try:
        await cache_manager.close()
        # Close other connections if needed
        logger.info("Backend shutdown completed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# Create FastAPI application
app = FastAPI(
    title="Plume & Mimir API",
    description="AI-powered knowledge management system with intelligent agents",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)

# Trusted hosts middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Request processing middleware"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Add request ID to headers
    request.state.request_id = request_id

    # Log request
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent", ""),
        client_ip=get_remote_address(request)
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))

        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2)
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time

        # Log error
        logger.error(
            "Request failed",
            request_id=request_id,
            error=str(e),
            process_time_ms=round(process_time * 1000, 2),
            exc_info=True
        )

        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "timestamp": time.time()
            },
            headers={
                "X-Request-ID": request_id,
                "X-Response-Time": str(round(process_time * 1000, 2))
            }
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    logger.warning(
        "HTTP exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id,
            "timestamp": time.time()
        },
        headers={"X-Request-ID": request_id}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    logger.error(
        "Unhandled exception",
        request_id=request_id,
        error=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "timestamp": time.time()
        },
        headers={"X-Request-ID": request_id}
    )

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time(), "version": settings.VERSION}

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Plume & Mimir API",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health"
    }

# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(archive.router, prefix="/api/v1", tags=["Archive"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # We use our own logging
        access_log=False  # We log requests in middleware
    )