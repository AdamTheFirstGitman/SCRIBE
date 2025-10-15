"""
SSE Context Management for Agent Tools

Ce module utilise contextvars pour passer la sse_queue aux tools AutoGen
sans modifier leurs signatures (requis par AutoGen).

Architecture:
- set_sse_queue() : Appelé par orchestrator avant group_chat.run()
- get_sse_queue() : Appelé par les tools pour récupérer la queue
- emit_agent_action() : Helper pour émettre les events SSE
"""

from contextvars import ContextVar
from typing import Optional, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

# Context variable pour stocker la sse_queue
_sse_queue_ctx: ContextVar[Optional[asyncio.Queue]] = ContextVar('sse_queue', default=None)


def set_sse_queue(queue: Optional[asyncio.Queue]) -> None:
    """
    Définit la queue SSE dans le contexte async actuel.

    À appeler depuis l'orchestrator AVANT group_chat.run().

    Args:
        queue: La queue asyncio pour émettre les events SSE
    """
    _sse_queue_ctx.set(queue)
    logger.debug(f"SSE queue configured in context: {queue is not None}")


def get_sse_queue() -> Optional[asyncio.Queue]:
    """
    Récupère la queue SSE depuis le contexte async actuel.

    À appeler depuis les tools pour émettre des events.

    Returns:
        La queue SSE si configurée, None sinon
    """
    return _sse_queue_ctx.get()


async def emit_agent_action(
    agent_name: str,
    action: str,
    status: str,
    details: Optional[str] = None,
    metadata: Optional[dict] = None
) -> None:
    """
    Émet un event SSE agent_action via la queue du contexte.

    Cette fonction est fail-safe : elle ne crashe jamais si la queue n'est pas configurée.

    Args:
        agent_name: Nom de l'agent (ex: "Mimir", "Plume")
        action: Action effectuée (ex: "search_knowledge", "create_note")
        status: État de l'action ("running", "completed", "failed")
        details: Détails additionnels optionnels
        metadata: Métadonnées additionnelles (ex: note_id, query, etc.)

    Example:
        await emit_agent_action(
            agent_name="Mimir",
            action="search_knowledge",
            status="running",
            details="Recherche dans les archives..."
        )
    """
    try:
        queue = get_sse_queue()
        if not queue:
            logger.debug(f"No SSE queue configured, skipping event: {agent_name}.{action}")
            return

        event_data = {
            "type": "agent_action",
            "agent": agent_name,
            "action": action,
            "status": status,
        }

        if details:
            event_data["details"] = details

        if metadata:
            event_data["metadata"] = metadata

        await queue.put(event_data)
        logger.debug(f"SSE event emitted: {agent_name}.{action} [{status}]")

    except Exception as e:
        # Never crash - SSE events sont optionnels
        logger.warning(f"Failed to emit SSE event {agent_name}.{action}: {e}")
