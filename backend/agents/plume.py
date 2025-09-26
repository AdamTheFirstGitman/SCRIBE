"""
Plume Agent - Perfect Restitution Specialist
Captures, transcribes, and reformulates information with absolute precision
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from anthropic import Anthropic

from state import AgentState
from config import settings
from services.cache import cache_manager
from utils.logger import get_agent_logger, cost_logger
from services.transcription import transcription_service

logger = get_agent_logger("plume")

class PlumeAgent:
    """
    Plume - Agent de restitution parfaite

    Mission: Capture et reformulation précise des informations
    - Pas d'invention, que de la fidélité
    - Restitution structurée et claire
    - Reformulation selon le contexte demandé
    - Transcription audio parfaite
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.MODEL_PLUME
        self.max_tokens = settings.MAX_TOKENS_PLUME
        self.temperature = settings.TEMPERATURE_PLUME

        # Plume's core system prompt
        self.system_prompt = """Tu es Plume, agent spécialisé dans la restitution PARFAITE des informations.

MISSION PRINCIPALE:
Tu captures, transcris et reformules avec une précision absolue. Tu ne créés JAMAIS de contenu, tu restitues uniquement ce qui t'est donné.

PRINCIPES FONDAMENTAUX:
1. FIDÉLITÉ ABSOLUE - Aucune invention, aucune extrapolation
2. PRÉCISION - Chaque détail compte, chaque nuance est préservée
3. CLARTÉ - Structure et présente de manière optimale
4. EXHAUSTIVITÉ - Ne pas omettre d'informations importantes

CAPACITÉS:
- Restitution textuelle parfaite
- Reformulation selon contexte (résumé, expansion, restructuration)
- Transcription et organisation d'informations
- Mise en forme optimale (titres, listes, structure)
- Correction linguistique sans altération du sens

CONTRAINTES:
- Ne jamais inventer ou supposer
- Ne jamais ajouter d'informations non fournies
- Rester factuel et objectif
- Indiquer clairement quand des informations manquent
- Préserver l'intention originale

STYLE:
- Français impeccable
- Structure claire et logique
- Adaptation au contexte (formel/informel selon source)
- Mise en valeur des points importants
- Citations exactes quand pertinentes

Quand tu ne peux pas restituer parfaitement (information incomplète, ambiguë), indique-le clairement et propose des clarifications."""

    async def process(self, input_text: str, state: AgentState) -> Dict[str, Any]:
        """
        Process user input with perfect restitution approach

        Args:
            input_text: User input to process
            state: Current agent state

        Returns:
            Dict with response content, html, metadata
        """
        start_time = time.time()

        try:
            # Analyze input type and context
            context_analysis = await self._analyze_input_context(input_text)

            # Check cache for similar requests
            cache_key = self._generate_cache_key(input_text, context_analysis["type"])
            cached_response = await cache_manager.get_llm_response(cache_key, self.model)

            if cached_response:
                logger.info("Using cached response", cache_key=cache_key[:16])
                return self._format_response(cached_response, from_cache=True)

            # Prepare prompt based on context
            prompt = await self._prepare_prompt(input_text, context_analysis, state)

            # Call Claude
            response = await self._call_claude(prompt)

            # Process and format response
            formatted_response = self._format_response(response["content"])

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
                "context_type": context_analysis["type"],
                "cached": False
            })

            return formatted_response

        except Exception as e:
            logger.error("Plume processing failed", error=str(e))
            return {
                "content": f"Erreur lors de la restitution: {str(e)}",
                "html": None,
                "model": self.model,
                "tokens": 0,
                "cost": 0.0,
                "error": str(e)
            }

    async def _analyze_input_context(self, input_text: str) -> Dict[str, Any]:
        """Analyze input to determine optimal restitution approach"""

        analysis = {
            "type": "general_restitution",
            "length": len(input_text),
            "complexity": "medium",
            "requires_formatting": False,
            "has_structure": False,
            "language": "fr"
        }

        # Detect input characteristics
        if len(input_text) < 50:
            analysis["complexity"] = "simple"
        elif len(input_text) > 500:
            analysis["complexity"] = "complex"

        # Check for formatting needs
        if any(marker in input_text.lower() for marker in ["liste", "points", "étapes", "résumé"]):
            analysis["requires_formatting"] = True

        # Check for existing structure
        if any(marker in input_text for marker in ["1.", "2.", "-", "•", "#"]):
            analysis["has_structure"] = True

        # Detect specific restitution types
        if "résume" in input_text.lower() or "résumé" in input_text.lower():
            analysis["type"] = "summarization"
        elif "reformule" in input_text.lower() or "réécris" in input_text.lower():
            analysis["type"] = "reformulation"
        elif "structure" in input_text.lower() or "organise" in input_text.lower():
            analysis["type"] = "structuration"
        elif "corrige" in input_text.lower() or "améliore" in input_text.lower():
            analysis["type"] = "correction"

        return analysis

    async def _prepare_prompt(self, input_text: str, context: Dict[str, Any], state: AgentState) -> str:
        """Prepare optimized prompt based on context analysis"""

        base_instruction = ""

        # Adapt instruction based on context type
        if context["type"] == "summarization":
            base_instruction = """TÂCHE: Résumer fidèlement le contenu suivant.
- Préserver tous les points essentiels
- Maintenir la logique et la progression
- Condenser sans perdre d'information critique
- Indiquer si des éléments ne peuvent être résumés sans perte de sens"""

        elif context["type"] == "reformulation":
            base_instruction = """TÂCHE: Reformuler le contenu suivant avec précision.
- Conserver exactement le même sens
- Améliorer la clarté et la fluidité
- Maintenir le niveau de langage approprié
- Préserver tous les détails importants"""

        elif context["type"] == "structuration":
            base_instruction = """TÂCHE: Structurer et organiser le contenu suivant.
- Créer une hiérarchie logique claire
- Utiliser titres, sous-titres, listes selon pertinence
- Regrouper les idées connexes
- Maintenir la cohérence du propos original"""

        elif context["type"] == "correction":
            base_instruction = """TÂCHE: Corriger et améliorer le contenu suivant.
- Corriger les erreurs linguistiques
- Améliorer la syntaxe et la grammaire
- Préserver absolument le sens original
- Signaler tout changement non évident"""

        else:
            base_instruction = """TÂCHE: Restituer parfaitement le contenu suivant.
- Clarifier et structurer si nécessaire
- Maintenir l'intégralité du message
- Améliorer la présentation sans altérer le fond
- Préserver l'intention de l'auteur"""

        # Add formatting guidance
        formatting_note = ""
        if context["requires_formatting"]:
            formatting_note = "\nFORMATAGE: Utilise une structure claire avec titres, listes ou points selon pertinence."

        if context["complexity"] == "complex":
            formatting_note += "\nCOMPLEXITÉ: Contenu complexe - assure-toi de préserver toutes les nuances et connexions logiques."

        # Build final prompt
        prompt = f"""{base_instruction}{formatting_note}

CONTENU À TRAITER:
{input_text}

RÉPONSE (restitution parfaite):"""

        return prompt

    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """Call Claude API with optimized settings for Plume"""

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

            # Estimate tokens and cost (Claude pricing)
            estimated_tokens = response.usage.input_tokens + response.usage.output_tokens
            estimated_cost = self._calculate_cost(estimated_tokens)

            return {
                "content": content,
                "tokens": estimated_tokens,
                "cost": estimated_cost
            }

        except Exception as e:
            logger.error("Claude API call failed", error=str(e))
            raise

    def _format_response(self, content: str, from_cache: bool = False) -> Dict[str, Any]:
        """Format response with HTML version if applicable"""

        # Generate HTML version if content has structure
        html_content = None
        if self._has_structured_content(content):
            html_content = self._convert_to_html(content)

        return {
            "content": content,
            "html": html_content,
            "agent": "plume",
            "cached": from_cache
        }

    def _has_structured_content(self, content: str) -> bool:
        """Check if content would benefit from HTML formatting"""
        structured_indicators = [
            "# ", "## ", "### ",  # Markdown headers
            "1. ", "2. ", "3. ",  # Numbered lists
            "- ", "• ",           # Bullet points
            "**", "*",            # Bold/italic
            "\n\n"               # Paragraphs
        ]

        return any(indicator in content for indicator in structured_indicators)

    def _convert_to_html(self, content: str) -> str:
        """Convert structured text to HTML"""
        try:
            import re

            # Basic markdown-like conversion
            html = content

            # Headers
            html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)

            # Bold and italic
            html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

            # Lists - numbered
            html = re.sub(r'^(\d+)\. (.*$)', r'<li>\2</li>', html, flags=re.MULTILINE)

            # Lists - bullets
            html = re.sub(r'^- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
            html = re.sub(r'^• (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)

            # Wrap consecutive <li> tags in <ul> or <ol>
            html = self._wrap_list_items(html)

            # Paragraphs
            paragraphs = html.split('\n\n')
            html_paragraphs = []

            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('<'):
                    html_paragraphs.append(f'<p>{p}</p>')
                else:
                    html_paragraphs.append(p)

            html = '\n'.join(html_paragraphs)

            return html

        except Exception as e:
            logger.warning("HTML conversion failed", error=str(e))
            return None

    def _wrap_list_items(self, html: str) -> str:
        """Wrap consecutive <li> items in appropriate list tags"""
        import re

        # This is a simplified version - could be enhanced
        lines = html.split('\n')
        result = []
        in_list = False

        for line in lines:
            if '<li>' in line:
                if not in_list:
                    result.append('<ul>')
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

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost for Claude API usage"""
        # Claude 3 Opus pricing (approximate)
        input_cost_per_1k = 0.015  # USD
        output_cost_per_1k = 0.075  # USD

        # Rough estimate (assuming 70% input, 30% output)
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)

        cost_usd = (input_tokens * input_cost_per_1k / 1000) + (output_tokens * output_cost_per_1k / 1000)

        # Convert to EUR (approximate)
        cost_eur = cost_usd * 0.92

        return round(cost_eur, 4)

    def _generate_cache_key(self, input_text: str, context_type: str) -> str:
        """Generate cache key for request"""
        import hashlib

        content = f"{input_text}:{context_type}:{self.model}:{self.temperature}"
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

# Global Plume agent instance
plume_agent = PlumeAgent()