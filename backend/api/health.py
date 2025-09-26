"""
Health check endpoints for Plume & Mimir API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import time
import asyncio
from datetime import datetime

from models.schemas import HealthCheck, DetailedHealthCheck
from config import settings
from services.storage import supabase_client
from services.cache import cache_manager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthCheck)
async def basic_health_check():
    """Basic health check endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.VERSION,
        services={"api": "running"}
    )

@router.get("/health/detailed", response_model=DetailedHealthCheck)
async def detailed_health_check():
    """Detailed health check with service status"""
    start_time = time.time()

    # Check all services
    services_status = await _check_all_services()

    # Determine overall status
    overall_status = "healthy"
    if any(status["status"] != "healthy" for status in services_status.values()):
        overall_status = "degraded"

    # Check if any service is completely down
    if any(status["status"] == "unhealthy" for status in services_status.values()):
        overall_status = "unhealthy"

    processing_time = (time.time() - start_time) * 1000

    return DetailedHealthCheck(
        status=overall_status,
        version=settings.VERSION,
        services={"api": "running"},
        database=services_status.get("database", {}),
        cache=services_status.get("cache", {}),
        external_apis=services_status.get("external_apis", {}),
        performance={
            "health_check_time_ms": round(processing_time, 2),
            "memory_usage": await _get_memory_usage(),
        }
    )

@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    try:
        # Check critical services
        db_status = await _check_database()

        if db_status["status"] != "healthy":
            raise HTTPException(status_code=503, detail="Database not ready")

        return {"status": "ready", "timestamp": datetime.utcnow()}

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    try:
        # Basic application health
        return {"status": "alive", "timestamp": datetime.utcnow(), "version": settings.VERSION}

    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Service not alive")

async def _check_all_services() -> Dict[str, Dict[str, Any]]:
    """Check status of all services"""
    services = {}

    # Run checks in parallel
    tasks = {
        "database": _check_database(),
        "cache": _check_cache(),
        "external_apis": _check_external_apis(),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for service_name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            services[service_name] = {
                "status": "unhealthy",
                "error": str(result),
                "timestamp": datetime.utcnow()
            }
        else:
            services[service_name] = result

    return services

async def _check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    start_time = time.time()

    try:
        # Test connection with a simple query
        success = await supabase_client.test_connection()

        response_time = (time.time() - start_time) * 1000

        if success:
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "timestamp": datetime.utcnow()
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": "Connection test failed",
                "timestamp": datetime.utcnow()
            }

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "response_time_ms": round(response_time, 2),
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

async def _check_cache() -> Dict[str, Any]:
    """Check cache connectivity"""
    start_time = time.time()

    try:
        # Test cache with a simple operation
        test_key = f"health_check_{int(time.time())}"
        test_value = "ok"

        await cache_manager.set(test_key, test_value, ttl=10)
        result = await cache_manager.get(test_key)
        await cache_manager.delete(test_key)

        response_time = (time.time() - start_time) * 1000

        if result == test_value:
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "timestamp": datetime.utcnow()
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": "Cache operation failed",
                "timestamp": datetime.utcnow()
            }

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return {
            "status": "degraded",  # Cache is not critical, so degraded instead of unhealthy
            "response_time_ms": round(response_time, 2),
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

async def _check_external_apis() -> Dict[str, Any]:
    """Check external API connectivity"""
    start_time = time.time()

    api_status = {}

    # Check Claude API (critical)
    if settings.CLAUDE_API_KEY:
        try:
            # This would be a real API check in production
            # For now, just check if the key is configured
            api_status["claude"] = {
                "status": "configured",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            api_status["claude"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }

    # Check OpenAI API (critical for embeddings and transcription)
    if settings.OPENAI_API_KEY:
        try:
            api_status["openai"] = {
                "status": "configured",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            api_status["openai"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }

    # Check optional APIs
    optional_apis = [
        ("perplexity", settings.PERPLEXITY_API_KEY),
        ("tavily", settings.TAVILY_API_KEY),
        ("cohere", settings.COHERE_API_KEY),
    ]

    for api_name, api_key in optional_apis:
        if api_key:
            api_status[api_name] = {
                "status": "configured",
                "timestamp": datetime.utcnow()
            }
        else:
            api_status[api_name] = {
                "status": "not_configured",
                "timestamp": datetime.utcnow()
            }

    response_time = (time.time() - start_time) * 1000

    # Determine overall API status
    critical_apis = ["claude", "openai"]
    critical_status = [api_status.get(api, {}).get("status") for api in critical_apis]

    if all(status == "configured" for status in critical_status):
        overall_status = "healthy"
    elif any(status == "error" for status in critical_status):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "response_time_ms": round(response_time, 2),
        "apis": api_status,
        "timestamp": datetime.utcnow()
    }

async def _get_memory_usage() -> Dict[str, Any]:
    """Get memory usage information"""
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}