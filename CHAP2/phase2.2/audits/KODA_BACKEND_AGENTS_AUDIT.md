# 🤖 Koda Backend Agents Audit - SCRIBE CHAP2

**Agent :** Koda (Backend Specialist)
**Mission :** Audit architecture agents backend actuelle + Roadmap architecture agentique avancée
**Date :** 30 septembre 2025
**Context :** Chapitre 2 "Sur le Chantier" - Architecture agentique complète

---

## 📋 ARCHITECTURE AGENTS ACTUELLE

### Structure Backend

```
backend/
├── agents/
│   ├── state.py              # AgentState TypedDict pour LangGraph ✅
│   ├── plume.py              # Agent restitution perfectionniste ✅
│   ├── mimir.py              # Agent archiviste RAG ✅
│   ├── orchestrator.py       # LangGraph workflow (EXISTS mais PAS UTILISÉ ⚠️)
│   └── autogen_agents.py     # AutoGen v0.4 integration (EXISTS mais PAS UTILISÉ ⚠️)
│
├── services/
│   ├── transcription.py      # Whisper OpenAI ✅
│   ├── embeddings.py         # text-embedding-3-large ✅
│   ├── rag.py                # RAG hybrid search ✅
│   ├── cache.py              # Redis caching ✅
│   ├── storage.py            # Supabase client ✅
│   ├── monitoring_service.py # Metrics & cost tracking ✅
│   └── realtime_service.py   # Supabase realtime ✅
│
├── api/
│   ├── chat.py               # Chat endpoints (agents direct, pas orchestrator) ⚠️
│   ├── upload.py             # Document upload ✅
│   ├── search.py             # Search endpoints (TODO) ⚠️
│   └── health.py             # Health checks ✅
│
└── main.py                    # FastAPI app ✅
```

---

## ✅ AGENTS PRODUCTION - DÉTAILS

### 1. Plume Agent (`agents/plume.py`)

**Status :** ✅ OPÉRATIONNEL

**Responsabilités :**
- Restitution parfaite des informations
- Transcription audio via Whisper
- Reformulation selon contexte
- Correction linguistique sans altération

**Architecture :**
```python
class PlumeAgent:
    - client: Anthropic (Claude API)
    - model: claude-opus-3 (configurable)
    - system_prompt: Instructions détaillées fidélité

    async def process(input_text, state) -> Dict:
        1. Analyze input context (type, intent)
        2. Check cache (LLM response cache)
        3. Prepare prompt with context
        4. Call Claude API
        5. Format response (text + HTML)
        6. Cache result
        7. Track costs (tokens, EUR)
```

**System Prompt :**
- **Fidélité absolue** : Aucune invention, aucune extrapolation
- **Précision** : Chaque détail préservé
- **Clarté** : Structure optimale
- **Exhaustivité** : Aucune omission

**Features Implémentées :**
- ✅ Cache intelligent (Redis)
- ✅ Cost tracking (tokens + EUR)
- ✅ Context analysis
- ✅ HTML formatting
- ✅ Error handling gracieux

**Intégration API :**
```python
# api/chat.py
plume_agent = PlumeAgent()  # Instanciation directe

async def process_message(agent_name, message, ...):
    agent = get_agent(agent_name)  # "plume" ou "mimir"
    response = await agent.process_message(...)
```

**Limitations Actuelles :**
- ❌ Pas de memory conversation long-terme
- ❌ Pas d'orchestration LangGraph
- ❌ Pas de coordination avec Mimir
- ❌ Routing manuel (user choisit)

---

### 2. Mimir Agent (`agents/mimir.py`)

**Status :** ✅ OPÉRATIONNEL

**Responsabilités :**
- Archivage et recherche méthodique
- RAG hybrid search (vector + fulltext + BM25)
- Web search integration (Perplexity + Tavily)
- Connexions intelligentes entre concepts
- Synthèse sources multiples

**Architecture :**
```python
class MimirAgent:
    - client: Anthropic (Claude API)
    - model: claude-sonnet-3.5 (configurable)
    - system_prompt: Instructions archiviste méthodique

    async def process(input_text, context, state) -> Dict:
        1. Analyze query (intent, keywords)
        2. Check cache
        3. RAG retrieval (vector + fulltext + BM25)
        4. Web search si nécessaire (Perplexity/Tavily)
        5. Synthesize context + web results
        6. Call Claude API with enriched context
        7. Format response with references
        8. Cache result
        9. Track costs
```

**System Prompt :**
- **Méthodologie** : Approche systématique
- **Contextualisation** : Utilise toujours le contexte fourni
- **Connexions** : Identifie les liens entre concepts
- **Références** : Sources précises et vérifiables
- **Exhaustivité** : Recherche complète

