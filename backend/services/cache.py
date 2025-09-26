"""
Multi-level cache system for Plume & Mimir
L1: In-memory cache (LRU)
L2: Redis cache (if available)
L3: Database (handled by storage service)
"""

import asyncio
import json
import hashlib
import time
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from collections import OrderedDict
import pickle
import redis.asyncio as redis

from ..config import settings
from ..utils.logger import get_logger, performance_logger

logger = get_logger(__name__)

class LRUCache:
    """In-memory LRU cache (L1)"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.ttl_cache: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get item from LRU cache"""
        if key not in self.cache:
            return None

        # Check TTL
        if key in self.ttl_cache:
            if datetime.utcnow() > self.ttl_cache[key]:
                self.delete(key)
                return None

        # Move to end (mark as recently used)
        value = self.cache.pop(key)
        self.cache[key] = value
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set item in LRU cache"""
        if key in self.cache:
            # Update existing item
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used item
            oldest_key = next(iter(self.cache))
            self.delete(oldest_key)

        self.cache[key] = value

        # Set TTL if provided
        if ttl:
            self.ttl_cache[key] = datetime.utcnow() + timedelta(seconds=ttl)
        elif key in self.ttl_cache:
            del self.ttl_cache[key]

    def delete(self, key: str):
        """Delete item from LRU cache"""
        self.cache.pop(key, None)
        self.ttl_cache.pop(key, None)

    def clear(self):
        """Clear all items from cache"""
        self.cache.clear()
        self.ttl_cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def cleanup_expired(self):
        """Remove expired items"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, expiry in self.ttl_cache.items()
            if current_time > expiry
        ]

        for key in expired_keys:
            self.delete(key)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")

