"""
Intent Classification Service
Classifies user input to route to appropriate agent (Plume, Mimir, or Discussion)
Supports both keyword-based and LLM-based classification
"""

import asyncio
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class IntentClassifier:
    """
    Classifies user intent for intelligent routing

    Intent types:
    - restitution: Reformulation, transcription, summarization → Plume
    - recherche: Knowledge search, RAG retrieval → Mimir
    - discussion: Complex analysis, debate, comparison → AutoGen
    """

    # Intent keywords mapping
    INTENT_KEYWORDS = {
        "restitution": [
            "reformule", "résume", "transcris", "explique", "simplifie",
            "clarifie", "traduis", "corrige", "améliore", "rédige",
            "écris", "formule", "présente", "décris"
        ],
        "recherche": [
            "cherche", "trouve", "recherche", "où", "quel", "quelle",
            "quels", "quelles", "qui", "comment", "quand", "combien",
            "qu'est-ce", "définition", "documentation", "source"
        ],
        "discussion": [
            "compare", "analyser", "débat", "différence", "avantages",
            "inconvénients", "évalue", "critique", "discute", "opinion",
            "perspectives", "pour et contre", "vs", "versus"
        ]
    }

    # Question indicators
    QUESTION_INDICATORS = ["?", "pourquoi", "comment", "qu'est", "que"]

    # Complex analysis indicators
    COMPLEX_INDICATORS = [
        "expliquer en détail", "analyse approfondie", "étude comparative",
        "évaluation critique", "plusieurs points de vue"
    ]

    def __init__(self, use_llm: bool = False):
        """
        Initialize intent classifier

        Args:
            use_llm: If True, use LLM for classification (more accurate but slower)
                    If False, use keyword-based classification (faster, cheaper)
        """
        self.use_llm = use_llm
        self.client = None

        if use_llm:
            self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
            logger.info("Intent classifier initialized with LLM mode")
        else:
            logger.info("Intent classifier initialized with keyword mode")

    async def classify(
        self,
        input_text: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent

        Args:
            input_text: User input message
            conversation_context: Previous messages for context

        Returns:
            {
                "intent": "restitution" | "recherche" | "discussion",
                "confidence": float (0.0 to 1.0),
                "reasoning": str,
                "method": "keyword" | "llm"
            }
        """

        if not input_text or not input_text.strip():
            return {
                "intent": "restitution",
                "confidence": 0.5,
                "reasoning": "Empty input, defaulting to restitution",
                "method": "default"
            }

        try:
            if self.use_llm:
                return await self._classify_with_llm(input_text, conversation_context)
            else:
                return self._classify_with_keywords(input_text, conversation_context)

        except Exception as e:
            logger.error("Intent classification failed", error=str(e))
            # Fallback to keyword-based
            return self._classify_with_keywords(input_text, conversation_context)

    def _classify_with_keywords(
        self,
        input_text: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Keyword-based classification (fast and cheap)
        """

        lower_text = input_text.lower().strip()
        text_length = len(input_text)

        # Score each intent based on keyword matches
        scores = {
            "restitution": 0.0,
            "recherche": 0.0,
            "discussion": 0.0
        }

        # Check keywords for each intent
        for intent, keywords in self.INTENT_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in lower_text)
            if matches > 0:
                scores[intent] = matches / len(keywords)

        # Question detection (favors recherche)
        if any(indicator in lower_text for indicator in self.QUESTION_INDICATORS):
            scores["recherche"] += 0.3

        # Complex indicators (favors discussion)
        if any(indicator in lower_text for indicator in self.COMPLEX_INDICATORS):
            scores["discussion"] += 0.4

        # Text length influence
        if text_length > 200:
            scores["discussion"] += 0.1  # Long text might need discussion
        elif text_length < 50:
            scores["restitution"] += 0.1  # Short text likely simple restitution

        # Conversation context influence
        if conversation_context and len(conversation_context) > 5:
            # Long conversation might need discussion
            scores["discussion"] += 0.1

        # Determine winner
        if max(scores.values()) == 0:
            # No matches, use defaults based on heuristics
            if "?" in input_text:
                intent = "recherche"
                confidence = 0.6
            else:
                intent = "restitution"
                confidence = 0.5
        else:
            intent = max(scores, key=scores.get)
            confidence = min(scores[intent] + 0.5, 0.95)  # Cap at 0.95

        reasoning = f"Keyword-based: {intent} scored {scores[intent]:.2f}"

        logger.info(
            "Intent classified with keywords",
            intent=intent,
            confidence=confidence,
            scores=scores
        )

        return {
            "intent": intent,
            "confidence": confidence,
            "reasoning": reasoning,
            "method": "keyword",
            "scores": scores
        }

    async def _classify_with_llm(
        self,
        input_text: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        LLM-based classification (accurate but slower/costlier)
        Uses Claude Haiku for fast, cheap classification
        """

        # Build context summary if available
        context_summary = ""
        if conversation_context:
            recent_messages = conversation_context[-3:]  # Last 3 messages
            context_summary = "\n".join([
                f"- {msg.get('role', 'user')}: {msg.get('content', '')[:100]}"
                for msg in recent_messages
            ])

        prompt = f"""Tu es un classificateur d'intentions pour un système d'agents IA.

Classifie l'intention de l'utilisateur parmi ces 3 catégories:

1. **restitution** - L'utilisateur veut:
   - Reformuler, résumer ou clarifier du contenu
   - Transcrire ou corriger du texte
   - Obtenir une présentation claire d'informations existantes
   - Exemples: "Résume ce texte", "Reformule cette idée", "Corrige cette phrase"

2. **recherche** - L'utilisateur veut:
   - Chercher des informations dans une base de connaissances
   - Obtenir des réponses factuelles à des questions
   - Trouver de la documentation ou des sources
   - Exemples: "Où se trouve...", "Qu'est-ce que...", "Trouve-moi des infos sur..."

3. **discussion** - L'utilisateur veut:
   - Analyser en profondeur un sujet complexe
   - Comparer plusieurs perspectives ou options
   - Débattre des avantages/inconvénients
   - Obtenir une évaluation critique
   - Exemples: "Compare X et Y", "Analyse les avantages de...", "Débat sur..."

{"Contexte conversation récente:" if context_summary else ""}
{context_summary if context_summary else ""}

Message utilisateur:
"{input_text}"

Réponds UNIQUEMENT au format JSON:
{{
    "intent": "restitution" | "recherche" | "discussion",
    "confidence": 0.0-1.0,
    "reasoning": "explication brève"
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cheap
                max_tokens=200,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = response.content[0].text.strip()

            # Try to extract JSON
            import json
            import re

            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                result = json.loads(json_match.group())

                intent = result.get("intent", "restitution")
                confidence = float(result.get("confidence", 0.8))
                reasoning = result.get("reasoning", "LLM classification")

                # Validate intent
                if intent not in ["restitution", "recherche", "discussion"]:
                    logger.warning(f"Invalid intent from LLM: {intent}, defaulting to restitution")
                    intent = "restitution"

                logger.info(
                    "Intent classified with LLM",
                    intent=intent,
                    confidence=confidence,
                    reasoning=reasoning
                )

                return {
                    "intent": intent,
                    "confidence": confidence,
                    "reasoning": f"LLM: {reasoning}",
                    "method": "llm"
                }
            else:
                logger.warning("Could not parse JSON from LLM response, falling back to keywords")
                return self._classify_with_keywords(input_text, conversation_context)

        except Exception as e:
            logger.error("LLM classification failed", error=str(e))
            # Fallback to keyword-based
            return self._classify_with_keywords(input_text, conversation_context)


# Global classifier instance (keyword-based by default for performance)
intent_classifier = IntentClassifier(use_llm=False)

# Alternative LLM-based classifier (use when accuracy is critical)
llm_intent_classifier = IntentClassifier(use_llm=True)