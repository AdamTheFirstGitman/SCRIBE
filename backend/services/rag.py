"""
RAG (Retrieval-Augmented Generation) service
Advanced knowledge retrieval with hybrid search and re-ranking
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

from config import settings
from services.embeddings import embedding_service
from services.storage import supabase_client
from services.cache import cache_manager
from utils.logger import get_logger, performance_logger

logger = get_logger(__name__)

class RAGService:
    """
    Advanced RAG service with hybrid search, re-ranking, and intelligent context management
    """

    def __init__(self):
        self.default_top_k = settings.RAG_TOP_K
        self.default_threshold = settings.RAG_SIMILARITY_THRESHOLD
        self.max_context_tokens = 8000  # Maximum context size for LLM

    async def search_knowledge(
        self,
        query: str,
        limit: int = None,
        similarity_threshold: float = None,
        search_type: str = "hybrid",
        include_context_ids: Optional[List[str]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using advanced RAG techniques

        Args:
            query: Search query
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score
            search_type: Type of search ("vector", "fulltext", "hybrid")
            include_context_ids: Specific note IDs to include in search
            rerank: Whether to apply re-ranking

        Returns:
            List of relevant documents with scores and metadata
        """
        start_time = time.time()
        limit = limit or self.default_top_k
        similarity_threshold = similarity_threshold or self.default_threshold

        try:
            # Check cache first
            cache_key = self._generate_search_cache_key(
                query, limit, similarity_threshold, search_type
            )
            cached_results = await cache_manager.get_search_results(cache_key, search_type)

            if cached_results:
                logger.info("Using cached search results",
                           query_length=len(query),
                           results_count=len(cached_results))
                return cached_results

            # Perform search based on type
            if search_type == "vector":
                results = await self._vector_search(query, limit, similarity_threshold)
            elif search_type == "fulltext":
                results = await self._fulltext_search(query, limit)
            else:  # hybrid
                results = await self._hybrid_search(query, limit, similarity_threshold)

            # Filter by context IDs if specified
            if include_context_ids:
                results = [r for r in results if r.get("note_id") in include_context_ids]

            # Re-rank results for better relevance
            if rerank and len(results) > 1:
                results = await self._rerank_results(query, results)

            # Enhance results with metadata
            enhanced_results = await self._enhance_results_metadata(results, query)

            # Log search analytics
            await self._log_search_analytics(query, len(enhanced_results), time.time() - start_time)

            # Cache results
            await cache_manager.set_search_results(cache_key, search_type, enhanced_results)

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info("Knowledge search completed",
                       query_length=len(query),
                       search_type=search_type,
                       results_found=len(enhanced_results),
                       processing_time_ms=processing_time_ms)

            return enhanced_results

        except Exception as e:
            logger.error("Knowledge search failed",
                        query=query[:100],
                        search_type=search_type,
                        error=str(e))
            return []

    async def _vector_search(
        self,
        query: str,
        limit: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        try:
            # Get query embedding
            query_embedding = await embedding_service.get_embedding(query)

            # Search using vector similarity
            results = await supabase_client.vector_search(
                query_embedding=query_embedding,
                match_threshold=similarity_threshold,
                match_count=limit * 2  # Get more to allow for filtering
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.get("id"),
                    "note_id": result.get("note_id"),
                    "chunk_text": result.get("chunk_text"),
                    "similarity_score": result.get("similarity", 0.0),
                    "relevance_score": result.get("similarity", 0.0),
                    "search_type": "vector"
                })

            return formatted_results[:limit]

        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            return []

    async def _fulltext_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform full-text search"""
        try:
            # Use Supabase full-text search via notes table
            results = await supabase_client.list_notes(
                search_query=query,
                limit=limit,
                order_by="created_at",
                order_direction="desc"
            )

            notes, _ = results

            # Convert notes to search result format
            formatted_results = []
            for i, note in enumerate(notes):
                # Create chunks from note content for consistency
                content = note.get("content", "")
                if len(content) > 500:
                    content = content[:500] + "..."

                formatted_results.append({
                    "id": f"fulltext_{note['id']}_{i}",
                    "note_id": note["id"],
                    "title": note.get("title", ""),
                    "chunk_text": content,
                    "similarity_score": 0.8,  # Default for fulltext
                    "relevance_score": 0.8,
                    "search_type": "fulltext",
                    "created_at": note.get("created_at")
                })

            return formatted_results

        except Exception as e:
            logger.error("Fulltext search failed", error=str(e))
            return []

    async def _hybrid_search(
        self,
        query: str,
        limit: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and full-text"""
        try:
            # Get query embedding for vector search
            query_embedding = await embedding_service.get_embedding(query)

            # Use Supabase hybrid search RPC
            results = await supabase_client.hybrid_search(
                query_text=query,
                query_embedding=query_embedding,
                match_threshold=similarity_threshold,
                match_count=limit * 2  # Get more to allow for re-ranking
            )

            # Format results
            formatted_results = []
            for result in results:
                # Combine vector similarity and text rank for hybrid score
                similarity = result.get("similarity", 0.0)
                text_rank = result.get("rank", 0.0)

                # Weighted hybrid score (70% vector, 30% text)
                hybrid_score = (similarity * 0.7) + (min(text_rank, 1.0) * 0.3)

                formatted_results.append({
                    "id": result.get("id"),
                    "note_id": result.get("note_id"),
                    "title": result.get("title", ""),
                    "chunk_text": result.get("chunk_text"),
                    "similarity_score": similarity,
                    "text_rank": text_rank,
                    "relevance_score": hybrid_score,
                    "search_type": "hybrid"
                })

            # Sort by hybrid score
            formatted_results.sort(key=lambda x: x["relevance_score"], reverse=True)

            return formatted_results[:limit]

        except Exception as e:
            logger.error("Hybrid search failed", error=str(e))
            # Fallback to vector search
            return await self._vector_search(query, limit, similarity_threshold)

    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results for better relevance using query-document similarity
        """
        try:
            if len(results) <= 1:
                return results

            # Simple re-ranking based on query-document text similarity
            reranked_results = []

            query_words = set(query.lower().split())

            for result in results:
                chunk_text = result.get("chunk_text", "").lower()
                chunk_words = set(chunk_text.split())

                # Calculate text overlap score
                if len(query_words) > 0:
                    overlap = len(query_words.intersection(chunk_words))
                    text_similarity = overlap / len(query_words)
                else:
                    text_similarity = 0.0

                # Combine with existing relevance score
                original_score = result.get("relevance_score", 0.0)
                boosted_score = (original_score * 0.8) + (text_similarity * 0.2)

                result["relevance_score"] = boosted_score
                result["text_similarity"] = text_similarity
                reranked_results.append(result)

            # Sort by boosted score
            reranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)

            logger.debug("Results re-ranked",
                        original_count=len(results),
                        reranked_count=len(reranked_results))

            return reranked_results

        except Exception as e:
            logger.warning("Re-ranking failed, returning original results", error=str(e))
            return results

    async def _enhance_results_metadata(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Enhance results with additional metadata"""
        try:
            enhanced = []

            for result in results:
                # Add query context
                result["query"] = query
                result["retrieved_at"] = datetime.utcnow().isoformat()

                # Add content preview with highlighting
                chunk_text = result.get("chunk_text", "")
                if chunk_text:
                    result["content_preview"] = self._create_content_preview(
                        chunk_text, query
                    )

                # Add relevance explanation
                result["relevance_explanation"] = self._generate_relevance_explanation(
                    result, query
                )

                enhanced.append(result)

            return enhanced

        except Exception as e:
            logger.warning("Failed to enhance results metadata", error=str(e))
            return results

    def _create_content_preview(self, content: str, query: str, max_length: int = 200) -> str:
        """Create a content preview with query term highlighting"""
        try:
            # Find query terms in content
            query_terms = query.lower().split()
            content_lower = content.lower()

            # Find best position to start preview (around query terms)
            best_start = 0
            for term in query_terms:
                pos = content_lower.find(term)
                if pos != -1:
                    # Start a bit before the term
                    best_start = max(0, pos - 50)
                    break

            # Create preview
            preview = content[best_start:best_start + max_length]

            # Add ellipsis if truncated
            if best_start > 0:
                preview = "..." + preview
            if len(content) > best_start + max_length:
                preview = preview + "..."

            return preview.strip()

        except Exception as e:
            logger.warning("Failed to create content preview", error=str(e))
            return content[:max_length] + "..." if len(content) > max_length else content

    def _generate_relevance_explanation(
        self,
        result: Dict[str, Any],
        query: str
    ) -> str:
        """Generate explanation of why this result is relevant"""
        try:
            explanations = []

            similarity_score = result.get("similarity_score", 0.0)
            if similarity_score > 0.9:
                explanations.append("Very high semantic similarity")
            elif similarity_score > 0.8:
                explanations.append("High semantic similarity")
            elif similarity_score > 0.7:
                explanations.append("Good semantic similarity")

            text_similarity = result.get("text_similarity", 0.0)
            if text_similarity > 0.5:
                explanations.append("Strong keyword overlap")
            elif text_similarity > 0.3:
                explanations.append("Good keyword overlap")

            search_type = result.get("search_type", "")
            if search_type == "hybrid":
                explanations.append("Matched by both semantic and keyword search")

            if not explanations:
                explanations.append("Relevant based on content analysis")

            return "; ".join(explanations)

        except Exception as e:
            logger.warning("Failed to generate relevance explanation", error=str(e))
            return "Relevant to query"

    async def _log_search_analytics(
        self,
        query: str,
        results_count: int,
        execution_time_seconds: float
    ):
        """Log search query for analytics"""
        try:
            await supabase_client.log_search_query(
                query=query,
                results_count=results_count,
                execution_time_ms=int(execution_time_seconds * 1000)
            )
        except Exception as e:
            logger.warning("Failed to log search analytics", error=str(e))

    def _generate_search_cache_key(
        self,
        query: str,
        limit: int,
        threshold: float,
        search_type: str
    ) -> str:
        """Generate cache key for search results"""
        content = f"{query}:{limit}:{threshold}:{search_type}"
        return hashlib.md5(content.encode()).hexdigest()

    async def prepare_context_for_llm(
        self,
        results: List[Dict[str, Any]],
        max_tokens: int = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Prepare search results as context for LLM with token management

        Args:
            results: Search results
            max_tokens: Maximum context tokens (optional)

        Returns:
            Tuple of (formatted_context, sources_used)
        """
        max_tokens = max_tokens or self.max_context_tokens

        try:
            context_parts = []
            sources_used = []
            estimated_tokens = 0

            for i, result in enumerate(results):
                title = result.get("title", "Document sans titre")
                content = result.get("chunk_text", "")
                similarity = result.get("relevance_score", 0.0)

                # Format source entry
                source_text = f"\n[SOURCE {i+1}] - {title} (pertinence: {similarity:.0%})\n{content}\n"

                # Estimate tokens (rough: 4 chars per token)
                estimated_source_tokens = len(source_text) // 4

                # Check if adding this source would exceed limit
                if estimated_tokens + estimated_source_tokens > max_tokens:
                    # Try to fit partial content
                    remaining_tokens = max_tokens - estimated_tokens
                    remaining_chars = remaining_tokens * 4

                    if remaining_chars > 200:  # Minimum meaningful content
                        truncated_content = content[:remaining_chars - 100] + "..."
                        source_text = f"\n[SOURCE {i+1}] - {title} (pertinence: {similarity:.0%})\n{truncated_content}\n"
                        context_parts.append(source_text)
                        sources_used.append(result)

                    break

                context_parts.append(source_text)
                sources_used.append(result)
                estimated_tokens += estimated_source_tokens

            formatted_context = "".join(context_parts) if context_parts else "Aucun contexte pertinent trouvé."

            logger.debug("Context prepared for LLM",
                        sources_count=len(sources_used),
                        estimated_tokens=estimated_tokens,
                        context_length=len(formatted_context))

            return formatted_context, sources_used

        except Exception as e:
            logger.error("Failed to prepare context for LLM", error=str(e))
            return "Erreur lors de la préparation du contexte.", []

    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on partial query

        Args:
            partial_query: Partial search query
            limit: Maximum suggestions

        Returns:
            List of search suggestions
        """
        try:
            # This is a simplified implementation
            # In a production system, you might use:
            # - Previous search queries
            # - Note titles and content analysis
            # - Query completion models

            suggestions = []

            # Get recent search queries that match
            # (This would require storing search history)

            # For now, return basic suggestions based on content
            if len(partial_query) >= 2:
                # Search for notes with similar titles
                results = await supabase_client.list_notes(
                    search_query=partial_query,
                    limit=limit * 2
                )
                notes, _ = results

                for note in notes:
                    title = note.get("title", "")
                    if title and title.lower().startswith(partial_query.lower()):
                        suggestions.append(title)

                # Remove duplicates and limit
                suggestions = list(set(suggestions))[:limit]

            return suggestions

        except Exception as e:
            logger.warning("Failed to get search suggestions", error=str(e))
            return []

    async def get_related_content(
        self,
        note_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get content related to a specific note

        Args:
            note_id: ID of the reference note
            limit: Maximum related items

        Returns:
            List of related content
        """
        try:
            # Get the source note
            source_note = await supabase_client.get_note(note_id)
            if not source_note:
                return []

            # Use the note content as query for finding related content
            content = source_note.get("content", "")
            title = source_note.get("title", "")

            # Create a query from title and content snippet
            query = f"{title} {content[:200]}"

            # Search for related content, excluding the source note
            results = await self.search_knowledge(
                query=query,
                limit=limit * 2,
                search_type="vector"
            )

            # Filter out the source note
            related = [r for r in results if r.get("note_id") != note_id]

            return related[:limit]

        except Exception as e:
            logger.error("Failed to get related content", note_id=note_id, error=str(e))
            return []

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        try:
            cache_stats = await cache_manager.get_stats()
            embedding_stats = await embedding_service.get_stats()

            stats = {
                "service": "rag",
                "default_top_k": self.default_top_k,
                "default_threshold": self.default_threshold,
                "max_context_tokens": self.max_context_tokens,
                "cache_stats": cache_stats,
                "embedding_stats": embedding_stats
            }

            return stats

        except Exception as e:
            logger.error("Failed to get RAG stats", error=str(e))
            return {"error": str(e)}

# Global RAG service instance
rag_service = RAGService()