**RAG Integration :**
```python
# services/rag.py - Hybrid search
1. Vector Search (pgvector cosine similarity)
2. Full-Text Search (PostgreSQL tsvector)
3. BM25 Ranking (statistical relevance)
4. Cross-Encoder Re-ranking (top-K)
5. Web Search (Perplexity API + Tavily API)
6. Result fusion + scoring
```

**Features Implémentées :**
- ✅ RAG state-of-the-art (multi-strategy)
- ✅ Web search temps réel
- ✅ Cache intelligent
- ✅ Cost tracking
- ✅ Sources tracking avec confidence
- ✅ Auto-tuning paramètres RAG

**Limitations Actuelles :**
- ❌ Pas de knowledge graph persisté
- ❌ Pas d'apprentissage continu (feedback loop)
- ❌ Pas de coordination avec Plume
- ❌ Routing manuel

---

## ⚠️ ORCHESTRATION - CODE EXISTE MAIS PAS UTILISÉ

### 3. LangGraph Orchestrator (`agents/orchestrator.py`)

**Status :** ⚠️ CODE COMPLET MAIS NON INTÉGRÉ API

**Architecture Workflow :**
```python
class PlumeOrchestrator:
    - graph: StateGraph(AgentState)
    - app: Compiled workflow with MemorySaver

    Nodes:
    1. intake_node          → Validation input
    2. transcription_node   → Whisper si voice
    3. router_node          → Décision agent(s) ⭐
    4. context_retrieval    → RAG retrieval
    5. plume_node           → Agent Plume
    6. mimir_node           → Agent Mimir
    7. discussion_node      → AutoGen multi-agents
    8. storage_node         → Supabase save
    9. finalize_node        → Response formatting
```

**Workflow Graph :**
```
START
  ↓
intake (validation)
  ↓
[voice?] → transcription → router
  ↓                         ↓
router_decision ⭐ (INTELLIGENT ROUTING)
  ↓         ↓         ↓
plume    mimir   discussion
  ↓         ↓         ↓
      storage
         ↓
      finalize
         ↓
        END
```

**Router Decision Logic :**
```python
def router_decision(state: AgentState) -> str:
    mode = state.get("mode", "auto")

    if mode == "plume":
        return "plume_only"
    elif mode == "mimir":
        return "mimir_only"
    elif mode == "discussion":
        return "discussion"
    else:  # auto
        # TODO: Intelligent routing based on intent
        # Analyze input → classify → route
        return "plume_only"  # Default fallback
```

**Checkpointing (Memory) :**
```python
memory = MemorySaver()  # In-memory checkpointing
app = graph.compile(checkpointer=memory)

# Permet de:
# - Resume conversations
# - Replay workflow steps
# - Debug state transitions
```

**Problème :** ❌ **PAS INTÉGRÉ DANS API**
```python
# api/chat.py - Utilise agents DIRECTS
plume_agent = PlumeAgent()  # Pas d'orchestrator
mimir_agent = MimirAgent()

# Devrait être:
orchestrator = PlumeOrchestrator()
await orchestrator.initialize()
response = await orchestrator.process(message, state)
```

**Ce qui manque pour intégration :**
1. Instanciation orchestrator dans API
2. Endpoint `/chat/orchestrated` utilisant LangGraph
3. Intent classification pour routing auto
4. Checkpointing Supabase (au lieu de MemorySaver)
5. Monitoring workflow steps
6. Error recovery & retry logic

---

### 4. AutoGen Discussion (`agents/autogen_agents.py`)

**Status :** ⚠️ CODE SETUP MAIS PAS UTILISÉ

**Architecture AutoGen v0.4 :**
```python
class AutoGenDiscussion:
    - plume_agent: AssistantAgent (AutoGen)
    - mimir_agent: AssistantAgent (AutoGen)
    - model_client: OpenAIChatCompletionClient
    - group_chat: RoundRobinGroupChat

    async def discuss(topic, context, max_turns=5):
        1. Initialize agents with system messages
        2. Create RoundRobinGroupChat
        3. Add termination conditions:
           - TextMentionTermination("TERMINATE")
           - MaxMessageTermination(max_turns)
        4. Run discussion loop
        5. Extract consensus/result
        6. Format final response
```

**Agents AutoGen :**
```python
plume_agent = AssistantAgent(
    name="Plume",
    model_client=model_client,
    system_message="Spécialisée restitution parfaite..."
)

mimir_agent = AssistantAgent(
    name="Mimir",
    model_client=model_client,
    system_message="Archiviste méthodique..."
)

group_chat = RoundRobinGroupChat([plume_agent, mimir_agent])
```

**Use Cases AutoGen :**
- Questions complexes nécessitant expertise multiple
- Débat Plume (fidélité) vs Mimir (enrichissement)
- Validation croisée informations
- Synthèse collaborative

