# Multi-stage Dockerfile for Plume & Mimir Backend
# Optimized for Render deployment

# =============================================================================
# Base Python image with dependencies
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# =============================================================================
# Dependencies stage
# =============================================================================
FROM base as dependencies

# Copy requirements first (for better caching)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =============================================================================
# Production stage
# =============================================================================
FROM base as production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY backend/ ./backend/
COPY database/ ./database/
COPY .env.example ./

# Set ownership and permissions
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command for production
CMD ["gunicorn", "backend.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--host", "0.0.0.0", "--port", "8000", "--access-logfile", "-", "--error-logfile", "-"]

# =============================================================================
# Development stage
# =============================================================================
FROM dependencies as development

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-mock httpx black isort mypy

# Copy application code
COPY backend/ ./backend/
COPY database/ ./database/
COPY .env.example ./

# Development command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]