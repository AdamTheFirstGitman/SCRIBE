"""
Embeddings service using OpenAI text-embedding models
Handles text vectorization with intelligent caching and batch processing
"""

import asyncio
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from openai import AsyncOpenAI
import numpy as np

from config import settings
from services.cache import cache_manager
from services.storage import supabase_client
from utils.logger import get_logger, performance_logger, cost_logger

logger = get_logger(__name__)

class EmbeddingService:
    """
    Text embedding service with intelligent chunking, caching, and batch processing
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.max_chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP

    async def create_embeddings_for_note(
        self,
        note_id: str,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create embeddings for a note with intelligent chunking

        Args:
            note_id: ID of the note
            content: Text content to embed
            title: Optional note title
            metadata: Additional metadata

        Returns:
            List of created embedding records
        """
        start_time = time.time()

        try:
            # Clean up existing embeddings for this note
            await supabase_client.delete_embeddings_for_note(note_id)

            # Chunk the content
            chunks = await self._chunk_text_intelligently(content, title)

            if not chunks:
                logger.warning("No chunks created for note", note_id=note_id)
                return []

            # Create embeddings for chunks
            embeddings_data = []

            for i, chunk in enumerate(chunks):
                try:
                    # Get embedding for chunk
                    embedding_vector = await self.get_embedding(chunk["text"])

                    # Prepare embedding record
                    embedding_record = {
                        "note_id": note_id,
                        "chunk_text": chunk["text"],
                        "embedding": embedding_vector,
                        "chunk_index": i,
                        "chunk_metadata": {
                            **chunk.get("metadata", {}),
                            "chunk_type": chunk.get("type", "content"),
                            "chunk_size": len(chunk["text"]),
                            "position": chunk.get("position", i),
                            **(metadata or {})
                        }
                    }

                    embeddings_data.append(embedding_record)

                except Exception as e:
                    logger.error("Failed to create embedding for chunk",
                                note_id=note_id,
                                chunk_index=i,
                                error=str(e))
                    continue

            # Store embeddings in database
            if embeddings_data:
                stored_embeddings = await supabase_client.create_embeddings(embeddings_data)

                processing_time_ms = (time.time() - start_time) * 1000

                logger.info("Embeddings created for note",
                           note_id=note_id,
                           chunks_created=len(stored_embeddings),
                           processing_time_ms=processing_time_ms)

                return stored_embeddings
            else:
                logger.warning("No embeddings created for note", note_id=note_id)
                return []

        except Exception as e:
            logger.error("Failed to create embeddings for note",
                        note_id=note_id,
                        error=str(e))
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text with caching

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        start_time = time.time()

        try:
            # Check cache first
            cached_embedding = await cache_manager.get_embedding(text)
            if cached_embedding:
                logger.debug("Using cached embedding", text_length=len(text))
                return cached_embedding

            # Clean and prepare text
            cleaned_text = self._clean_text_for_embedding(text)

            if not cleaned_text.strip():
                logger.warning("Empty text after cleaning")
                # Return zero vector
                return [0.0] * self.dimensions

            # Call OpenAI API
            response = await self.client.embeddings.create(
                input=[cleaned_text],
                model=self.model
            )

            embedding_vector = response.data[0].embedding

            # Validate embedding
            if len(embedding_vector) != self.dimensions:
                raise ValueError(f"Unexpected embedding dimensions: {len(embedding_vector)} (expected {self.dimensions})")

            processing_time_ms = (time.time() - start_time) * 1000

            # Log performance
            performance_logger.log_api_call(
                service="openai_embeddings",
                endpoint="embeddings",
                duration_ms=processing_time_ms,
                status_code=200
            )

            # Log costs
            cost = self._calculate_embedding_cost(len(cleaned_text))
            cost_logger.log_token_usage(
                service="openai",
                model=self.model,
                tokens=len(cleaned_text) // 4,  # Rough token estimate
                cost=cost
            )

            # Cache embedding
            await cache_manager.set_embedding(text, embedding_vector)

            logger.debug("Embedding created",
                        text_length=len(text),
                        processing_time_ms=processing_time_ms)

            return embedding_vector

        except Exception as e:
            logger.error("Failed to create embedding",
                        text_length=len(text),
                        error=str(e))
            raise

    async def batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        start_time = time.time()

        try:
            if not texts:
                return []

            # Check cache for existing embeddings
            embeddings = []
            uncached_indices = []
            uncached_texts = []

            for i, text in enumerate(texts):
                cached = await cache_manager.get_embedding(text)
                if cached:
                    embeddings.append(cached)
                else:
                    embeddings.append(None)  # Placeholder
                    uncached_indices.append(i)
                    uncached_texts.append(self._clean_text_for_embedding(text))

            # Process uncached texts in batches
            if uncached_texts:
                batch_size = 100  # OpenAI batch limit
                new_embeddings = []

                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i + batch_size]

                    # Call OpenAI API for batch
                    response = await self.client.embeddings.create(
                        input=batch,
                        model=self.model
                    )

                    batch_embeddings = [item.embedding for item in response.data]
                    new_embeddings.extend(batch_embeddings)

                    # Cache new embeddings
                    for j, embedding in enumerate(batch_embeddings):
                        original_text = texts[uncached_indices[i + j]]
                        await cache_manager.set_embedding(original_text, embedding)

                # Fill in the new embeddings
                for i, embedding in enumerate(new_embeddings):
                    original_index = uncached_indices[i]
                    embeddings[original_index] = embedding

            processing_time_ms = (time.time() - start_time) * 1000

            logger.info("Batch embeddings completed",
                       total_texts=len(texts),
                       cached_count=len(texts) - len(uncached_texts),
                       new_embeddings=len(uncached_texts),
                       processing_time_ms=processing_time_ms)

            return embeddings

        except Exception as e:
            logger.error("Batch embedding failed", count=len(texts), error=str(e))
            raise

    async def _chunk_text_intelligently(self, content: str, title: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Intelligently chunk text for optimal embedding

        Args:
            content: Text content to chunk
            title: Optional title to include in first chunk

        Returns:
            List of chunk dictionaries
        """
        try:
            chunks = []

            # Include title in first chunk if provided
            if title:
                title_chunk = {
                    "text": f"# {title}\n\n" + content[:self.max_chunk_size - len(title) - 4],
                    "type": "title_content",
                    "metadata": {"has_title": True},
                    "position": 0
                }
                chunks.append(title_chunk)

                # Adjust remaining content
                remaining_content = content[len(title_chunk["text"]) - len(title) - 4:]
            else:
                remaining_content = content

            # Chunk remaining content
            content_chunks = await self._chunk_by_semantic_boundaries(remaining_content)

            for i, chunk_text in enumerate(content_chunks):
                chunk = {
                    "text": chunk_text,
                    "type": "content",
                    "metadata": {"semantic_chunk": True},
                    "position": len(chunks) + i
                }
                chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error("Text chunking failed", error=str(e))
            # Fallback to simple chunking
            return await self._chunk_by_size(content)

    async def _chunk_by_semantic_boundaries(self, text: str) -> List[str]:
        """
        Chunk text by semantic boundaries (paragraphs, sentences)

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        try:
            # Split by double newlines (paragraphs)
            paragraphs = text.split('\n\n')
            chunks = []
            current_chunk = ""

            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue

                # Check if adding this paragraph exceeds chunk size
                potential_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph

                if len(potential_chunk) <= self.max_chunk_size:
                    current_chunk = potential_chunk
                else:
                    # Save current chunk if it exists
                    if current_chunk:
                        chunks.append(current_chunk)

                    # Handle long paragraphs
                    if len(paragraph) > self.max_chunk_size:
                        # Split long paragraph by sentences
                        sentence_chunks = await self._chunk_by_sentences(paragraph)
                        chunks.extend(sentence_chunks[:-1])  # All but last
                        current_chunk = sentence_chunks[-1] if sentence_chunks else ""
                    else:
                        current_chunk = paragraph

            # Add final chunk
            if current_chunk:
                chunks.append(current_chunk)

            return chunks

        except Exception as e:
            logger.warning("Semantic chunking failed, using size-based", error=str(e))
            return await self._chunk_by_size(text)

    async def _chunk_by_sentences(self, text: str) -> List[str]:
        """
        Chunk text by sentences when paragraphs are too long

        Args:
            text: Text to chunk

        Returns:
            List of sentence-based chunks
        """
        # Simple sentence splitting (could be enhanced with NLP)
        sentences = re.split(r'[.!?]+\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            potential_chunk = current_chunk + (" " if current_chunk else "") + sentence + "."

            if len(potential_chunk) <= self.max_chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                # Handle very long sentences
                if len(sentence) > self.max_chunk_size:
                    # Split by words as last resort
                    word_chunks = await self._chunk_by_size(sentence)
                    chunks.extend(word_chunks[:-1])
                    current_chunk = word_chunks[-1] + "." if word_chunks else ""
                else:
                    current_chunk = sentence + "."

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def _chunk_by_size(self, text: str) -> List[str]:
        """
        Fallback chunking by size with overlap

        Args:
            text: Text to chunk

        Returns:
            List of size-based chunks
        """
        if len(text) <= self.max_chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.max_chunk_size

            # Try to break at word boundary
            if end < len(text):
                # Find last space before the limit
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap
            if start <= 0:
                start = end

        return chunks

    def _clean_text_for_embedding(self, text: str) -> str:
        """
        Clean text for optimal embedding quality

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove very long sequences of repeated characters
        text = re.sub(r'(.)\1{10,}', r'\1\1\1', text)

        # Trim
        text = text.strip()

        # Limit length for API
        if len(text) > 8000:  # Conservative limit
            text = text[:8000]
            # Try to end at a word boundary
            last_space = text.rfind(' ')
            if last_space > 7000:
                text = text[:last_space]

        return text

    def _calculate_embedding_cost(self, text_length: int) -> float:
        """
        Calculate embedding cost in EUR

        Args:
            text_length: Length of text in characters

        Returns:
            Cost in EUR
        """
        # OpenAI text-embedding-3-large pricing: $0.00013 per 1K tokens
        estimated_tokens = text_length / 4  # Rough estimation
        cost_per_1k_tokens_usd = 0.00013

        cost_usd = (estimated_tokens / 1000) * cost_per_1k_tokens_usd
        cost_eur = cost_usd * 0.92  # Convert to EUR

        return round(cost_eur, 6)

    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.78
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using query embedding

        Args:
            query_embedding: Query vector
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of similar documents with scores
        """
        try:
            results = await supabase_client.vector_search(
                query_embedding=query_embedding,
                match_threshold=similarity_threshold,
                match_count=limit
            )

            logger.debug("Similarity search completed",
                        results_found=len(results),
                        threshold=similarity_threshold)

            return results

        except Exception as e:
            logger.error("Similarity search failed", error=str(e))
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        try:
            # Get basic stats from database
            performance_stats = await supabase_client.get_performance_stats()

            stats = {
                "model": self.model,
                "dimensions": self.dimensions,
                "max_chunk_size": self.max_chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "database_stats": performance_stats.get("embeddings", {}),
                "cache_stats": await cache_manager.get_stats()
            }

            return stats

        except Exception as e:
            logger.error("Failed to get embedding stats", error=str(e))
            return {"error": str(e)}

# Global embedding service instance
embedding_service = EmbeddingService()