**Problème :** ❌ **PAS INTÉGRÉ DANS ORCHESTRATOR NI API**
```python
# orchestrator.py - discussion_node existe mais minimal
async def discussion_node(state: AgentState):
    # TODO: Implement AutoGen discussion
    pass
```

**Ce qui manque pour intégration :**
1. Appel AutoGenDiscussion dans orchestrator discussion_node
2. Intent detection "discussion mode" (questions complexes)
3. Configuration model_client pour Claude (pas seulement OpenAI)
4. Termination conditions customisées
5. Conversation history pour AutoGen
6. Cost tracking discussions multi-agents

---

## 🧩 SERVICES IA - DÉTAILS

### Transcription Service (`services/transcription.py`)

**Status :** ✅ PRODUCTION READY

**Features :**
- OpenAI Whisper API (whisper-1 model)
- Formats supportés : webm, mp3, wav, m4a, ogg
- Cache intelligent (Redis avec validation audio hash)
- Chunking automatique si >25MB
- Language detection
- Cost tracking (€0.006 / minute)

---

### Embeddings Service (`services/embeddings.py`)

**Status :** ✅ PRODUCTION READY

**Features :**
- Model : text-embedding-3-large (1536 dimensions)
- Chunking sémantique (overlap 50 tokens)
- Batch processing optimisé (100 chunks/batch)
- Cache Redis persistant (TTL 7 jours)
- Cost tracking (€0.00013 / 1K tokens)

---

### RAG Service (`services/rag.py`)

**Status :** ✅ STATE-OF-THE-ART

**Strategies :**
```python
1. Vector Search (pgvector):
   - Cosine similarity sur embeddings
   - Top-K results (configurable)
   - Threshold similarity (0.7 default)

2. Full-Text Search (PostgreSQL):
   - tsvector + tsquery
   - Ranking tf-idf
   - Language-aware (français)

3. BM25 Ranking:
   - Statistical relevance
   - Term frequency + document frequency
   - Normalization document length

4. Cross-Encoder Re-ranking:
   - Top-K refinement
   - Query-document relevance score
   - Semantic understanding

5. Result Fusion:
   - Weighted scoring (vector 0.5 + fulltext 0.3 + BM25 0.2)
   - Deduplication
   - Confidence scores
```

**Auto-Tuning :**
- Learning optimal weights selon performance queries
- Adaptation threshold similarity
- Dynamic K adjustment

**Web Search Integration :**
```python
# services/rag.py
if confidence < 0.6 or no_results:
    # Fallback web search
    web_results = await perplexity_search(query)
    # ou
    web_results = await tavily_search(query)

    # Merge local + web results
    combined = merge_results(local, web)
```

---

### Cache Service (`services/cache.py`)

**Status :** ✅ PRODUCTION READY

**Cache Layers :**
```python
1. LLM Response Cache:
   - Key: hash(prompt + model + params)
   - TTL: 24h (ajustable)
   - Savings: ~60% API calls repetés

2. Embeddings Cache:
   - Key: hash(text)
   - TTL: 7 jours
   - Savings: ~80% embedding requests

3. RAG Results Cache:
   - Key: hash(query + filters)
   - TTL: 1h
   - Savings: ~50% searches

4. Transcription Cache:
   - Key: hash(audio_data)
   - TTL: 30 jours (audio stable)
   - Savings: ~90% transcriptions identiques
```

**Redis Configuration :**
```python
- Persistence: RDB snapshots
- Eviction policy: allkeys-lru
- Max memory: 512MB (configurable)
- Connection pooling
```

---

### Storage Service (`services/storage.py`)

**Status :** ✅ PRODUCTION READY

**Supabase Integration :**
```python
Tables:
- documents        → Upload + metadata
- chunks           → Document chunks + embeddings
- conversations    → Chat history
- messages         → Individual messages
- notes            → User notes (Plume outputs)
- searches         → Search history + analytics
```

**RLS (Row Level Security) :**
- User isolation (multi-user ready)
- Read/Write permissions
- Audit logging

---

### Monitoring Service (`services/monitoring_service.py`)

**Status :** ✅ PRODUCTION READY

**Metrics Tracked :**
```python
- API response times (P50/P95/P99)
- Agent processing times
- LLM API calls (tokens, costs)
- Cache hit rates
- Error rates
- RAG search performance
- WebSocket connections active
```

**Cost Tracking :**
```python
- Claude API : tokens × €0.015/1K (Opus)
- OpenAI Whisper : minutes × €0.006
- OpenAI Embeddings : tokens × €0.00013/1K
- Perplexity API : requests × €0.005
- Tavily API : searches × €0.01

Total cost per conversation tracked
Alerting si budget dépassé
```

