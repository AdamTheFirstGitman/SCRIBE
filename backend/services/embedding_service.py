"""
Embedding Service
Handles text embedding generation for Mimir RAG system using OpenAI
"""

import asyncio
import hashlib
from typing import List, Dict, Optional, Tuple
import openai
import redis
import json
import numpy as np
from datetime import datetime, timedelta
import os
from ..config import get_settings

class EmbeddingService:
    """
    Service for generating and caching text embeddings
    Uses OpenAI text-embedding-3-large model (1536 dimensions)
    """

    def __init__(self):
        settings = get_settings()

        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        # Initialize Redis for caching
        self.redis_client = None
        if settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis_client = None

        # Configuration
        self.model = "text-embedding-3-large"
        self.dimensions = 1536
        self.cache_ttl = settings.CACHE_TTL_EMBEDDINGS  # 7 days default
        self.batch_size = 100  # OpenAI batch limit

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Check cache first
        if self.redis_client:
            cached = await self._get_cached_embedding(text)
            if cached:
                return cached

        # Generate embedding via OpenAI
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model=self.model,
                dimensions=self.dimensions
            )

            embedding = response.data[0].embedding

            # Cache the result
            if self.redis_client:
                await self._cache_embedding(text, embedding)

            return embedding

        except Exception as e:
            raise Exception(f"OpenAI embedding generation failed: {str(e)}")

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors in same order as input
        """

        if not texts:
            return []

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = await self._process_batch(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    async def _process_batch(self, texts: List[str]) -> List[List[float]]:
        """Process a single batch of texts"""

        # Check cache for each text
        cache_results = []
        uncached_texts = []
        uncached_indices = []

        for idx, text in enumerate(texts):
            if self.redis_client:
                cached = await self._get_cached_embedding(text)
                if cached:
                    cache_results.append((idx, cached))
                    continue

            uncached_texts.append(text)
            uncached_indices.append(idx)

        # Generate embeddings for uncached texts
        new_embeddings = []
        if uncached_texts:
            try:
                response = await self.openai_client.embeddings.create(
                    input=uncached_texts,
                    model=self.model,
                    dimensions=self.dimensions
                )

                new_embeddings = [item.embedding for item in response.data]

                # Cache new embeddings
                if self.redis_client:
                    for text, embedding in zip(uncached_texts, new_embeddings):
                        await self._cache_embedding(text, embedding)

            except Exception as e:
                raise Exception(f"Batch embedding generation failed: {str(e)}")

        # Combine cached and new embeddings in correct order
        result = [None] * len(texts)

        # Place cached embeddings
        for idx, embedding in cache_results:
            result[idx] = embedding

        # Place new embeddings
        for uncached_idx, embedding in zip(uncached_indices, new_embeddings):
            result[uncached_idx] = embedding

        return result

    async def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve embedding from cache"""

        if not self.redis_client:
            return None

        try:
            cache_key = self._get_cache_key(text)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    async def _cache_embedding(self, text: str, embedding: List[float]):
        """Store embedding in cache"""

        if not self.redis_client:
            return

        try:
            cache_key = self._get_cache_key(text)
            cache_data = json.dumps(embedding)

            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                cache_data
            )

        except Exception as e:
            print(f"Cache storage error: {e}")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""

        # Create hash of text for consistent key
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{self.model}:{text_hash}"

    async def get_embedding_stats(self) -> Dict:
        """Get embedding service statistics"""

        stats = {
            "model": self.model,
            "dimensions": self.dimensions,
            "cache_enabled": self.redis_client is not None,
            "cache_ttl_hours": self.cache_ttl / 3600,
            "batch_size": self.batch_size
        }

        # Add cache stats if available
        if self.redis_client:
            try:
                # Count embedding cache keys
                cache_keys = self.redis_client.keys("embedding:*")
                stats["cached_embeddings"] = len(cache_keys)

                # Estimate cache memory usage
                cache_info = self.redis_client.info("memory")
                stats["cache_memory_mb"] = round(
                    cache_info.get("used_memory", 0) / 1024 / 1024, 2
                )

            except Exception as e:
                stats["cache_error"] = str(e)

        return stats

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (-1 to 1)
        """

        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have same dimensions")

        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def find_most_similar(self,
                         query_embedding: List[float],
                         candidates: List[Tuple[str, List[float]]],
                         top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find most similar embeddings to query

        Args:
            query_embedding: Query vector
            candidates: List of (text, embedding) tuples
            top_k: Number of results to return

        Returns:
            List of (text, similarity_score) tuples, sorted by similarity
        """

        similarities = []

        for text, embedding in candidates:
            similarity = self.calculate_similarity(query_embedding, embedding)
            similarities.append((text, similarity))

        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    async def clear_cache(self):
        """Clear all cached embeddings"""

        if not self.redis_client:
            return {"message": "No cache to clear"}

        try:
            # Find all embedding cache keys
            keys = self.redis_client.keys("embedding:*")

            if keys:
                # Delete all embedding keys
                self.redis_client.delete(*keys)
                return {"message": f"Cleared {len(keys)} cached embeddings"}
            else:
                return {"message": "No cached embeddings found"}

        except Exception as e:
            raise Exception(f"Cache clearing failed: {str(e)}")

# Helper function for dependency injection
_embedding_service_instance = None

def get_embedding_service() -> EmbeddingService:
    """Get singleton instance of embedding service"""
    global _embedding_service_instance

    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()

    return _embedding_service_instance