class CacheManager:
    """Multi-level cache manager"""

    def __init__(self):
        self.l1_cache = LRUCache(max_size=1000)
        self.redis_client: Optional[redis.Redis] = None
        self.redis_available = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize cache system"""
        try:
            # Try to connect to Redis (L2)
            if settings.REDIS_URL or settings.REDIS_HOST:
                self.redis_client = redis.Redis(**settings.redis_connection_kwargs)

                # Test Redis connection
                await self.redis_client.ping()
                self.redis_available = True
                logger.info("Redis cache (L2) initialized successfully")
            else:
                logger.info("Redis not configured, using only L1 cache")

            # Start cleanup task for L1 cache
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("Cache manager initialized successfully")

        except Exception as e:
            logger.warning("Failed to initialize Redis cache", error=str(e))
            self.redis_available = False
            logger.info("Falling back to L1 cache only")

    async def close(self):
        """Close cache connections"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Cache manager closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache (L1 -> L2)"""
        start_time = time.time()
        cache_hit = False
        level = None

        try:
            # Try L1 cache first
            value = self.l1_cache.get(key)
            if value is not None:
                cache_hit = True
                level = "L1"
                return value

            # Try L2 cache (Redis)
            if self.redis_available and self.redis_client:
                try:
                    cached_data = await self.redis_client.get(key)
                    if cached_data:
                        value = pickle.loads(cached_data)
                        # Store in L1 for faster access next time
                        self.l1_cache.set(key, value)
                        cache_hit = True
                        level = "L2"
                        return value
                except Exception as e:
                    logger.warning("Redis get failed", key=key, error=str(e))

            return None

        finally:
            duration = (time.time() - start_time) * 1000
            performance_logger.log_cache_operation(
                f"get_{level or 'miss'}", cache_hit, duration, key=key
            )

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set item in cache (L1 and L2)"""
        start_time = time.time()

        try:
            # Store in L1 cache
            self.l1_cache.set(key, value, ttl)

            # Store in L2 cache (Redis) if available
            if self.redis_available and self.redis_client:
                try:
                    serialized_value = pickle.dumps(value)
                    if ttl:
                        await self.redis_client.setex(key, ttl, serialized_value)
                    else:
                        await self.redis_client.set(key, serialized_value)
                except Exception as e:
                    logger.warning("Redis set failed", key=key, error=str(e))

        finally:
            duration = (time.time() - start_time) * 1000
            performance_logger.log_cache_operation("set", True, duration, key=key)

    async def delete(self, key: str):
        """Delete item from cache (L1 and L2)"""
        start_time = time.time()

        try:
            # Delete from L1
            self.l1_cache.delete(key)

            # Delete from L2 (Redis) if available
            if self.redis_available and self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception as e:
                    logger.warning("Redis delete failed", key=key, error=str(e))

        finally:
            duration = (time.time() - start_time) * 1000
            performance_logger.log_cache_operation("delete", True, duration, key=key)

    async def clear(self, pattern: Optional[str] = None):
        """Clear cache items"""
        start_time = time.time()

        try:
            if pattern:
                # Clear specific pattern
                if self.redis_available and self.redis_client:
                    try:
                        keys = await self.redis_client.keys(pattern)
                        if keys:
                            await self.redis_client.delete(*keys)
                    except Exception as e:
                        logger.warning("Redis pattern clear failed", pattern=pattern, error=str(e))

                # For L1 cache, we need to check each key manually
                keys_to_delete = [k for k in self.l1_cache.cache.keys() if self._match_pattern(k, pattern)]
                for key in keys_to_delete:
                    self.l1_cache.delete(key)
            else:
                # Clear all
                self.l1_cache.clear()
                if self.redis_available and self.redis_client:
                    try:
                        await self.redis_client.flushdb()
                    except Exception as e:
                        logger.warning("Redis clear failed", error=str(e))

        finally:
            duration = (time.time() - start_time) * 1000
            performance_logger.log_cache_operation("clear", True, duration, pattern=pattern)

    # =============================================================================
    # SPECIALIZED CACHE METHODS
    # =============================================================================

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        key = self._embedding_key(text)
        return await self.get(key)

    async def set_embedding(self, text: str, embedding: List[float]):
        """Cache embedding for text"""
        key = self._embedding_key(text)
        await self.set(key, embedding, ttl=settings.CACHE_TTL_EMBEDDINGS)

    async def get_transcription(self, audio_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached transcription"""
        key = f"transcription:{audio_hash}"
        return await self.get(key)

    async def set_transcription(self, audio_hash: str, transcription: Dict[str, Any]):
        """Cache transcription result"""
        key = f"transcription:{audio_hash}"
        await self.set(key, transcription, ttl=settings.CACHE_TTL_TRANSCRIPTIONS)

    async def get_llm_response(self, prompt_hash: str, model: str) -> Optional[str]:
        """Get cached LLM response"""
        key = f"llm:{model}:{prompt_hash}"
        return await self.get(key)

    async def set_llm_response(self, prompt_hash: str, model: str, response: str):
        """Cache LLM response"""
        key = f"llm:{model}:{prompt_hash}"
        await self.set(key, response, ttl=settings.CACHE_TTL_LLM_RESPONSES)

    async def get_search_results(self, query_hash: str, search_type: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        key = f"search:{search_type}:{query_hash}"
        return await self.get(key)

    async def set_search_results(self, query_hash: str, search_type: str, results: List[Dict[str, Any]]):
        """Cache search results"""
        key = f"search:{search_type}:{query_hash}"
        # Search results have shorter TTL
        await self.set(key, results, ttl=3600)  # 1 hour

    # =============================================================================
    # CACHE INVALIDATION
    # =============================================================================

    async def invalidate_note_cache(self, note_id: str):
        """Invalidate all cache entries related to a note"""
        patterns_to_clear = [
            f"search:*",  # Clear all search results
            f"embedding:*",  # Clear embeddings (they might have changed)
        ]

        for pattern in patterns_to_clear:
            await self.clear(pattern)

        logger.info("Cache invalidated for note", note_id=note_id)

    async def invalidate_search_cache(self):
        """Invalidate all search-related cache"""
        await self.clear("search:*")
        logger.info("Search cache invalidated")

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def _embedding_key(self, text: str) -> str:
        """Generate cache key for embedding"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{text_hash}"

    def _prompt_hash(self, prompt: str, model: str, **kwargs) -> str:
        """Generate hash for prompt + parameters"""
        content = f"{prompt}:{model}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def _query_hash(self, query: str, **kwargs) -> str:
        """Generate hash for search query + parameters"""
        content = f"{query}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys"""
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        return key == pattern

    async def _cleanup_loop(self):
        """Background task to cleanup expired L1 cache items"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                self.l1_cache.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cache cleanup failed", error=str(e))

    # =============================================================================
    # MONITORING & STATS
    # =============================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "l1_cache": {
                "size": self.l1_cache.size(),
                "max_size": self.l1_cache.max_size,
                "utilization": self.l1_cache.size() / self.l1_cache.max_size * 100
            },
            "l2_cache": {
                "available": self.redis_available
            }
        }

        if self.redis_available and self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
                stats["l2_cache"].update({
                    "memory_used": redis_info.get("used_memory_human", "N/A"),
                    "memory_peak": redis_info.get("used_memory_peak_human", "N/A"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                })

                # Calculate hit rate
                hits = redis_info.get("keyspace_hits", 0)
                misses = redis_info.get("keyspace_misses", 0)
                total = hits + misses
                if total > 0:
                    stats["l2_cache"]["hit_rate"] = (hits / total) * 100
                else:
                    stats["l2_cache"]["hit_rate"] = 0

            except Exception as e:
                logger.warning("Failed to get Redis stats", error=str(e))

        return stats

# Global cache manager instance
cache_manager = CacheManager()