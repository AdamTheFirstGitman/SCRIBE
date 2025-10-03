"""
AutoGen Tools for Plume & Mimir agents
Permet aux agents de décider quand utiliser RAG, memory, etc.
"""

from typing import List, Dict, Any, Optional, Annotated
from services.rag import rag_service
from services.rag_service import get_rag_service
from services.storage import supabase_client
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize advanced RAG service for web search
web_rag_service = get_rag_service()


async def search_knowledge(
    query: str,
    limit: int = 10,
    similarity_threshold: float = 0.75
) -> Dict[str, Any]:
    """
    Recherche dans la base de connaissances en utilisant RAG (Retrieval-Augmented Generation).

    Utilise cette fonction quand:
    - L'utilisateur demande explicitement une recherche
    - La question nécessite des informations archivées
    - Il faut retrouver des notes/documents précédents

    Ne PAS utiliser pour:
    - Salutations simples (bonjour, salut, etc.)
    - Questions générales ne nécessitant pas de contexte archivé
    - Conversations courantes

    Args:
        query: Question ou terme de recherche
        limit: Nombre maximum de résultats (défaut: 10)
        similarity_threshold: Seuil de similarité (0-1, défaut: 0.75)

    Returns:
        Dict avec 'results' (liste de documents trouvés) et 'count' (nombre total)
    """
    try:
        logger.info("Tool search_knowledge called", query=query, limit=limit)

        results = await rag_service.search_knowledge(
            query=query,
            limit=limit,
            similarity_threshold=similarity_threshold
        )

        logger.info("Tool search_knowledge completed", results_found=len(results))

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        logger.error("Tool search_knowledge failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0
        }


async def web_search(
    query: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Recherche sur internet en utilisant Perplexity AI et Tavily.

    Utilise cette fonction quand:
    - La question nécessite des informations récentes/actuelles
    - Les archives locales ne contiennent pas l'information
    - L'utilisateur demande explicitement une recherche web
    - Il faut des données à jour (actualités, statistiques récentes, etc.)

    Ne PAS utiliser pour:
    - Informations déjà disponibles dans les archives locales
    - Questions sur le contenu stocké
    - Salutations ou conversations courantes

    Args:
        query: Question ou terme de recherche
        max_results: Nombre maximum de résultats (défaut: 5)

    Returns:
        Dict avec 'results' (liste de résultats web), 'count', et 'sources'
    """
    try:
        logger.info("Tool web_search called", query=query, max_results=max_results)

        # Utilise AdvancedRAGService avec web search activé
        rag_context = await web_rag_service.search(
            query=query,
            max_results=max_results,
            include_web=True,
            search_strategy="comprehensive"
        )

        logger.info("Tool web_search completed", results_found=rag_context.total_results)

        return {
            "success": True,
            "results": [
                {
                    "content": r.content,
                    "title": r.title,
                    "source": r.source,
                    "score": r.score,
                    "source_type": r.source_type
                }
                for r in rag_context.results
            ],
            "count": rag_context.total_results,
            "query": query,
            "confidence": rag_context.confidence_score
        }
    except Exception as e:
        logger.error("Tool web_search failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0
        }


async def get_related_content(
    note_id: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Trouve du contenu similaire à une note donnée.

    Utilise cette fonction quand:
    - L'utilisateur demande "quoi d'autre sur ce sujet?"
    - Il faut explorer des connexions entre concepts
    - Une note est mentionnée et l'utilisateur veut approfondir

    Args:
        note_id: ID de la note de référence
        limit: Nombre maximum de contenus similaires (défaut: 5)

    Returns:
        Dict avec 'results' (liste de contenus similaires) et 'count'
    """
    try:
        logger.info("Tool get_related_content called", note_id=note_id, limit=limit)

        results = await rag_service.get_related_content(
            note_id=note_id,
            limit=limit
        )

        logger.info("Tool get_related_content completed", results_found=len(results))

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "reference_note_id": note_id
        }
    except Exception as e:
        logger.error("Tool get_related_content failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0
        }


async def create_note(
    title: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crée une nouvelle note dans les archives.

    Utilise cette fonction quand:
    - Tu dois sauvegarder une restitution importante
    - L'utilisateur demande explicitement de sauvegarder quelque chose
    - Une synthèse ou reformulation mérite d'être archivée

    Args:
        title: Titre de la note
        content: Contenu textuel de la note
        metadata: Métadonnées optionnelles (tags, source, etc.)

    Returns:
        Dict avec 'success', 'note_id', et détails de la note créée
    """
    try:
        logger.info("Tool create_note called", title=title[:50])

        # Préparer les données de la note
        note_data = {
            "title": title,
            "text_content": content,
            "metadata": metadata or {},
            "tags": metadata.get("tags", []) if metadata else [],
            "source": "plume_agent"
        }

        # Créer la note
        note = await supabase_client.create_note(note_data)

        logger.info("Tool create_note completed", note_id=note.get("id"))

        return {
            "success": True,
            "note_id": note.get("id"),
            "title": note.get("title"),
            "created_at": note.get("created_at")
        }
    except Exception as e:
        logger.error("Tool create_note failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "note_id": None
        }


async def update_note(
    note_id: str,
    content: Optional[str] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Met à jour une note existante.

    Utilise cette fonction quand:
    - Une note nécessite une correction ou enrichissement
    - L'utilisateur demande de modifier une note
    - Il faut ajouter des informations à une note existante

    Args:
        note_id: ID de la note à mettre à jour
        content: Nouveau contenu (optionnel)
        title: Nouveau titre (optionnel)
        metadata: Nouvelles métadonnées (optionnel)

    Returns:
        Dict avec 'success' et détails de la note mise à jour
    """
    try:
        logger.info("Tool update_note called", note_id=note_id)

        # Préparer les données de mise à jour
        update_data = {}
        if content is not None:
            update_data["text_content"] = content
        if title is not None:
            update_data["title"] = title
        if metadata is not None:
            update_data["metadata"] = metadata

        # Mettre à jour la note
        note = await supabase_client.update_note(note_id, update_data)

        if note:
            logger.info("Tool update_note completed", note_id=note_id)
            return {
                "success": True,
                "note_id": note.get("id"),
                "title": note.get("title"),
                "updated_at": note.get("updated_at")
            }
        else:
            return {
                "success": False,
                "error": "Note not found",
                "note_id": note_id
            }
    except Exception as e:
        logger.error("Tool update_note failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "note_id": note_id
        }


# =============================================================================
# TOOLS ASSIGNMENT
# =============================================================================

# Mimir Tools - Agent archiviste et recherche
MIMIR_TOOLS = [
    search_knowledge,      # Recherche archives locales
    web_search,           # Recherche internet (Perplexity + Tavily)
    get_related_content   # Contenus similaires
]

# Plume Tools - Agent restitution et capture
PLUME_TOOLS = [
    create_note,          # Stocker restitutions
    update_note           # Mettre à jour notes
]
