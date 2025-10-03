"""
State-of-the-Art RAG Service
Advanced retrieval with hybrid search, web augmentation, and knowledge graphs
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import httpx
from collections import defaultdict

from services.embeddings import embedding_service
from services.storage import supabase_client
from config import get_settings

@dataclass
class SearchResult:
    """Unified search result structure"""
    content: str
    title: str
    source: str
    score: float
    source_type: str  # 'document', 'web', 'knowledge_graph'
    metadata: Dict[str, Any]
    timestamp: datetime
    relevance_explanation: str = ""

@dataclass
class RAGContext:
    """Complete RAG context with multiple sources"""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float
    search_strategy: str
    confidence_score: float
    sources_summary: Dict[str, int]

class AdvancedRAGService:
    """
    State-of-the-art RAG service combining:
    - Vector similarity search (documents)
    - Full-text search (PostgreSQL)
    - BM25 scoring
    - Web search (Perplexity + Tavily)
    - Knowledge graph connections
    - Auto-tuning performance optimization
    """

    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = embedding_service
        self.supabase = supabase_client

        # Performance tracking
        self.query_stats = defaultdict(list)
        self.auto_tune_params = {
            'vector_weight': 0.4,
            'fulltext_weight': 0.3,
            'web_weight': 0.2,
            'knowledge_weight': 0.1,
            'similarity_threshold': 0.75,
            'max_results': 15,
            'web_search_trigger': 0.6  # If confidence < 0.6, trigger web search
        }

    async def search(self,
                    query: str,
                    max_results: int = 10,
                    include_web: bool = True,
                    search_strategy: str = "adaptive") -> RAGContext:
        """
        Main RAG search with hybrid approach

        Args:
            query: Search query
            max_results: Maximum results to return
            include_web: Whether to include web search
            search_strategy: 'fast', 'comprehensive', 'adaptive'
        """

        start_time = time.time()

        # Step 1: Generate query embedding
        query_embedding = await self.embedding_service.get_embedding(query)

        # Step 2: Parallel search across all sources
        search_tasks = [
            self._vector_search(query, query_embedding, max_results),
            self._fulltext_search(query, max_results),
            self._knowledge_graph_search(query, max_results)
        ]

        # Add web search if enabled
        if include_web:
            search_tasks.extend([
                self._perplexity_search(query, max_results // 3),
                self._tavily_search(query, max_results // 3)
            ])

        # Execute searches in parallel
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Step 3: Process and combine results
        all_results = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                all_results.extend(result)

        # Step 4: Re-rank with advanced scoring
        ranked_results = await self._advanced_reranking(query, query_embedding, all_results)

        # Step 5: Select best results
        final_results = ranked_results[:max_results]

        # Step 6: Calculate confidence and adapt strategy
        confidence_score = self._calculate_confidence(final_results, query)

        # Step 7: Auto-tune if needed
        if search_strategy == "adaptive":
            await self._auto_tune_parameters(query, final_results, confidence_score)

        processing_time = time.time() - start_time

        # Build context
        sources_summary = defaultdict(int)
        for result in final_results:
            sources_summary[result.source_type] += 1

        context = RAGContext(
            query=query,
            results=final_results,
            total_results=len(all_results),
            processing_time=processing_time,
            search_strategy=search_strategy,
            confidence_score=confidence_score,
            sources_summary=dict(sources_summary)
        )

        # Track for analytics
        await self._track_search(context)

        return context

    async def _vector_search(self, query: str, embedding: List[float], max_results: int) -> List[SearchResult]:
        """Vector similarity search in documents"""
        try:
            # Use the hybrid search function from database
            result = self.supabase.rpc(
                'hybrid_search',
                {
                    'query_text': query,
                    'query_embedding': embedding,
                    'match_threshold': self.auto_tune_params['similarity_threshold'],
                    'match_count': max_results * 2  # Get more for reranking
                }
            ).execute()

            search_results = []
            for row in result.data:
                search_results.append(SearchResult(
                    content=row['chunk_text'],
                    title=row['title'],
                    source=f"document:{row['note_id']}",
                    score=float(row['similarity']),
                    source_type='document',
                    metadata={
                        'document_id': row['note_id'],
                        'chunk_id': row['id'],
                        'fulltext_rank': float(row['rank'])
                    },
                    timestamp=datetime.now(),
                    relevance_explanation=f"Vector similarity: {row['similarity']:.3f}"
                ))

            return search_results

        except Exception as e:
            print(f"Vector search error: {e}")
            return []

    async def _fulltext_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Full-text search with PostgreSQL"""
        try:
            # Full-text search with ranking
            result = self.supabase.from_('notes') \
                .select('id, title, content, html') \
                .text_search('title,content', query, config='french') \
                .limit(max_results) \
                .execute()

            search_results = []
            for row in result.data:
                # Calculate BM25-like score (simplified)
                score = self._calculate_bm25_score(query, row['content'])

                search_results.append(SearchResult(
                    content=row['content'][:500] + "..." if len(row['content']) > 500 else row['content'],
                    title=row['title'],
                    source=f"fulltext:{row['id']}",
                    score=score,
                    source_type='document',
                    metadata={
                        'document_id': row['id'],
                        'has_html': bool(row['html'])
                    },
                    timestamp=datetime.now(),
                    relevance_explanation=f"Full-text match, BM25 score: {score:.3f}"
                ))

            return search_results

        except Exception as e:
            print(f"Fulltext search error: {e}")
            return []

    async def _perplexity_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Web search using Perplexity AI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful research assistant. Provide factual, up-to-date information with sources."
                            },
                            {
                                "role": "user",
                                "content": f"Search for recent information about: {query}. Provide key insights with sources."
                            }
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.2,
                        "return_citations": True
                    },
                    timeout=10.0
                )

            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']

                # Extract citations if available
                citations = []
                if 'citations' in data:
                    citations = data['citations']

                return [SearchResult(
                    content=content,
                    title="Perplexity AI Research",
                    source="web:perplexity",
                    score=0.85,  # High score for recent web info
                    source_type='web',
                    metadata={
                        'citations': citations,
                        'model': 'llama-3.1-sonar',
                        'search_engine': 'perplexity'
                    },
                    timestamp=datetime.now(),
                    relevance_explanation="Real-time web search with AI synthesis"
                )]

            return []

        except Exception as e:
            print(f"Perplexity search error: {e}")
            return []

    async def _tavily_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Web search using Tavily"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    headers={
                        "Content-Type": "application/json"
                    },
                    json={
                        "api_key": self.settings.TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "advanced",
                        "include_answer": True,
                        "include_raw_content": False,
                        "max_results": max_results,
                        "include_domains": [],
                        "exclude_domains": []
                    },
                    timeout=10.0
                )

            if response.status_code == 200:
                data = response.json()
                search_results = []

                # Add synthesized answer if available
                if data.get('answer'):
                    search_results.append(SearchResult(
                        content=data['answer'],
                        title="Tavily AI Summary",
                        source="web:tavily:summary",
                        score=0.80,
                        source_type='web',
                        metadata={
                            'search_engine': 'tavily',
                            'type': 'ai_summary'
                        },
                        timestamp=datetime.now(),
                        relevance_explanation="AI-synthesized web search summary"
                    ))

                # Add individual results
                for i, result in enumerate(data.get('results', [])):
                    search_results.append(SearchResult(
                        content=result['content'],
                        title=result['title'],
                        source=f"web:tavily:{result['url']}",
                        score=0.70 - (i * 0.05),  # Decreasing score by rank
                        source_type='web',
                        metadata={
                            'url': result['url'],
                            'search_engine': 'tavily',
                            'published_date': result.get('published_date')
                        },
                        timestamp=datetime.now(),
                        relevance_explanation=f"Web result #{i+1} from Tavily search"
                    ))

                return search_results

            return []

        except Exception as e:
            print(f"Tavily search error: {e}")
            return []

    async def _knowledge_graph_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Knowledge graph connections between documents"""
        try:
            # For now, implement basic document connections
            # TODO: Implement proper knowledge graph with entities and relationships

            query_embedding = await self.embedding_service.get_embedding(query)

            # Find documents with similar topics/entities
            result = self.supabase.from_('notes') \
                .select('id, title, content, tags, metadata') \
                .limit(max_results * 3) \
                .execute()

            knowledge_results = []

            for row in result.data:
                # Simple knowledge connections based on tags and topics
                metadata = row.get('metadata', {})
                tags = row.get('tags', [])
                topics = metadata.get('topics', [])

                # Check for connections
                connection_score = 0
                connections = []

                # Tag connections
                for tag in tags:
                    if tag.lower() in query.lower():
                        connection_score += 0.3
                        connections.append(f"tag:{tag}")

                # Topic connections
                for topic in topics:
                    if topic.lower() in query.lower():
                        connection_score += 0.2
                        connections.append(f"topic:{topic}")

                if connection_score > 0:
                    knowledge_results.append(SearchResult(
                        content=row['content'][:400] + "..." if len(row['content']) > 400 else row['content'],
                        title=row['title'],
                        source=f"knowledge:{row['id']}",
                        score=connection_score,
                        source_type='knowledge_graph',
                        metadata={
                            'document_id': row['id'],
                            'connections': connections,
                            'tags': tags,
                            'topics': topics
                        },
                        timestamp=datetime.now(),
                        relevance_explanation=f"Knowledge connections: {', '.join(connections)}"
                    ))

            # Sort by connection score
            knowledge_results.sort(key=lambda x: x.score, reverse=True)

            return knowledge_results[:max_results]

        except Exception as e:
            print(f"Knowledge graph search error: {e}")
            return []

    async def _advanced_reranking(self, query: str, query_embedding: List[float], results: List[SearchResult]) -> List[SearchResult]:
        """Advanced re-ranking with multiple signals"""

        if not results:
            return results

        # Calculate composite scores
        for result in results:
            composite_score = 0

            # Original score weighted by source type
            if result.source_type == 'document':
                composite_score += result.score * self.auto_tune_params['vector_weight']
            elif result.source_type == 'web':
                composite_score += result.score * self.auto_tune_params['web_weight']
            elif result.source_type == 'knowledge_graph':
                composite_score += result.score * self.auto_tune_params['knowledge_weight']

            # Query relevance boost
            query_terms = query.lower().split()
            content_lower = result.content.lower()
            title_lower = result.title.lower()

            # Title matching gets high boost
            title_matches = sum(1 for term in query_terms if term in title_lower)
            composite_score += (title_matches / len(query_terms)) * 0.3

            # Content density boost
            content_matches = sum(1 for term in query_terms if term in content_lower)
            composite_score += (content_matches / len(query_terms)) * 0.2

            # Recency boost for web results
            if result.source_type == 'web':
                time_diff = datetime.now() - result.timestamp
                if time_diff.days < 1:
                    composite_score += 0.1  # Recent web content boost

            # Diversity penalty (avoid too similar results)
            # TODO: Implement semantic similarity checking

            result.score = composite_score

        # Sort by composite score
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def _calculate_bm25_score(self, query: str, document: str) -> float:
        """Simplified BM25 scoring"""
        # Simplified implementation - in production use proper BM25
        query_terms = query.lower().split()
        doc_terms = document.lower().split()

        score = 0
        for term in query_terms:
            tf = doc_terms.count(term)
            if tf > 0:
                # Simplified BM25 formula
                score += tf / (tf + 1.5)

        return score / len(query_terms) if query_terms else 0

    def _calculate_confidence(self, results: List[SearchResult], query: str) -> float:
        """Calculate confidence score for results"""
        if not results:
            return 0.0

        # Factors for confidence calculation
        top_score = results[0].score if results else 0
        source_diversity = len(set(r.source_type for r in results))
        query_coverage = self._calculate_query_coverage(query, results)

        # Composite confidence score
        confidence = (
            min(top_score, 1.0) * 0.4 +          # Top result quality
            min(source_diversity / 3, 1.0) * 0.3 + # Source diversity
            query_coverage * 0.3                   # Query term coverage
        )

        return min(confidence, 1.0)

    def _calculate_query_coverage(self, query: str, results: List[SearchResult]) -> float:
        """Calculate how well results cover query terms"""
        query_terms = set(query.lower().split())
        if not query_terms:
            return 1.0

        covered_terms = set()
        for result in results[:3]:  # Check top 3 results
            content_terms = set(result.content.lower().split())
            title_terms = set(result.title.lower().split())
            covered_terms.update(query_terms.intersection(content_terms | title_terms))

        return len(covered_terms) / len(query_terms)

    async def _auto_tune_parameters(self, query: str, results: List[SearchResult], confidence: float):
        """Auto-tune RAG parameters based on performance"""

        # Store query performance
        self.query_stats[query].append({
            'confidence': confidence,
            'result_count': len(results),
            'timestamp': datetime.now(),
            'sources': [r.source_type for r in results]
        })

        # Adapt parameters based on recent performance
        recent_stats = list(self.query_stats.values())[-100:]  # Last 100 queries

        if len(recent_stats) >= 10:
            avg_confidence = sum(stat[0]['confidence'] for stat in recent_stats) / len(recent_stats)

            # If confidence is consistently low, adjust parameters
            if avg_confidence < 0.6:
                # Increase web search weight
                self.auto_tune_params['web_weight'] = min(0.4, self.auto_tune_params['web_weight'] + 0.05)
                self.auto_tune_params['vector_weight'] = max(0.2, self.auto_tune_params['vector_weight'] - 0.05)

            # If confidence is high, can reduce web dependency
            elif avg_confidence > 0.8:
                self.auto_tune_params['vector_weight'] = min(0.5, self.auto_tune_params['vector_weight'] + 0.05)
                self.auto_tune_params['web_weight'] = max(0.1, self.auto_tune_params['web_weight'] - 0.05)

    async def _track_search(self, context: RAGContext):
        """Track search analytics"""
        try:
            analytics_data = {
                'query': context.query,
                'results_count': len(context.results),
                'total_found': context.total_results,
                'processing_time_ms': round(context.processing_time * 1000),
                'confidence_score': context.confidence_score,
                'search_strategy': context.search_strategy,
                'sources_summary': context.sources_summary,
                'timestamp': datetime.now().isoformat()
            }

            # Store in analytics table (if exists)
            self.supabase.table('search_queries').insert(analytics_data).execute()

        except Exception as e:
            print(f"Analytics tracking error: {e}")

    async def get_search_analytics(self) -> Dict[str, Any]:
        """Get RAG service analytics"""
        try:
            # Get recent search stats
            result = self.supabase.table('search_queries') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(100) \
                .execute()

            queries = result.data

            if not queries:
                return {
                    'total_searches': 0,
                    'avg_confidence': 0,
                    'avg_processing_time': 0,
                    'source_distribution': {},
                    'current_params': self.auto_tune_params
                }

            # Calculate analytics
            total_searches = len(queries)
            avg_confidence = sum(q.get('confidence_score', 0) for q in queries) / total_searches
            avg_processing_time = sum(q.get('processing_time_ms', 0) for q in queries) / total_searches

            # Source distribution
            source_dist = defaultdict(int)
            for q in queries:
                sources = q.get('sources_summary', {})
                for source, count in sources.items():
                    source_dist[source] += count

            return {
                'total_searches': total_searches,
                'avg_confidence': round(avg_confidence, 3),
                'avg_processing_time_ms': round(avg_processing_time, 2),
                'source_distribution': dict(source_dist),
                'current_params': self.auto_tune_params,
                'recent_queries': [q['query'] for q in queries[:10]]
            }

        except Exception as e:
            return {'error': str(e), 'current_params': self.auto_tune_params}

# Singleton instance
_rag_service = None

def get_rag_service() -> AdvancedRAGService:
    """Get singleton RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = AdvancedRAGService()
    return _rag_service