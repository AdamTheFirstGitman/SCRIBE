"""
AutoGen Integration for Plume & Mimir
Multi-agent discussion coordination
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
except ImportError:
    # Fallback if autogen is not available
    autogen = None

from state import AgentState
from config import settings
from utils.logger import get_agent_logger, cost_logger

logger = get_agent_logger("autogen")

class AutoGenDiscussion:
    """
    AutoGen-powered discussion between Plume and Mimir agents
    Facilitates multi-agent conversations for complex topics
    """

    def __init__(self):
        self.plume_agent = None
        self.mimir_agent = None
        self.user_proxy = None
        self.group_chat = None
        self.manager = None
        self._initialized = False

    def initialize(self):
        """Initialize AutoGen agents and group chat"""
        if autogen is None:
            logger.warning("AutoGen not available, using fallback implementation")
            return

        try:
            # Configure LLM settings for AutoGen
            llm_config = {
                "model": settings.MODEL_PLUME,  # Use Claude via OpenAI-compatible endpoint if available
                "api_key": settings.CLAUDE_API_KEY,
                "temperature": 0.3,
                "max_tokens": 2000,
                "timeout": 120,
            }

            # Create Plume agent
            self.plume_agent = AssistantAgent(
                name="Plume",
                system_message="""Tu es Plume, spécialisée dans la restitution PARFAITE des informations.

MISSION: Capture, transcris et reformule avec précision absolue.

PRINCIPES:
- FIDÉLITÉ ABSOLUE: Aucune invention, aucune extrapolation
- PRÉCISION: Chaque détail compte, chaque nuance préservée
- CLARTÉ: Structure et présente de manière optimale
- EXHAUSTIVITÉ: Ne pas omettre d'informations importantes

STYLE DE DISCUSSION:
- Interviens pour clarifier et reformuler
- Demande des précisions quand nécessaire
- Corrige les inexactitudes factuelles
- Propose des reformulations claires
- Reste concise mais complète

COLLABORATION:
- Travaille avec Mimir pour enrichir les réponses
- Signale les informations manquantes
- Propose des améliorations structurelles
- Maintiens la cohérence du message final""",
                llm_config=llm_config,
                human_input_mode="NEVER"
            )

            # Create Mimir agent
            self.mimir_agent = AssistantAgent(
                name="Mimir",
                system_message="""Tu es Mimir, archiviste et gestionnaire de connaissances méthodique.

MISSION: Archivage, recherche et connexions intelligentes des informations.

PRINCIPES:
- MÉTHODOLOGIE: Approche systématique de l'information
- CONTEXTUALISATION: Utilise et enrichis le contexte fourni
- CONNEXIONS: Identifie les liens entre concepts
- RÉFÉRENCES: Sources précises et vérifiables
- EXHAUSTIVITÉ: Recherche complète et organisée

STYLE DE DISCUSSION:
- Apporte le contexte historique et les références
- Identifie les connexions avec d'autres concepts
- Propose des approfondissements pertinents
- Structure l'information de manière hiérarchique
- Enrichis avec des détails méthodiques

