# 🤖 KODA - Phase 2.2 : AutoGen Discussion Streaming

**Agent :** Koda (Backend Specialist)
**Phase :** 2.2 - Phase 1 (Parallèle)
**Durée estimée :** 3-4 heures
**Status :** 🚧 À EXÉCUTER

---

## 🎯 OBJECTIF

Modifier l'orchestrateur LangGraph pour rendre visible la discussion interne entre Plume et Mimir en mode AutoGen. L'utilisateur doit voir les échanges entre agents en temps réel via streaming SSE, comme s'il assistait à une conversation entre eux.

**Priorité :** Streaming fluide, routing intelligent par prénom, discussion complète visible.

---

## 📊 ARCHITECTURE ACTUELLE

**Orchestrator (Phase 2.1) :**
- LangGraph StateGraph avec nodes : intake, transcription, routing, context, processing, storage, finalize
- Mode `auto` : routing intelligent via Intent Classifier
- Mode `plume` / `mimir` : force agent spécifique
- Mode `discussion` : AutoGen multi-agents (implémenté mais pas visible)
- Checkpointing avec MemorySaver
- Memory Service intégré

**Problème actuel :**
- Mode `discussion` existe mais renvoie uniquement la réponse finale
- Les messages internes Plume ↔ Mimir ne sont pas exposés
- Frontend ne peut pas afficher la "conversation" entre agents

**Objectif Phase 2.2 :**
- Capturer messages internes AutoGen
- Les streamer via SSE au frontend
- Permettre routing par prénom ("Plume, peux-tu..." → force Plume)
- Historique discussion disponible dans metadata finale

---

## 🏗️ MODIFICATIONS ORCHESTRATOR

### **1. Capturer Messages AutoGen**

**Fichier :** `backend/agents/orchestrator.py`

**Créer nouveau node `discussion_node` :**

```python
async def discussion_node(self, state: AgentState) -> AgentState:
    """
    Handle AutoGen multi-agent discussion
    Captures internal messages for streaming
    """

    input_text = state.get("input_text", "")
    conversation_id = state.get("conversation_id")
    user_id = state.get("user_id")

    logger.info(f"Starting AutoGen discussion for: {input_text[:50]}...")

    # Initialize discussion history
    discussion_history = []

    try:
        # Create AutoGen agents
        from agents.autogen_discussion import create_discussion_agents

        plume_agent, mimir_agent, user_proxy = create_discussion_agents()

        # Custom message handler to capture exchanges
        def message_handler(sender, recipient, message):
            """Capture messages between agents"""
            discussion_history.append({
                'agent': sender.name.lower(),
                'message': message.get('content', ''),
                'timestamp': datetime.now().isoformat(),
                'to': recipient.name.lower()
            })

            # Also stream to SSE if connection exists
            if hasattr(state, '_sse_queue'):
                state['_sse_queue'].put_nowait({
                    'type': 'agent_message',
                    'agent': sender.name.lower(),
                    'content': message.get('content', ''),
                    'to': recipient.name.lower(),
                    'timestamp': datetime.now().isoformat()
                })

        # Register message handler
        plume_agent.register_reply(
            trigger=lambda sender, recipient, message: True,
            reply_func=lambda sender, recipient, message, request_reply: message_handler(sender, recipient, message)
        )

        mimir_agent.register_reply(
            trigger=lambda sender, recipient, message: True,
            reply_func=lambda sender, recipient, message, request_reply: message_handler(sender, recipient, message)
        )

        # Start discussion
        user_proxy.initiate_chat(
            recipient=plume_agent if 'plume' in input_text.lower() else mimir_agent,
            message=input_text
        )

        # Get final response
        final_response = user_proxy.last_message().get('content', '')

        # Update state
        state["response"] = final_response
        state["agent_used"] = "discussion"
        state["agents_involved"] = ["plume", "mimir"]
        state["discussion_history"] = discussion_history

        logger.info(f"Discussion completed with {len(discussion_history)} exchanges")

    except Exception as e:
        logger.error(f"Discussion failed: {str(e)}")
        state["response"] = f"Erreur lors de la discussion : {str(e)}"
        state["agent_used"] = "error"
        state["errors"].append({
            "node": "discussion",
            "error": str(e)
        })

    return state
```

---

### **2. Routing par Prénom**

**Modifier `routing_node` pour détecter prénoms dans input :**