---

## 🚧 CE QUI MANQUE - DÉTAILS DÉVELOPPÉS

### 1. ❌ LangGraph Orchestrator Integration

**Problème :** Code orchestrator complet mais jamais appelé par l'API

**Impact :**
- Pas de workflow structuré
- Pas de checkpointing conversations
- Pas de retry logic automatique
- Pas de monitoring steps

**Solution Requise :**

**Step 1: Instanciation orchestrator**
```python
# main.py - Lifespan startup
orchestrator = PlumeOrchestrator()
await orchestrator.initialize()
app.state.orchestrator = orchestrator
```

**Step 2: Nouveau endpoint orchestré**
```python
# api/chat.py
@router.post("/orchestrated")
async def chat_orchestrated(
    request: ChatRequest,
    orchestrator: PlumeOrchestrator = Depends(get_orchestrator)
):
    # Create initial state
    state = create_initial_state(
        input_text=request.message,
        mode=request.mode or "auto",
        session_id=request.session_id
    )

    # Run workflow
    result = await orchestrator.run(state)

    # Return final response
    return {
        "message": result["final_output"],
        "agent_used": result["agent_used"],
        "agents_involved": result["agents_involved"],
        "processing_time_ms": result["processing_time_ms"],
        "tokens_used": result["tokens_used"],
        "cost_eur": result["cost_eur"]
    }
```

**Step 3: Checkpoint persistence Supabase**
```python
# agents/orchestrator.py
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(conn_string=settings.SUPABASE_URL)
app = graph.compile(checkpointer=checkpointer)

# Permet:
# - Resume conversations interrupted
# - History workflow state
# - Replay & debug
# - Multi-session support
```

**Estimation :** 3-4 jours

---

### 2. ❌ Routing Automatique Intelligent

**Problème :** User choisit manuellement agent (Plume/Mimir), pas de routing auto

**Intent Classification Requise :**
```python
# services/intent_classifier.py

class IntentClassifier:
    """
    Classifie intent utilisateur pour router vers agent approprié
    """

    INTENTS = {
        "restitution": ["reformule", "résume", "transcris", "explique"],
        "recherche": ["cherche", "trouve", "recherche", "où est", "quel"],
        "discussion": ["compare", "débat", "analyse", "quelle différence"],
        "unknown": []
    }

    async def classify(self, input_text: str) -> Dict[str, Any]:
        """
        Classifie intent avec LLM léger (Claude Haiku)
        ou
        Classification basée keywords + embeddings similarity
        """

        # Option A: LLM classification (plus précis)
        prompt = f"""
        Classifie l'intent utilisateur parmi:
        - restitution: reformulation, résumé, transcription
        - recherche: recherche dans connaissances, RAG
        - discussion: question complexe, débat, analyse multi-facettes

        Input: "{input_text}"

        Réponds uniquement: restitution | recherche | discussion
        """

        intent = await claude_haiku_call(prompt)
        confidence = 0.9  # LLM confidence

        # Option B: Keyword + embedding (plus rapide, moins cher)
        keywords_found = self._check_keywords(input_text)
        embedding_similarity = await self._embedding_similarity(input_text)

        intent = self._decide_intent(keywords_found, embedding_similarity)
        confidence = embedding_similarity["score"]

        return {
            "intent": intent,
            "confidence": confidence,
            "reasoning": "..."
        }
```

**Router Node Update :**
```python
# agents/orchestrator.py

async def router_node(self, state: AgentState) -> AgentState:
    """Route to appropriate agent(s) based on intent"""

    mode = state.get("mode", "auto")

    if mode == "auto":
        # Intelligent routing
        intent_result = await intent_classifier.classify(state["input"])

        if intent_result["intent"] == "restitution":
            state["mode"] = "plume"
        elif intent_result["intent"] == "recherche":
            state["mode"] = "mimir"
        elif intent_result["intent"] == "discussion":
            state["mode"] = "discussion"
        else:
            # Default fallback based on context
            has_context = len(state.get("context", [])) > 0
            state["mode"] = "mimir" if has_context else "plume"

    return state

def router_decision(self, state: AgentState) -> str:
    """Decide routing based on state mode"""
    mode = state.get("mode")

    routing = {
        "plume": "plume_only",
        "mimir": "mimir_only",
        "discussion": "discussion"
    }

    return routing.get(mode, "plume_only")
```

**Estimation :** 4-5 jours

---

### 3. ❌ AutoGen Discussion Integration

**Problème :** Code AutoGen setup mais jamais utilisé dans workflow

**Integration Required :**