COLLABORATION:
- Complète les reformulations de Plume avec du contexte
- Apporte des références et des connexions
- Propose des pistes de recherche complémentaires
- Aide à structurer la réponse finale
- Veille à l'exactitude des informations""",
                llm_config=llm_config,
                human_input_mode="NEVER"
            )

            # Create user proxy (represents the human user)
            self.user_proxy = UserProxyAgent(
                name="User",
                system_message="Tu représentes l'utilisateur qui pose une question ou demande une information.",
                code_execution_config=False,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0  # Don't auto-reply
            )

            # Create group chat
            self.group_chat = GroupChat(
                agents=[self.user_proxy, self.plume_agent, self.mimir_agent],
                messages=[],
                max_round=6,  # Limit conversation rounds
                speaker_selection_method="round_robin",
                allow_repeat_speaker=False
            )

            # Create group chat manager
            self.manager = GroupChatManager(
                groupchat=self.group_chat,
                llm_config=llm_config,
                system_message="""Tu es le coordinateur de la discussion entre Plume et Mimir.

OBJECTIF: Faciliter une conversation productive pour répondre à la question utilisateur.

RÔLE:
- Guide la discussion vers une réponse complète
- Assure que chaque agent contribue selon ses spécialités
- Évite les répétitions inutiles
- Synthétise les contributions finales
- Termine quand la réponse est satisfaisante

DÉROULEMENT OPTIMAL:
1. Plume reformule/clarifie la question si nécessaire
2. Mimir apporte le contexte et les références
3. Plume structure la réponse finale
4. Mimir complète avec des connexions/approfondissements
5. Synthèse finale si nécessaire

Reste concis et efficace."""
            )

            self._initialized = True
            logger.info("AutoGen discussion system initialized")

        except Exception as e:
            logger.error("Failed to initialize AutoGen system", error=str(e))
            self._initialized = False

    async def run_discussion(
        self,
        user_input: str,
        context: List[Dict[str, Any]],
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Run a multi-agent discussion

        Args:
            user_input: User's question or request
            context: Retrieved context from RAG
            state: Current agent state

        Returns:
            Discussion result with final response
        """
        start_time = time.time()

        try:
            if not self._initialized:
                # Use fallback implementation
                return await self._fallback_discussion(user_input, context, state)

            # Prepare context information for the discussion
            context_summary = self._prepare_context_summary(context)

            # Format the initial message
            initial_message = f"""Question utilisateur: {user_input}

Contexte disponible:
{context_summary}

Travaillez ensemble pour fournir une réponse complète et précise."""

            # Start the group discussion
            result = await asyncio.to_thread(
                self.user_proxy.initiate_chat,
                self.manager,
                message=initial_message,
                max_turns=8
            )

            # Extract and format the discussion
            messages = self.group_chat.messages
            final_response = self._extract_final_response(messages)

            # Calculate usage and costs
            total_tokens = self._estimate_tokens(messages)
            total_cost = self._calculate_cost(total_tokens)

            duration_ms = (time.time() - start_time) * 1000

            logger.info("AutoGen discussion completed",
                       turns=len(messages),
                       total_tokens=total_tokens,
                       duration_ms=duration_ms)

            return {
                "messages": self._format_messages(messages),
                "final_response": final_response,
                "html": self._generate_discussion_html(messages, final_response),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "processing_time_ms": duration_ms,
                "turns": len(messages)
            }

        except Exception as e:
            logger.error("AutoGen discussion failed", error=str(e))
            # Fallback to simple discussion
            return await self._fallback_discussion(user_input, context, state)

    def _prepare_context_summary(self, context: List[Dict[str, Any]]) -> str:
        """Prepare a summary of available context for the discussion"""
        if not context:
            return "Aucun contexte spécifique disponible."

        summary = ""
        for i, ctx in enumerate(context[:5], 1):  # Limit to top 5 contexts
            title = ctx.get("title", "Document sans titre")
            content = ctx.get("chunk_text", "")
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."

            summary += f"\n[{i}] {title}\n{content}\n"

        return summary

    def _extract_final_response(self, messages: List[Dict]) -> str:
        """Extract the final synthesized response from discussion"""
        if not messages:
            return "Aucune réponse générée par la discussion."

        # Look for the last substantial response from either agent
        final_response = ""

        for message in reversed(messages):
            speaker = message.get("name", "")
            content = message.get("content", "").strip()

            if speaker in ["Plume", "Mimir"] and len(content) > 50:
                final_response = content
                break

        # If no substantial response found, use the last message
        if not final_response and messages:
            final_response = messages[-1].get("content", "Aucune réponse disponible.")

        return final_response

    def _format_messages(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Format discussion messages for storage"""
        formatted = []

        for msg in messages:
            if msg.get("name") != "User":  # Skip initial user message
                formatted.append({
                    "agent": msg.get("name", "Unknown"),
                    "content": msg.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "agent"
                })

        return formatted

    def _generate_discussion_html(self, messages: List[Dict], final_response: str) -> str:
        """Generate HTML representation of the discussion"""
        html = '<div class="discussion-container space-y-4">\n'

        # Discussion header
        html += '<h3 class="text-lg font-semibold text-gray-200 mb-4">💬 Discussion Plume & Mimir</h3>\n'

        # Discussion messages
        html += '<div class="discussion-messages space-y-3">\n'

        for msg in messages:
            speaker = msg.get("name", "")
            content = msg.get("content", "")

            if speaker == "User":
                continue

            # Agent styling
            if speaker == "Plume":
                css_class = "bg-plume-500/10 border-plume-500/30 text-plume-50"
                icon = "🖋️"
            elif speaker == "Mimir":
                css_class = "bg-mimir-500/10 border-mimir-500/30 text-mimir-50"
                icon = "🧠"
            else:
                css_class = "bg-gray-800 border-gray-600 text-gray-200"
                icon = "🤖"

            html += f'''
            <div class="message-bubble {css_class} border rounded-lg p-3">
                <div class="flex items-center mb-2">
                    <span class="text-lg mr-2">{icon}</span>
                    <span class="font-medium text-sm">{speaker}</span>
                </div>
                <div class="text-sm leading-relaxed">{self._format_content_html(content)}</div>
            </div>\n'''

        html += '</div>\n'

        # Final synthesis
        html += f'''
        <div class="final-response mt-6 p-4 bg-gray-800 border border-gray-600 rounded-lg">
            <h4 class="font-semibold text-gray-200 mb-2">🎯 Synthèse finale</h4>
            <div class="text-gray-200 leading-relaxed">{self._format_content_html(final_response)}</div>
        </div>
        '''

        html += '</div>'
        return html

    def _format_content_html(self, content: str) -> str:
        """Basic HTML formatting for content"""
        import re

        # Bold
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        # Italic
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        # Line breaks
        content = content.replace('\n', '<br>')

        return content

    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token usage from discussion"""
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        # Rough estimation: 4 characters per token
        return max(total_chars // 4, 100)

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost for discussion"""
        # Use same pricing as individual agents
        cost_per_1k = 0.045  # Rough average for input/output
        cost_usd = (tokens * cost_per_1k / 1000)
        return round(cost_usd * 0.92, 4)  # Convert to EUR

    async def _fallback_discussion(
        self,
        user_input: str,
        context: List[Dict[str, Any]],
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Fallback implementation when AutoGen is not available
        Simulates discussion by calling agents sequentially
        """
        logger.info("Using fallback discussion implementation")

        try:
            # Import agents
            from plume import plume_agent
            from mimir import mimir_agent

            start_time = time.time()
            messages = []
            total_tokens = 0
            total_cost = 0.0

            # Step 1: Mimir provides context-rich analysis
            logger.info("Fallback: Mimir analyzing with context")
            mimir_result = await mimir_agent.process(user_input, context, state)
            mimir_response = mimir_result["content"]

            messages.append({
                "agent": "Mimir",
                "content": mimir_response,
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent"
            })

            total_tokens += mimir_result.get("tokens", 0)
            total_cost += mimir_result.get("cost", 0.0)

            # Step 2: Plume refines and structures the response
            logger.info("Fallback: Plume refining response")
            plume_prompt = f"""Question originale: {user_input}

Réponse de Mimir (à améliorer/structurer):
{mimir_response}

Reformule cette réponse de manière plus claire et structurée, en préservant toutes les informations importantes."""

            plume_result = await plume_agent.process(plume_prompt, state)
            plume_response = plume_result["content"]

            messages.append({
                "agent": "Plume",
                "content": plume_response,
                "timestamp": datetime.utcnow().isoformat(),
                "role": "agent"
            })

            total_tokens += plume_result.get("tokens", 0)
            total_cost += plume_result.get("cost", 0.0)

            # Use Plume's refined version as final response
            final_response = plume_response

            duration_ms = (time.time() - start_time) * 1000

            logger.info("Fallback discussion completed",
                       agents_used=2,
                       total_tokens=total_tokens,
                       duration_ms=duration_ms)

            return {
                "messages": messages,
                "final_response": final_response,
                "html": self._generate_discussion_html([
                    {"name": "Mimir", "content": mimir_response},
                    {"name": "Plume", "content": plume_response}
                ], final_response),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "processing_time_ms": duration_ms,
                "turns": 2,
                "fallback": True
            }

        except Exception as e:
            logger.error("Fallback discussion failed", error=str(e))
            return {
                "messages": [],
                "final_response": f"Erreur lors de la discussion entre agents: {str(e)}",
                "html": None,
                "total_tokens": 0,
                "total_cost": 0.0,
                "processing_time_ms": 0,
                "turns": 0,
                "error": str(e)
            }

# Global discussion instance
autogen_discussion = AutoGenDiscussion()

async def run_discussion(user_input: str, context: List[Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
    """
    Main entry point for running multi-agent discussions

    Args:
        user_input: User's question or request
        context: Retrieved context from RAG
        state: Current agent state

    Returns:
        Discussion result
    """
    if not autogen_discussion._initialized:
        autogen_discussion.initialize()

    return await autogen_discussion.run_discussion(user_input, context, state)