"""
Performance Optimization Middleware
Caching, compression, and optimization for production
"""

import time
import gzip
import json
import hashlib
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
import asyncio

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import redis.asyncio as redis

from ..config import get_settings

class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Performance optimization middleware with:
    - Response caching
    - Gzip compression
    - Request deduplication
    - Performance metrics
    """

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.settings = get_settings()
        self.redis_client = redis_client
        self.metrics = {
            'requests_total': 0,
            'response_times': [],
            'cache_hits': 0,
            'cache_misses': 0
        }

    async def dispatch(self, request: Request, call_next):
        """Process request with performance optimizations"""

        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')

        # Check cache for GET requests
        if request.method == "GET" and self.redis_client:
            cached_response = await self._get_cached_response(request)
            if cached_response:
                self.metrics['cache_hits'] += 1
                return cached_response

        # Process request
        response = await call_next(request)
        processing_time = time.time() - start_time

        # Update metrics
        self.metrics['requests_total'] += 1
        self.metrics['response_times'].append(processing_time)

        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]

        # Cache GET responses if successful
        if (request.method == "GET" and
            response.status_code == 200 and
            self.redis_client):
            await self._cache_response(request, response)

        # Add performance headers
        response.headers["X-Response-Time"] = str(round(processing_time * 1000, 2))
        response.headers["X-Cache"] = "HIT" if getattr(response, '_from_cache', False) else "MISS"

        # Compress response if beneficial
        if self._should_compress(request, response):
            response = await self._compress_response(response)

        return response

    async def _get_cached_response(self, request: Request) -> Optional[Response]:
        """Get cached response if available"""
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)

                response = JSONResponse(
                    content=data['content'],
                    status_code=data['status_code'],
                    headers=data['headers']
                )
                response._from_cache = True
                return response

        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    async def _cache_response(self, request: Request, response: Response):
        """Cache response for future requests"""
        try:
            # Only cache certain endpoints
            cacheable_paths = ['/api/upload/health', '/api/chat/health', '/health']

            if not any(request.url.path.startswith(path) for path in cacheable_paths):
                return

            cache_key = self._generate_cache_key(request)

            # Extract response data
            response_data = {
                'content': response.body.decode() if hasattr(response, 'body') else '',
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }

            # Cache for 5 minutes
            await self.redis_client.setex(
                cache_key,
                300,  # 5 minutes
                json.dumps(response_data)
            )

        except Exception as e:
            print(f"Cache storage error: {e}")

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        key_data = f"{request.method}:{request.url.path}:{request.url.query}"
        return f"scribe:cache:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _should_compress(self, request: Request, response: Response) -> bool:
        """Check if response should be compressed"""

        # Check accept-encoding header
        accept_encoding = request.headers.get('accept-encoding', '')
        if 'gzip' not in accept_encoding:
            return False

        # Check content type
        content_type = response.headers.get('content-type', '')
        compressible_types = [
            'application/json',
            'text/html',
            'text/plain',
            'application/javascript',
            'text/css'
        ]

        if not any(ct in content_type for ct in compressible_types):
            return False

        # Check content length
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) < 1000:
            return False  # Don't compress small responses

        return True

    async def _compress_response(self, response: Response) -> Response:
        """Compress response with gzip"""
        try:
            if hasattr(response, 'body'):
                compressed_body = gzip.compress(response.body)

                response.headers['content-encoding'] = 'gzip'
                response.headers['content-length'] = str(len(compressed_body))
                response.body = compressed_body

        except Exception as e:
            print(f"Compression error: {e}")

        return response

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        response_times = self.metrics['response_times']

        return {
            'requests_total': self.metrics['requests_total'],
            'cache_hit_rate': (
                self.metrics['cache_hits'] /
                max(self.metrics['cache_hits'] + self.metrics['cache_misses'], 1)
            ),
            'avg_response_time_ms': (
                sum(response_times) / len(response_times) * 1000
                if response_times else 0
            ),
            'p95_response_time_ms': (
                sorted(response_times)[int(len(response_times) * 0.95)] * 1000
                if response_times else 0
            ),
            'timestamp': datetime.now().isoformat()
        }

# CDN and Static Asset Optimization
class StaticOptimizationMiddleware(BaseHTTPMiddleware):
    """Optimize static assets delivery"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add caching headers for static assets
        if self._is_static_asset(request.url.path):
            # Cache static assets for 1 year
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            response.headers["ETag"] = f'"{hash(request.url.path)}"'

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

    def _is_static_asset(self, path: str) -> bool:
        """Check if path is a static asset"""
        static_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2']
        return any(path.endswith(ext) for ext in static_extensions)

# Request deduplication for expensive operations
class DeduplicationMiddleware:
    """Prevent duplicate expensive requests"""

    def __init__(self):
        self.active_requests: Dict[str, asyncio.Event] = {}
        self.request_results: Dict[str, Any] = {}

    def deduplicate(self, key_func=None):
        """Decorator to deduplicate function calls"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate deduplication key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                # Check if request is already in progress
                if key in self.active_requests:
                    # Wait for ongoing request
                    await self.active_requests[key].wait()
                    return self.request_results.get(key)

                # Create event for this request
                self.active_requests[key] = asyncio.Event()

                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    self.request_results[key] = result

                    # Notify waiting requests
                    self.active_requests[key].set()

                    # Cleanup after a delay
                    asyncio.create_task(self._cleanup_after_delay(key, 60))  # 1 minute

                    return result

                except Exception as e:
                    # Notify waiters about the error
                    self.active_requests[key].set()
                    raise e

            return wrapper
        return decorator

    async def _cleanup_after_delay(self, key: str, delay: int):
        """Clean up request tracking after delay"""
        await asyncio.sleep(delay)
        self.active_requests.pop(key, None)
        self.request_results.pop(key, None)

# Global instances
deduplicator = DeduplicationMiddleware()

# Performance monitoring
class PerformanceMonitor:
    """Monitor and alert on performance issues"""

    def __init__(self):
        self.thresholds = {
            'max_response_time': 5.0,  # 5 seconds
            'max_memory_usage': 0.8,   # 80%
            'min_cache_hit_rate': 0.5  # 50%
        }
        self.alerts = []

    async def check_performance(self, metrics: Dict[str, Any]):
        """Check performance metrics against thresholds"""
        alerts = []

        # Check response time
        if metrics.get('avg_response_time_ms', 0) > self.thresholds['max_response_time'] * 1000:
            alerts.append({
                'type': 'slow_response',
                'message': f"Average response time exceeded {self.thresholds['max_response_time']}s",
                'value': metrics['avg_response_time_ms']
            })

        # Check cache hit rate
        if metrics.get('cache_hit_rate', 1.0) < self.thresholds['min_cache_hit_rate']:
            alerts.append({
                'type': 'low_cache_hit_rate',
                'message': f"Cache hit rate below {self.thresholds['min_cache_hit_rate']*100}%",
                'value': metrics['cache_hit_rate']
            })

        # Store alerts
        self.alerts.extend(alerts)

        # Keep only recent alerts
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.alerts = [alert for alert in self.alerts
                      if alert.get('timestamp', datetime.now()) > cutoff_time]

        return alerts

    def get_alerts(self) -> list:
        """Get current performance alerts"""
        return self.alerts

# Global performance monitor
performance_monitor = PerformanceMonitor()