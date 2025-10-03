"""
Mimir Agent - Knowledge Archiving and Retrieval Specialist
Indexes, searches, and connects information with methodical precision
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from anthropic import Anthropic

from agents.state import AgentState
from config import settings
from services.cache import cache_manager
from services.rag import rag_service
from services.embeddings import embedding_service
from utils.logger import get_agent_logger, cost_logger

logger = get_agent_logger("mimir")

class MimirAgent:
    """
    Mimir - Agent archiviste et gestionnaire de connaissances

    Mission: Archivage et recherche méthodique des informations
    - Indexation précise et structurée
    - Recherche contextuelle avec RAG
    - Connections intelligentes entre concepts
    - Restitution enrichie par le contexte archivé
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.MODEL_MIMIR
        self.max_tokens = settings.MAX_TOKENS_MIMIR
        self.temperature = settings.TEMPERATURE_MIMIR

        # Mimir's core system prompt
        self.system_prompt = """Tu es Mimir, agent spécialisé dans l'archivage et la recherche méthodique de connaissances.

MISSION PRINCIPALE:
Tu indexes, cherches et connectes les informations avec rigueur. Tu utilises le contexte archivé pour enrichir tes réponses et créer des connexions pertinentes.

PRINCIPES FONDAMENTAUX:
1. MÉTHODOLOGIE - Approche systématique de l'information
2. CONTEXTUALISATION - Utilise toujours le contexte fourni
3. CONNEXIONS - Identifie les liens entre concepts
4. ADAPTATION - Modulation intelligente de la réponse
5. PRÉCISION - Références exactes et vérifiables

MODULATION DE RÉPONSE (CRITIQUE):
- Salutations/questions simples → Réponse BRÈVE et directe (2-3 phrases max)
- Questions sans contexte pertinent → Court et concis (1-2 paragraphes)
- Recherches avec peu de sources (0-2) → Synthèse courte
- Recherches riches (3+ sources) → Développement structuré complet
- Analyses complexes → Détails seulement si justifiés par le volume de sources

CAPACITÉS:
- Recherche contextuelle avancée
- Indexation et catégorisation
- Synthèse de sources multiples
- Identification de patterns et connexions
- Restitution enrichie avec références
- Organisation hiérarchique des connaissances

APPROCHE MÉTHODIQUE:
1. Analyser la requête et identifier les concepts clés
2. Utiliser le contexte fourni comme base de connaissance
3. Synthétiser les informations pertinentes
4. Créer des connexions logiques
5. Structurer la réponse de manière hiérarchique
6. Fournir des références précises

STYLE DE RÉPONSE:
- Structuré et organisé
- Citations et références quand pertinentes
- Connexions explicites entre concepts
- Nuances et précisions importantes
- Suggestions pour approfondir

GESTION DU CONTEXTE:
- Toujours utiliser le contexte fourni en priorité
- Indiquer clairement les sources utilisées
- Signaler quand l'information est incomplète
- Proposer des pistes de recherche complémentaires

Tu es un archiviste méticuleux qui transforme l'information en connaissance structurée."""

    async def process(self, input_text: str, context: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """
        Process user input with knowledge-based approach

        Args:
            input_text: User input/question
            context: Retrieved context from RAG system
            state: Current agent state

        Returns:
            Dict with response content, html, metadata
        """
        start_time = time.time()

        try:
            # Analyze query and context
            query_analysis = await self._analyze_query(input_text, context)

            # Check cache for similar knowledge queries
            cache_key = self._generate_cache_key(input_text, query_analysis["key_concepts"])
            cached_response = await cache_manager.get_llm_response(cache_key, self.model)

            if cached_response:
                logger.info("Using cached knowledge response", cache_key=cache_key[:16])
                return self._format_response(cached_response, context, from_cache=True)

            # Prepare knowledge-enriched prompt
            prompt = await self._prepare_knowledge_prompt(input_text, context, query_analysis)

            # Call Claude with context
            response = await self._call_claude(prompt)

            # Process and enrich response with references
            formatted_response = self._format_response(response["content"], context)

            # Cache the response
            await cache_manager.set_llm_response(cache_key, self.model, response["content"])

            # Log costs and usage
            duration_ms = (time.time() - start_time) * 1000
            self._log_usage(response["tokens"], response["cost"], duration_ms)

            # Add metadata
            formatted_response.update({
                "model": self.model,
                "tokens": response["tokens"],
                "cost": response["cost"],
                "processing_time_ms": duration_ms,
                "context_sources": len(context),
                "query_type": query_analysis["type"],
                "key_concepts": query_analysis["key_concepts"],
                "cached": False
            })

            return formatted_response

        except Exception as e:
            logger.log_agent_error("knowledge_task", error=str(e))
            return {
                "content": f"Erreur lors de la recherche de connaissances: {str(e)}",
                "html": None,
                "model": self.model,
                "tokens": 0,
                "cost": 0.0,
                "error": str(e)
            }

    async def _analyze_query(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze query to understand information needs"""

        analysis = {
            "type": "information_request",
            "key_concepts": [],
            "complexity": "medium",
            "requires_synthesis": False,
            "has_context": len(context) > 0,
            "context_relevance": "medium"
        }

        # Extract key concepts (simplified)
        query_lower = query.lower()

        # Detect query types
        question_indicators = ["comment", "pourquoi", "qu'est-ce que", "que", "qui", "où", "quand", "combien"]
        if any(indicator in query_lower for indicator in question_indicators):
            analysis["type"] = "question"

        comparison_indicators = ["différence", "comparer", "versus", "vs", "avantages", "inconvénients"]
        if any(indicator in query_lower for indicator in comparison_indicators):
            analysis["type"] = "comparison"
            analysis["requires_synthesis"] = True

        explanation_indicators = ["expliquer", "détailler", "développer", "approfondir"]
        if any(indicator in query_lower for indicator in explanation_indicators):
            analysis["type"] = "explanation"
            analysis["requires_synthesis"] = True

        # Assess context relevance
        if context:
            # Simple relevance scoring based on keyword overlap
            query_words = set(query_lower.split())
            context_relevance_scores = []

            for ctx in context:
                ctx_text = (ctx.get("chunk_text", "") + " " + ctx.get("title", "")).lower()
                ctx_words = set(ctx_text.split())
                overlap = len(query_words.intersection(ctx_words))
                relevance = overlap / max(len(query_words), 1)
                context_relevance_scores.append(relevance)

            avg_relevance = sum(context_relevance_scores) / len(context_relevance_scores) if context_relevance_scores else 0

            if avg_relevance > 0.3:
                analysis["context_relevance"] = "high"
            elif avg_relevance > 0.1:
                analysis["context_relevance"] = "medium"
            else:
                analysis["context_relevance"] = "low"

        # Extract key concepts (basic keyword extraction)
        import re
        words = re.findall(r'\b\w{4,}\b', query_lower)  # Words with 4+ characters
        analysis["key_concepts"] = list(set(words[:5]))  # Top 5 unique concepts

        return analysis

    async def _prepare_knowledge_prompt(self, query: str, context: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Prepare prompt enriched with knowledge context"""

        # Build context section
        context_section = ""
        if context:
            context_section = "\n\nCONTEXTE ARCHIVÉ:\n"

            for i, ctx in enumerate(context, 1):
                title = ctx.get("title", "Document sans titre")
                content = ctx.get("chunk_text", ctx.get("content", ""))
                similarity = ctx.get("similarity_score", 0)

                # Truncate long content
                if len(content) > 800:
                    content = content[:800] + "..."

                context_section += f"\n[SOURCE {i}] - {title} (pertinence: {similarity:.2f})\n{content}\n"

        # Adapt instructions based on query analysis
        task_instruction = ""

        if analysis["type"] == "question":
            task_instruction = """TÂCHE: Répondre à la question en utilisant le contexte archivé.
- Utilise prioritairement les sources fournies
- Structure la réponse de manière claire et logique
- Cite les sources utilisées [SOURCE X]
- Indique si l'information est incomplète"""

        elif analysis["type"] == "comparison":
            task_instruction = """TÂCHE: Comparer les éléments en synthétisant le contexte archivé.
- Identifie les points de comparaison pertinents
- Structure en avantages/inconvénients ou différences/similitudes
- Utilise les sources pour étayer chaque point
- Fournis une synthèse équilibrée"""

        elif analysis["type"] == "explanation":
            task_instruction = """TÂCHE: Expliquer le concept en utilisant le contexte archivé.
- Structure l'explication de manière pédagogique
- Utilise le contexte pour enrichir l'explication
- Identifie les connexions entre concepts
- Propose des approfondissements si pertinent"""

        else:
            task_instruction = """TÂCHE: Traiter la demande d'information avec le contexte archivé.
- Analyse le contexte fourni
- Synthétise les informations pertinentes
- Structure la réponse de manière logique
- Références les sources utilisées"""

        # Add context-specific guidance
        context_guidance = ""
        if analysis["context_relevance"] == "high":
            context_guidance = "\nCONTEXTE RICHE: Tu as accès à du contexte très pertinent. Utilise-le pleinement."
        elif analysis["context_relevance"] == "low":
            context_guidance = "\nCONTEXTE LIMITÉ: Le contexte fourni semble moins directement pertinent. Utilise ce qui est applicable et indique les limites."

        # Build synthesis guidance
        synthesis_guidance = ""
        if analysis["requires_synthesis"]:
            synthesis_guidance = "\nSYNTHÈSE: Cette requête nécessite de synthétiser plusieurs sources. Crée des connexions logiques entre les informations."

        # Build final prompt
        prompt = f"""{task_instruction}{context_guidance}{synthesis_guidance}{context_section}

QUESTION/REQUÊTE:
{query}

RÉPONSE MIMIR (basée sur les connaissances archivées):"""

        return prompt

    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """Call Claude API with optimized settings for Mimir"""

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Estimate tokens and cost
            estimated_tokens = response.usage.input_tokens + response.usage.output_tokens
            estimated_cost = self._calculate_cost(estimated_tokens)

            return {
                "content": content,
                "tokens": estimated_tokens,
                "cost": estimated_cost
            }

        except Exception as e:
            logger.log_agent_error("llm_call", error=str(e))
            raise

    def _format_response(self, content: str, context: List[Dict[str, Any]], from_cache: bool = False) -> Dict[str, Any]:
        """Format response with enhanced HTML and source references"""

        # Generate enhanced HTML version
        html_content = self._convert_to_enhanced_html(content, context)

        # Extract source references
        sources = self._extract_source_references(content, context)

        return {
            "content": content,
            "html": html_content,
            "sources": sources,
            "agent": "mimir",
            "cached": from_cache,
            "context_used": len(context)
        }

    def _convert_to_enhanced_html(self, content: str, context: List[Dict[str, Any]]) -> str:
        """Convert to HTML with enhanced formatting for knowledge content"""
        try:
            import re

            html = content

            # Headers
            html = re.sub(r'^### (.*$)', r'<h3 class="text-lg font-semibold text-mimir-400 mt-4 mb-2">\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.*$)', r'<h2 class="text-xl font-bold text-mimir-300 mt-6 mb-3">\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.*$)', r'<h1 class="text-2xl font-bold text-mimir-200 mt-8 mb-4">\1</h1>', html, flags=re.MULTILINE)

            # Source references with enhanced styling
            html = re.sub(r'\[SOURCE (\d+)\]', r'<span class="inline-flex items-center px-2 py-1 text-xs font-medium bg-mimir-100 text-mimir-800 rounded-full">[SOURCE \1]</span>', html)

            # Bold and italic
            html = re.sub(r'\*\*(.*?)\*\*', r'<strong class="font-semibold text-mimir-100">\1</strong>', html)
            html = re.sub(r'\*(.*?)\*', r'<em class="italic text-mimir-200">\1</em>', html)

            # Lists with styling
            html = re.sub(r'^(\d+)\. (.*$)', r'<li class="mb-1">\2</li>', html, flags=re.MULTILINE)
            html = re.sub(r'^- (.*$)', r'<li class="mb-1">\1</li>', html, flags=re.MULTILINE)

            # Wrap list items
            html = self._wrap_enhanced_lists(html)

            # Paragraphs with spacing
            paragraphs = html.split('\n\n')
            html_paragraphs = []

            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('<'):
                    html_paragraphs.append(f'<p class="mb-3 leading-relaxed">{p}</p>')
                else:
                    html_paragraphs.append(p)

            html = '\n'.join(html_paragraphs)

            # Add source context at the end
            if context:
                sources_html = self._generate_sources_html(context)
                html += f'\n\n<div class="mt-6 pt-4 border-t border-mimir-700">{sources_html}</div>'

            return html

        except Exception as e:
            logger.warning("Enhanced HTML conversion failed", error=str(e))
            return content

    def _wrap_enhanced_lists(self, html: str) -> str:
        """Wrap list items with enhanced styling"""
        lines = html.split('\n')
        result = []
        in_list = False

        for line in lines:
            if '<li class=' in line:
                if not in_list:
                    result.append('<ul class="list-disc list-inside space-y-1 ml-4 text-gray-200">')
                    in_list = True
                result.append(line)
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)

        if in_list:
            result.append('</ul>')

        return '\n'.join(result)

    def _generate_sources_html(self, context: List[Dict[str, Any]]) -> str:
        """Generate HTML for source references"""
        if not context:
            return ""

        sources_html = '<h4 class="text-lg font-semibold text-mimir-300 mb-3">Sources utilisées</h4>\n<div class="space-y-2">'

        for i, ctx in enumerate(context, 1):
            title = ctx.get("title", "Document sans titre")
            similarity = ctx.get("similarity_score", 0)
            note_id = ctx.get("note_id", "")

            sources_html += f'''
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <div>
                    <span class="text-sm font-medium text-mimir-300">[SOURCE {i}]</span>
                    <span class="ml-2 text-sm text-gray-200">{title}</span>
                </div>
                <div class="text-xs text-gray-400">
                    Pertinence: {similarity:.0%}
                </div>
            </div>'''

        sources_html += '</div>'
        return sources_html

    def _extract_source_references(self, content: str, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract which sources were referenced in the response"""
        import re

        references = []
        source_mentions = re.findall(r'\[SOURCE (\d+)\]', content)

        for mention in source_mentions:
            source_num = int(mention) - 1  # Convert to 0-based index
            if 0 <= source_num < len(context):
                ctx = context[source_num]
                references.append({
                    "source_number": mention,
                    "title": ctx.get("title", ""),
                    "note_id": ctx.get("note_id", ""),
                    "similarity_score": ctx.get("similarity_score", 0)
                })

        return references

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost for Claude API usage"""
        # Claude 3 Opus pricing (approximate)
        input_cost_per_1k = 0.015  # USD
        output_cost_per_1k = 0.075  # USD

        # Rough estimate (70% input, 30% output for knowledge queries)
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)

        cost_usd = (input_tokens * input_cost_per_1k / 1000) + (output_tokens * output_cost_per_1k / 1000)

        # Convert to EUR (approximate)
        cost_eur = cost_usd * 0.92

        return round(cost_eur, 4)

    def _generate_cache_key(self, query: str, concepts: List[str]) -> str:
        """Generate cache key for knowledge query"""
        import hashlib

        concepts_str = ",".join(sorted(concepts))
        content = f"{query}:{concepts_str}:{self.model}:{self.temperature}"
        return hashlib.md5(content.encode()).hexdigest()

    def _log_usage(self, tokens: int, cost: float, duration_ms: float):
        """Log token usage and cost"""
        logger.log_llm_call(
            model=self.model,
            tokens_used=tokens,
            cost=cost
        )

        cost_logger.log_token_usage(
            service="claude",
            model=self.model,
            tokens=tokens,
            cost=cost
        )

# Global Mimir agent instance
mimir_agent = MimirAgent()