```python
async def routing_node(self, state: AgentState) -> AgentState:
    """
    Intelligent routing based on intent and explicit agent mention
    """

    input_text = state.get("input_text", "")
    mode = state.get("mode", "auto")

    # Check for explicit agent mention by name
    input_lower = input_text.lower()

    if "plume" in input_lower and "mimir" not in input_lower:
        # User explicitly mentioned Plume
        logger.info("Routing to Plume (explicit mention)")
        state["agent_used"] = "plume"
        state["routing_reason"] = "explicit_mention_plume"
        return state

    if "mimir" in input_lower and "plume" not in input_lower:
        # User explicitly mentioned Mimir
        logger.info("Routing to Mimir (explicit mention)")
        state["agent_used"] = "mimir"
        state["routing_reason"] = "explicit_mention_mimir"
        return state

    if "plume" in input_lower and "mimir" in input_lower:
        # Both mentioned → discussion mode
        logger.info("Routing to Discussion (both mentioned)")
        state["agent_used"] = "discussion"
        state["routing_reason"] = "both_agents_mentioned"
        return state

    # No explicit mention → use intent classifier or forced mode
    if mode != "auto":
        # Mode forced by user
        state["agent_used"] = mode
        state["routing_reason"] = "forced_mode"
        return state

    # Auto routing via Intent Classifier
    from services.intent_classifier import IntentClassifier

    classifier = IntentClassifier()
    intent_result = await classifier.classify(input_text)

    agent = intent_result.get("agent", "plume")
    confidence = intent_result.get("confidence", 0.5)

    state["agent_used"] = agent
    state["routing_reason"] = f"intent_classifier_confidence_{confidence}"
    state["routing_metadata"] = intent_result

    logger.info(f"Routed to {agent} (confidence: {confidence})")

    return state
```

---

### **3. SSE Streaming Support**

**Créer nouveau endpoint SSE pour streaming discussion :**

**Fichier :** `backend/api/chat.py`

```python
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json

@router.post("/orchestrated/stream")
async def chat_orchestrated_stream(request: OrchestratedChatRequest, fastapi_request: Request):
    """
    Orchestrated chat with SSE streaming
    Streams agent messages in real-time
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events"""

        # Create queue for messages
        message_queue = asyncio.Queue()

        try:
            # Get orchestrator
            orchestrator: PlumeOrchestrator = fastapi_request.app.state.orchestrator

            # Inject queue into state for discussion_node to use
            # This is a hack but works for streaming
            orchestrator._current_queue = message_queue

            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'session_id': request.session_id or 'new'})}\n\n"

            # Start processing in background task
            process_task = asyncio.create_task(
                orchestrator.process(
                    input_text=request.message,
                    mode=request.mode,
                    conversation_id=request.conversation_id,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    context_ids=request.context_ids,
                    _sse_queue=message_queue  # Pass queue
                )
            )

            # Stream messages from queue
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(message_queue.get(), timeout=0.5)

                    # Send message as SSE
                    yield f"data: {json.dumps(message)}\n\n"

                except asyncio.TimeoutError:
                    # No message, check if processing done
                    if process_task.done():
                        break

                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

            # Get final result
            result = await process_task

            # Send final response
            yield f"data: {json.dumps({'type': 'complete', 'result': result})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        finally:
            # Cleanup
            orchestrator._current_queue = None

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

---

### **4. Modifier Discussion Node pour Queue**

**Update `discussion_node` pour utiliser queue SSE :**

```python
async def discussion_node(self, state: AgentState) -> AgentState:
    """Handle AutoGen discussion with streaming support"""

    input_text = state.get("input_text", "")
    sse_queue = state.get("_sse_queue")  # Get queue if streaming
    discussion_history = []

    try:
        from agents.autogen_discussion import create_discussion_agents

        plume_agent, mimir_agent, user_proxy = create_discussion_agents()

        # Message handler
        async def message_handler(sender, recipient, message):
            """Capture and stream messages"""

            content = message.get('content', '')
            agent_name = sender.name.lower() if hasattr(sender, 'name') else 'unknown'

            message_data = {
                'agent': agent_name,
                'message': content,
                'timestamp': datetime.now().isoformat(),
                'to': recipient.name.lower() if hasattr(recipient, 'name') else 'user'
            }

            # Store in history
            discussion_history.append(message_data)

            # Stream if queue exists
            if sse_queue:
                await sse_queue.put({
                    'type': 'agent_message',
                    **message_data
                })

            return message  # Return original message for AutoGen flow

        # Register handlers on both agents
        plume_agent.register_hook('process_message_before_send', message_handler)
        mimir_agent.register_hook('process_message_before_send', message_handler)

        # Start discussion
        initial_recipient = plume_agent if 'plume' in input_text.lower() else mimir_agent

        result = await user_proxy.a_initiate_chat(
            recipient=initial_recipient,
            message=input_text
        )

        # Extract final response
        final_response = result.chat_history[-1].get('content', '') if result.chat_history else "Discussion terminée sans réponse claire"

        # Update state
        state["response"] = final_response
        state["agent_used"] = "discussion"
        state["agents_involved"] = ["plume", "mimir"]
        state["discussion_history"] = discussion_history

        logger.info(f"Discussion completed: {len(discussion_history)} exchanges")

    except Exception as e:
        logger.error(f"Discussion failed: {str(e)}")
        state["response"] = f"Erreur lors de la discussion : {str(e)}"
        state["agent_used"] = "error"
        state["errors"].append({"node": "discussion", "error": str(e)})

    return state