**Step 1: Discussion node implementation**
```python
# agents/orchestrator.py

from agents.autogen_agents import AutoGenDiscussion

autogen_discussion = AutoGenDiscussion()

async def discussion_node(self, state: AgentState) -> AgentState:
    """
    Multi-agent discussion via AutoGen
    Pour questions complexes nécessitant débat
    """

    topic = state["input"]
    context = state.get("context", [])

    # Run AutoGen discussion
    discussion_result = await autogen_discussion.discuss(
        topic=topic,
        context=context,
        max_turns=5,
        termination_keywords=["TERMINATE", "CONSENSUS"]
    )

    # Extract result
    state["discussion_history"] = discussion_result["messages"]
    state["final_output"] = discussion_result["consensus"]
    state["agents_involved"] = ["plume", "mimir"]

    # Track costs
    state["tokens_used"] += discussion_result["tokens_used"]
    state["cost_eur"] += discussion_result["cost_eur"]

    add_processing_step(state, "autogen_discussion_completed")

    return state
```

**Step 2: Claude model client AutoGen**
```python
# agents/autogen_agents.py

from autogen_ext.models.anthropic import AnthropicChatCompletionClient

# Use Claude instead of OpenAI
self.model_client = AnthropicChatCompletionClient(
    model="claude-3-5-sonnet-20241022",
    api_key=settings.CLAUDE_API_KEY,
    temperature=0.3,
    max_tokens=2000
)
```

**Step 3: Termination conditions customisées**
```python
# Custom termination: when consensus reached
class ConsensusTermination(TerminationCondition):
    async def is_terminated(self, messages: List) -> bool:
        last_message = messages[-1].content

        # Check si agents agree
        consensus_keywords = ["d'accord", "consensus", "je confirme"]
        return any(kw in last_message.lower() for kw in consensus_keywords)

group_chat = RoundRobinGroupChat(
    [plume_agent, mimir_agent],
    termination_condition=ConsensusTermination() | MaxMessageTermination(5)
)
```

**Estimation :** 5-6 jours

---

### 4. ❌ Memory Partagée & Long-Terme

**Problème :** Pas de memory conversation persistée, chaque appel isolé

**Solution : Conversation Memory System**

**Architecture Memory :**
```python
# services/memory_service.py

class ConversationMemory:
    """
    Gère memory long-terme conversations
    - Short-term: derniers N messages (context window)
    - Long-term: embeddings + RAG sur history
    - User preferences: patterns usage, topics favoris
    """

    async def get_conversation_context(
        self,
        conversation_id: str,
        n_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Récupère contexte conversation
        - Derniers N messages (short-term)
        - Messages similaires history (long-term RAG)
        - User preferences
        """

        # Short-term: derniers messages
        recent_messages = await self.get_recent_messages(
            conversation_id,
            limit=n_messages
        )

        # Long-term: RAG sur history
        current_topic = self._extract_topic(recent_messages)
        similar_past = await self.search_conversation_history(
            user_id=user_id,
            query=current_topic,
            limit=5
        )

        # User preferences
        preferences = await self.get_user_preferences(user_id)

        return {
            "recent_messages": recent_messages,
            "similar_past_conversations": similar_past,
            "user_preferences": preferences
        }
```

**Database Schema :**
```sql
-- Conversations table (exists)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID,
    title TEXT,
    summary TEXT,  -- NEW: Auto-generated summary
    agents_used TEXT[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata JSONB
);

-- Messages table (exists)
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role TEXT,  -- 'user' | 'plume' | 'mimir'
    content TEXT,
    embedding VECTOR(1536),  -- NEW: Pour RAG sur history
    metadata JSONB,
    created_at TIMESTAMP
);

-- NEW: User preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY,
    preferred_agent TEXT,  -- 'plume' | 'mimir' | 'auto'
    topics_of_interest TEXT[],
    interaction_patterns JSONB,  -- Usage analytics
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Integration Orchestrator :**
```python
# agents/orchestrator.py

async def intake_node(self, state: AgentState) -> AgentState:
    """Enriched intake with memory"""

    conversation_id = state.get("conversation_id")

    if conversation_id:
        # Load conversation context
        memory_context = await memory_service.get_conversation_context(
            conversation_id=conversation_id,
            n_messages=10
        )

        state["context"] = memory_context["recent_messages"]
        state["similar_past"] = memory_context["similar_past_conversations"]
        state["user_preferences"] = memory_context["user_preferences"]

    return state
```

**Estimation :** 6-7 jours

---

### 5. ❌ Agent Learning & Feedback Loop

**Problème :** Agents statiques, pas d'amélioration continue

**Solution : Feedback & Learning System**

**Architecture :**
```python
# services/feedback_service.py

