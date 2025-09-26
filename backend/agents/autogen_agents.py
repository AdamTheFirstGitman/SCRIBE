"""
AutoGen Integration for Plume & Mimir
Multi-agent discussion coordination
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    # AutoGen v0.4 imports
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    AUTOGEN_V4_AVAILABLE = True
except ImportError:
    # Fallback if autogen v0.4 is not available
    AUTOGEN_V4_AVAILABLE = False

from agents.state import AgentState
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
        self.model_client = None
        self.group_chat = None
        self._initialized = False

    def initialize(self):
        """Initialize AutoGen v0.4 agents and group chat"""
        if not AUTOGEN_V4_AVAILABLE:
            logger.warning("AutoGen v0.4 not available, using fallback implementation")
            return

        try:
            # Configure model client for AutoGen v0.4
            # Since we use Claude, we'll need to use OpenAI-compatible endpoint or create custom client
            # For now, using OpenAI client with Claude settings (may need adjustment)
            self.model_client = OpenAIChatCompletionClient(
                model="gpt-4o",  # Will need to configure for Claude later
                api_key=settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else "placeholder",
                # temperature=0.3,  # Set via agent system messages
                # max_tokens=2000,  # Set per agent
            )

            # Create Plume agent
            self.plume_agent = AssistantAgent(
                name="Plume",
                model_client=self.model_client,
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
- Maintiens la cohérence du message final"""
            )

            # Create Mimir agent
            self.mimir_agent = AssistantAgent(
                name="Mimir",
                model_client=self.model_client,
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
- Veille à l'exactitude des informations"""
            )

            # Create termination condition - stop when agents agree or max turns reached
            termination_condition = MaxMessageTermination(6)  # Max 6 rounds

            # Create RoundRobinGroupChat with Plume and Mimir
            self.group_chat = RoundRobinGroupChat(
                participants=[self.plume_agent, self.mimir_agent],
                termination_condition=termination_condition
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

            # Format the initial task message
            task_message = f"""Question utilisateur: {user_input}

Contexte disponible:
{context_summary}

Travaillez ensemble pour fournir une réponse complète et précise."""

            # Run the group discussion using AutoGen v0.4 async API
            result = await self.group_chat.run(task=task_message)

            # Extract messages and final response from v0.4 result
            messages = result.messages if hasattr(result, 'messages') else []
            final_response = self._extract_final_response_v4(messages)

            # Calculate usage and costs
            total_tokens = self._estimate_tokens(messages)
            total_cost = self._calculate_cost(total_tokens)

            duration_ms = (time.time() - start_time) * 1000

            logger.info("AutoGen discussion completed",
                       turns=len(messages),
                       total_tokens=total_tokens,
                       duration_ms=duration_ms)

            return {
                "messages": self._format_messages_v4(messages),
                "final_response": final_response,
                "html": self._generate_discussion_html_v4(messages, final_response),
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

    def _extract_final_response_v4(self, messages: List) -> str:
        """Extract the final synthesized response from AutoGen v0.4 discussion"""
        if not messages:
            return "Aucune réponse générée par la discussion."

        # AutoGen v0.4 messages have different structure
        final_response = ""

        for message in reversed(messages):
            # v0.4 messages might have different attributes
            content = ""
            source = ""

            if hasattr(message, 'content'):
                content = str(message.content).strip()
            elif hasattr(message, 'text'):
                content = str(message.text).strip()
            elif isinstance(message, dict):
                content = message.get('content', '').strip()

            if hasattr(message, 'source'):
                source = str(message.source)
            elif hasattr(message, 'name'):
                source = str(message.name)
            elif isinstance(message, dict):
                source = message.get('source', message.get('name', ''))

            if source in ["Plume", "Mimir"] and len(content) > 50:
                final_response = content
                break

        # If no substantial response found, use the last message
        if not final_response and messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'content'):
                final_response = str(last_msg.content)
            elif isinstance(last_msg, dict):
                final_response = last_msg.get('content', 'Aucune réponse disponible.')
            else:
                final_response = "Aucune réponse disponible."

        return final_response

    def _format_messages_v4(self, messages: List) -> List[Dict[str, Any]]:
        """Format AutoGen v0.4 discussion messages for storage"""
        formatted = []

        for msg in messages:
            content = ""
            source = ""

            if hasattr(msg, 'content'):
                content = str(msg.content)
            elif hasattr(msg, 'text'):
                content = str(msg.text)
            elif isinstance(msg, dict):
                content = msg.get('content', '')

            if hasattr(msg, 'source'):
                source = str(msg.source)
            elif hasattr(msg, 'name'):
                source = str(msg.name)
            elif isinstance(msg, dict):
                source = msg.get('source', msg.get('name', 'Unknown'))

            # Skip initial user messages and empty messages
            if source not in ["User", "user"] and content.strip():
                formatted.append({
                    "agent": source,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "agent"
                })

        return formatted

    def _generate_discussion_html_v4(self, messages: List, final_response: str) -> str:
        """Generate HTML representation of the AutoGen v0.4 discussion"""
        html = '<div class="discussion-container space-y-4">\n'

        # Discussion header
        html += '<h3 class="text-lg font-semibold text-gray-200 mb-4">💬 Discussion Plume & Mimir (v0.4)</h3>\n'

        # Discussion messages
        html += '<div class="discussion-messages space-y-3">\n'

        for msg in messages:
            content = ""
            source = ""

            if hasattr(msg, 'content'):
                content = str(msg.content)
            elif isinstance(msg, dict):
                content = msg.get('content', '')

            if hasattr(msg, 'source'):
                source = str(msg.source)
            elif hasattr(msg, 'name'):
                source = str(msg.name)
            elif isinstance(msg, dict):
                source = msg.get('source', msg.get('name', ''))

            if source in ["User", "user"] or not content.strip():
                continue

            # Agent styling
            if source == "Plume":
                css_class = "bg-plume-500/10 border-plume-500/30 text-plume-50"
                icon = "🖋️"
            elif source == "Mimir":
                css_class = "bg-mimir-500/10 border-mimir-500/30 text-mimir-50"
                icon = "🧠"
            else:
                css_class = "bg-gray-800 border-gray-600 text-gray-200"
                icon = "🤖"

            html += f'''
            <div class="message-bubble {css_class} border rounded-lg p-3">
                <div class="flex items-center mb-2">
                    <span class="text-lg mr-2">{icon}</span>
                    <span class="font-medium text-sm">{source}</span>
                </div>
                <div class="text-sm leading-relaxed">{self._format_content_html(content)}</div>
            </div>\n'''

        html += '</div>\n'

        # Final synthesis
        html += f'''
        <div class="final-response mt-6 p-4 bg-gray-800 border border-gray-600 rounded-lg">
            <h4 class="font-semibold text-gray-200 mb-2">🎯 Synthèse finale (v0.4)</h4>
            <div class="text-gray-200 leading-relaxed">{self._format_content_html(final_response)}</div>
        </div>
        '''

        html += '</div>'
        return html

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
            from agents.plume import plume_agent
            from agents.mimir import mimir_agent

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
                "html": self._generate_discussion_html_v4([
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