```

---

### **5. AutoGen Agents Setup**

**Fichier :** `backend/agents/autogen_discussion.py`

```python
"""
AutoGen Multi-Agent Discussion Setup
Plume and Mimir collaborate on complex tasks
"""

from autogen import ConversableAgent, UserProxyAgent
from config import settings
import logging

logger = logging.getLogger(__name__)

def create_discussion_agents():
    """
    Create Plume, Mimir and UserProxy for discussion
    """

    # LLM Config
    llm_config = {
        "model": "claude-3-5-sonnet-20241022",
        "api_key": settings.ANTHROPIC_API_KEY,
        "api_type": "anthropic",
        "temperature": 0.7,
        "max_tokens": 2000
    }

    # Plume Agent - Restitution & Reformulation
    plume_agent = ConversableAgent(
        name="Plume",
        system_message="""Tu es Plume, agent de restitution parfaite.

        Tes compétences :
        - Capturer et reformuler des idées avec précision
        - Structurer du contenu de manière claire
        - Créer des notes bien organisées

        Ton rôle dans la discussion :
        - Tu prends en charge les tâches de création, reformulation, structuration
        - Tu collabores avec Mimir quand il faut chercher dans les archives
        - Tu es direct et précis dans tes réponses
        """,
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3
    )

    # Mimir Agent - RAG Search & Knowledge
    mimir_agent = ConversableAgent(
        name="Mimir",
        system_message="""Tu es Mimir, archiviste intelligent et expert en recherche.

        Tes compétences :
        - Recherche avancée dans la base de connaissances (RAG)
        - Trouver des connections entre notes
        - Contextualiser l'information

        Ton rôle dans la discussion :
        - Tu prends en charge les recherches et analyses de notes
        - Tu collabores avec Plume quand il faut reformuler ou créer du contenu
        - Tu cites tes sources et expliques tes trouvailles
        """,
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3
    )

    # User Proxy - Represents user, terminates conversation
    user_proxy = UserProxyAgent(
        name="User",
        system_message="Utilisateur humain qui pose des questions.",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,  # Never auto-reply
        code_execution_config=False
    )

    # Set up discussion pattern
    # Plume can talk to Mimir and vice versa
    plume_agent.register_nested_chats(
        trigger=mimir_agent,
        chat_queue=[
            {
                "recipient": mimir_agent,
                "message": "J'ai besoin de ton aide sur cette recherche",
                "max_turns": 2
            }
        ]
    )

    mimir_agent.register_nested_chats(
        trigger=plume_agent,
        chat_queue=[
            {
                "recipient": plume_agent,
                "message": "Peux-tu reformuler ces résultats ?",
                "max_turns": 2
            }
        ]
    )

    return plume_agent, mimir_agent, user_proxy