class AgentFeedbackSystem:
    """
    Collecte feedback utilisateur + metrics
    Améliore agents via fine-tuning ou prompt optimization
    """

    async def collect_feedback(
        self,
        message_id: str,
        feedback: Dict[str, Any]
    ):
        """
        Feedback utilisateur:
        - Thumbs up/down
        - Qualité réponse (1-5)
        - Corrections proposées
        - Tags (helpful, accurate, clear, etc.)
        """

        await supabase.table("feedback").insert({
            "message_id": message_id,
            "rating": feedback["rating"],
            "tags": feedback["tags"],
            "corrections": feedback.get("corrections"),
            "timestamp": datetime.utcnow()
        })

    async def analyze_performance(self, agent_name: str) -> Dict:
        """
        Analyse performance agent
        - Average rating
        - Common issues
        - Success patterns
        - Improvement suggestions
        """

        feedback_data = await self._get_agent_feedback(agent_name)

        metrics = {
            "avg_rating": self._calculate_avg_rating(feedback_data),
            "thumbs_up_ratio": self._calculate_ratio(feedback_data),
            "common_issues": self._extract_issues(feedback_data),
            "success_patterns": self._extract_patterns(feedback_data)
        }

        return metrics

    async def optimize_prompts(self, agent_name: str):
        """
        Optimise system prompts basé sur feedback
        - Identifie weaknesses
        - Generate improved prompts
        - A/B testing
        """

        performance = await self.analyze_performance(agent_name)

        if performance["avg_rating"] < 4.0:
            # Generate improved prompt
            improved_prompt = await self._generate_improved_prompt(
                current_prompt=agent.system_prompt,
                issues=performance["common_issues"],
                successes=performance["success_patterns"]
            )

            # A/B test
            await self._start_ab_test(
                agent_name=agent_name,
                variant_a=agent.system_prompt,
                variant_b=improved_prompt
            )