```

---

## 📋 FORMAT SSE EVENTS

**Types d'événements streamés :**

### **1. Start Event**
```json
{
  "type": "start",
  "session_id": "uuid",
  "timestamp": "2025-09-30T10:00:00Z"
}
```

### **2. Agent Message Event**
```json
{
  "type": "agent_message",
  "agent": "plume|mimir",
  "content": "Message de l'agent...",
  "to": "mimir|plume|user",
  "timestamp": "2025-09-30T10:00:05Z"
}
```

### **3. Processing Event**
```json
{
  "type": "processing",
  "node": "routing|context|discussion",
  "status": "started|completed",
  "timestamp": "2025-09-30T10:00:10Z"
}
```

### **4. Complete Event**
```json
{
  "type": "complete",
  "result": {
    "response": "Réponse finale...",
    "agent_used": "discussion",
    "agents_involved": ["plume", "mimir"],
    "discussion_history": [
      {
        "agent": "plume",
        "message": "...",
        "to": "mimir",
        "timestamp": "..."
      }
    ],
    "processing_time_ms": 3456,
    "tokens_used": 1234,
    "cost_eur": 0.0123
  }
}
```

### **5. Error Event**
```json
{
  "type": "error",
  "error": "Message d'erreur",
  "timestamp": "2025-09-30T10:00:15Z"
}
```

### **6. Keepalive Event**
```json
{
  "type": "keepalive"
}
```

---

## ✅ CHECKLIST DE TÂCHES

### **Setup**
- [ ] Créer fichier `agents/autogen_discussion.py`
- [ ] Installer AutoGen v0.4 (si pas déjà fait)
- [ ] Vérifier variables env ANTHROPIC_API_KEY

### **Orchestrator Modifications**
- [ ] Créer `discussion_node()` avec capture messages
- [ ] Modifier `routing_node()` pour détection prénoms
- [ ] Ajouter support `_sse_queue` dans AgentState
- [ ] Tester graph flow avec nouveau node

### **SSE Streaming**
- [ ] Créer endpoint `/orchestrated/stream`
- [ ] Implémenter `event_stream()` generator
- [ ] Gérer queue messages async
- [ ] Tester keepalive et timeouts

### **AutoGen Setup**
- [ ] Créer Plume & Mimir ConversableAgents
- [ ] Configurer system messages
- [ ] Setup nested chats entre agents
- [ ] Tester discussion simple Plume ↔ Mimir

### **Routing Prénoms**
- [ ] Détecter "Plume" seul → force Plume
- [ ] Détecter "Mimir" seul → force Mimir
- [ ] Détecter les deux → mode discussion
- [ ] Fallback intent classifier si aucun prénom

### **Tests**
- [ ] Test discussion simple : "Plume et Mimir, cherchez RAG"
- [ ] Test routing prénom : "Mimir, trouve mes notes sur Python"
- [ ] Test streaming SSE : vérifier messages temps réel
- [ ] Test error handling : discussion qui échoue
- [ ] Test keepalive : connexion longue

### **Déploiement**
- [ ] Vérifier AutoGen dependencies dans requirements.txt
- [ ] Push vers Render
- [ ] Tester streaming en production (nginx buffering?)
- [ ] Monitor logs AutoGen

---

## 🎯 CRITÈRES DE SUCCÈS

**Discussion AutoGen :**
- ✅ Plume et Mimir peuvent discuter entre eux
- ✅ Messages internes capturés dans discussion_history
- ✅ Réponse finale cohérente avec discussion

**Streaming SSE :**
- ✅ Messages streamés en temps réel (< 500ms latency)
- ✅ Keepalive fonctionne (pas de timeout)
- ✅ Event "complete" avec résultat final
- ✅ Error handling propre

**Routing Prénoms :**
- ✅ "Plume" seul → force Plume
- ✅ "Mimir" seul → force Mimir
- ✅ Les deux → mode discussion
- ✅ Aucun → intent classifier

**Performance :**
- ✅ Discussion complète < 10s
- ✅ Streaming fluide sans buffering
- ✅ Pas de memory leaks (queue cleanup)

**Déploiement :**
- ✅ Fonctionne en production Render
- ✅ Logs clairs pour debug
- ✅ Nginx ne buffer pas SSE

---

## 📝 NOTES IMPORTANTES

1. **SSE vs WebSocket :** SSE choisi pour simplicité (unidirectionnel suffit). WebSocket possible future si besoin bidirectionnel.

2. **Queue Hack :** Passer queue via state est un hack temporaire. Mieux : event emitter pattern. À refactorer si temps.

3. **AutoGen v0.4 :** Utiliser async API (`a_initiate_chat`) pour non-blocking. Version sync bloque event loop.

4. **Nginx Buffering :** En production, Render/nginx peuvent buffer SSE. Ajouter header `X-Accel-Buffering: no`.

5. **Keepalive :** Nécessaire pour éviter timeout proxy (30s default). Envoyer keepalive toutes les 15s.

6. **Discussion Termination :** AutoGen peut tourner indéfiniment. Limiter avec `max_consecutive_auto_reply=3`.

7. **Cost Monitoring :** Chaque message AutoGen = API call. Discussion 10 messages = ~20 API calls (Plume + Mimir). Monitorer coûts.

8. **Routing Priority :**
   1. Prénom explicite (ex: "Plume, ...")
   2. Mode forcé (ex: mode="mimir")
   3. Intent classifier auto

---

**Document créé par :** Leo (Architecture)
**Pour agent :** Koda (Backend Specialist)
**Phase :** 2.2 Phase 1 (Parallèle)
**Date :** 30 septembre 2025