```

**Database Schema :**
```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    message_id UUID REFERENCES messages(id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    tags TEXT[],
    corrections TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE agent_performance (
    agent_name TEXT,
    date DATE,
    avg_rating FLOAT,
    total_interactions INT,
    thumbs_up INT,
    thumbs_down INT,
    PRIMARY KEY (agent_name, date)
);
```

**Estimation :** 7-8 jours

---

### 6. ❌ Knowledge Graph Persisté

**Problème :** Connexions concepts calculées à la volée, pas persistées

**Solution : Knowledge Graph avec Neo4j ou PostgreSQL**

**Architecture :**
```python
# services/knowledge_graph.py

class KnowledgeGraph:
    """
    Graph persisté des concepts et connexions
    Améliore RAG avec connexions sémantiques
    """

    async def add_concept(self, concept: str, metadata: Dict):
        """Add concept to graph"""
        # Neo4j: CREATE (c:Concept {name: concept, ...})
        # ou PostgreSQL: INSERT INTO concepts ...

    async def add_connection(
        self,
        concept_a: str,
        concept_b: str,
        relationship: str,
        strength: float
    ):
        """Add connection between concepts"""
        # Neo4j: MATCH (a:Concept), (b:Concept)
        #        CREATE (a)-[:relationship {strength: strength}]->(b)

    async def find_related_concepts(
        self,
        concept: str,
        max_depth: int = 2
    ) -> List[Dict]:
        """Find related concepts via graph traversal"""
        # Neo4j: MATCH (c:Concept {name: concept})-[*1..max_depth]-(related)
        #        RETURN related

    async def get_concept_cluster(
        self,
        concept: str
    ) -> List[str]:
        """Get cluster of highly connected concepts"""
        # Community detection algorithms
        # Louvain, Label Propagation, etc.
```

**Integration Mimir :**
```python
# agents/mimir.py

async def process(self, input_text, context, state):
    # ... existing RAG search ...

    # Enrich with knowledge graph
    concepts = self._extract_concepts(input_text)

    for concept in concepts:
        related = await knowledge_graph.find_related_concepts(concept)
        context.extend(related)

    # ... continue with Claude API call ...
```

**Estimation :** 8-10 jours

---

### 7. ❌ Cost Optimization Active

**Problème :** Cost tracking existe, mais pas d'optimisation automatique

**Solution : Cost Optimizer**

**Features :**
```python
# services/cost_optimizer.py

class CostOptimizer:
    """
    Optimise coûts API intelligemment
    - Model selection (Claude Opus vs Sonnet vs Haiku)
    - Cache aggressif
    - Batch processing
    - Rate limiting intelligent
    """

    async def select_model(
        self,
        task_complexity: str,
        user_tier: str
    ) -> str:
        """
        Sélectionne model optimal selon complexité

        Simple tasks → Claude Haiku (€0.00025/1K)
        Medium tasks → Claude Sonnet (€0.003/1K)
        Complex tasks → Claude Opus (€0.015/1K)
        """

        model_mapping = {
            ("simple", "free"): "claude-3-haiku-20240307",
            ("simple", "pro"): "claude-3-5-sonnet-20241022",
            ("medium", "free"): "claude-3-5-sonnet-20241022",
            ("medium", "pro"): "claude-3-5-sonnet-20241022",
            ("complex", "free"): "claude-3-5-sonnet-20241022",
            ("complex", "pro"): "claude-opus-3-20240229"
        }

        return model_mapping.get((task_complexity, user_tier))

    async def check_budget(self, user_id: str) -> Dict:
        """
        Vérifie budget utilisateur
        - Monthly spending
        - Remaining budget
        - Alerting si proche limite
        """

        spending = await self._get_monthly_spending(user_id)
        budget_limit = await self._get_user_budget_limit(user_id)

        if spending >= budget_limit * 0.9:
            await self._send_budget_alert(user_id)

        return {
            "spending": spending,
            "limit": budget_limit,
            "remaining": budget_limit - spending,
            "percentage_used": (spending / budget_limit) * 100
        }
```

**Estimation :** 4-5 jours

---

### 8. ❌ Multi-User Support

**Problème :** Backend prêt (RLS Supabase) mais pas de contexte utilisateur

**Solution : User Context & Authentication**

**Architecture :**
```python
# api/auth.py (NEW)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Extract user from JWT token
    Validate with Supabase Auth
    """

    token = credentials.credentials

    try:
        user = await supabase.auth.get_user(token)
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

**Integration API :**
```python
# api/chat.py

@router.post("/message")
async def send_message(
    request: ChatRequest,
    user: Dict = Depends(get_current_user)  # NEW: User context
):
    # User context available
    user_id = user["id"]

    # Load user preferences
    preferences = await memory_service.get_user_preferences(user_id)

    # Process with user context
    response = await orchestrator.process(
        message=request.message,
        user_id=user_id,
        preferences=preferences
    )

    return response
```

**Estimation :** 5-6 jours

---

### 9. ❌ Streaming Responses (SSE)

**Problème :** Code existe mais pas complètement implémenté

**Solution : Streaming complet LangGraph + Claude**

**Architecture :**
```python
# api/chat.py

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: Dict = Depends(get_current_user)
):
    """Stream response tokens in real-time"""

    async def generate():
        # Create state
        state = create_initial_state(request.message, user_id=user["id"])

        # Stream workflow steps + LLM tokens
        async for event in orchestrator.stream(state):
            if event["type"] == "node_start":
                yield f"data: {json.dumps({'step': event['node']})}\n\n"

            elif event["type"] == "llm_token":
                yield f"data: {json.dumps({'token': event['token']})}\n\n"

            elif event["type"] == "node_end":
                yield f"data: {json.dumps({'step_complete': event['node']})}\n\n"

        # Final result
        yield f"data: {json.dumps({'done': True, 'result': state['final_output']})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**LangGraph Streaming :**
```python
# agents/orchestrator.py

async def stream(self, state: AgentState) -> AsyncGenerator:
    """Stream workflow execution events"""

    async for event in self.app.astream(state):
        yield event
```

**Estimation :** 3-4 jours

---

### 10. ❌ Error Recovery & Resilience

**Problème :** Error handling basique, pas de retry automatique

**Solution : Resilience Patterns**

**Features :**
```python
# utils/resilience.py

from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientAgent:
    """
    Wrapper pour agents avec resilience patterns
    - Retry avec exponential backoff
    - Circuit breaker
    - Fallback responses
    - Graceful degradation
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def call_agent_with_retry(
        self,
        agent: Any,
        input_text: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """Call agent with automatic retry"""

        try:
            response = await agent.process(input_text, state)
            return response
        except Exception as e:
            logger.warning(f"Agent call failed, retrying...", error=str(e))
            raise  # Will be retried by tenacity

    async def call_with_fallback(
        self,
        primary_agent: Any,
        fallback_agent: Any,
        input_text: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """Try primary, fallback to secondary if fails"""

        try:
            return await self.call_agent_with_retry(primary_agent, input_text, state)
        except Exception as e:
            logger.error("Primary agent failed, using fallback", error=str(e))
            return await fallback_agent.process(input_text, state)
```

**Circuit Breaker :**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api(url: str):
    """
    Circuit breaker pour APIs externes
    Si 5 failures → Open circuit (stop calls)
    Après 60s → Half-open (test 1 call)
    Si succès → Close circuit (resume calls)
    """
    response = await httpx.get(url)
    return response
```

**Estimation :** 4-5 jours

---

## 📦 NOUVELLES DÉPENDANCES BACKEND

```python
# requirements.txt - À ajouter

# LangGraph & orchestration
langgraph>=0.2.0                    # Graph workflow
langgraph-checkpoint-postgres       # Supabase checkpointing

# AutoGen v0.4
autogen-agentchat>=0.4.0.dev8
autogen-ext[anthropic]>=0.4.0.dev8  # Claude support
autogen-core>=0.4.0.dev8

# Resilience & reliability
tenacity>=8.2.0                     # Retry logic
circuitbreaker>=2.0.0               # Circuit breaker pattern

# Knowledge graph (option A: Neo4j)
neo4j>=5.15.0
neomodel>=5.2.0

# Knowledge graph (option B: PostgreSQL graph)
# (Already have PostgreSQL via Supabase)

# Intent classification
sentence-transformers>=2.2.0        # Semantic similarity
scikit-learn>=1.4.0                 # ML models

# Monitoring & observability
opentelemetry-api>=1.22.0          # Tracing
opentelemetry-sdk>=1.22.0
opentelemetry-instrumentation-fastapi
```

---

## 🎯 PRIORITÉS CHAP2 - SUGGESTION

### Phase 2.1 : Orchestration Foundation (Semaine 1-3)
**Priorité :** ⭐⭐⭐⭐⭐

1. **LangGraph Orchestrator Integration**
   - Instanciation dans API
   - Endpoint `/chat/orchestrated`
   - Checkpointing Supabase
   - Monitoring workflow steps

2. **Routing Automatique Intelligent**
   - Intent classifier (LLM ou embedding-based)
   - Router node logic
   - Confidence scoring
   - Fallback strategies

3. **Memory Partagée Conversations**
   - ConversationMemory service
   - Database schema updates
   - Integration orchestrator intake
   - Short-term + long-term context

**Estimation :** 15-18 jours

---

### Phase 2.2 : Multi-Agent Coordination (Semaine 4-6)
**Priorité :** ⭐⭐⭐⭐

4. **AutoGen Discussion Integration**
   - Discussion node implementation
   - Claude model client AutoGen
   - Termination conditions
   - Cost tracking discussions

5. **Agent Learning & Feedback**
   - Feedback collection system
   - Performance analytics
   - Prompt optimization (optional)
   - A/B testing framework

**Estimation :** 12-14 jours

---

### Phase 2.3 : Advanced Features (Semaine 7-9)
**Priorité :** ⭐⭐⭐

6. **Knowledge Graph**
   - Concept & connections persistence
   - Graph traversal queries
   - Integration Mimir RAG
   - Visualization (optional)

7. **Cost Optimization**
   - Model selection intelligent
   - Budget tracking per user
   - Alerts & throttling
   - Cache optimization

8. **Multi-User Support**
   - Authentication integration
   - User context in all endpoints
   - Preferences management
   - RLS enforcement

**Estimation :** 18-20 jours

---

### Phase 2.4 : Production Hardening (Semaine 10-11)
**Priorité :** ⭐⭐⭐⭐

9. **Streaming Responses SSE**
   - LangGraph streaming
   - Token-by-token Claude
   - Progress indicators
   - Client handling

10. **Error Recovery & Resilience**
    - Retry logic with backoff
    - Circuit breakers
    - Fallback responses
    - Graceful degradation

**Estimation :** 7-8 jours

---

## 📝 QUESTIONS À CLARIFIER

1. **LangGraph Orchestrator :** Intégration immédiate ou progressive (coexistence ancien/nouveau) ?
2. **AutoGen Discussion :** Use cases prioritaires (toutes questions complexes ou manual trigger) ?
3. **Memory Persistence :** Combien de messages historique (10, 50, 100) ?
4. **Knowledge Graph :** Neo4j (graph natif) ou PostgreSQL (plus simple) ?
5. **Intent Classification :** LLM (précis mais coûteux) ou Embeddings (rapide mais moins précis) ?
6. **Multi-User :** Déployer auth maintenant ou phase future ?
7. **Cost Optimization :** Model switching automatique ou user control ?
8. **Streaming :** Priorité haute (UX) ou peut attendre ?

---

## 🚀 LIVRABLE ATTENDU KODA

**Format :**
- Plan détaillé phase par phase
- Architecture diagrams (LangGraph workflow, AutoGen flow)
- Database migrations SQL
- API contract changes (nouveaux endpoints)
- Configuration changes (env vars)
- Estimation temps réaliste par feature
- Ordre d'implémentation recommandé
- Dependencies à installer
- Tests à écrire (critiques)

**Validation :**
- Review avec Leo (architecte principal)
- Alignment vision SCRIBE
- Faisabilité technique
- Priorités ajustées ensemble
- Budget cost APIs (augmentation attendue avec multi-agents)

---

**Document créé par :** Leo (Architecte Principal)
**Pour :** Koda (Backend Specialist)
**Date :** 30 septembre 2025
**Status :** 🚧 Audit CHAP2 - Architecture agentique à compléter ensemble