# SCRIBE - Solutions Chat UX Proposées

**Date:** 14 octobre 2025
**Contexte:** Refonte architecture chat pour expérience WhatsApp-style flawless
**Objectif:** Éliminer messages cryptiques + optimiser longueur échanges + séparer Archives/Works

---

## 🎯 **PROBLÈMES RÉSOLUS**

### ✅ 1. Séparation Archives vs Works
**Avant :**
- Table `notes` stocke TOUT (conversations + documents)
- Confusion conceptuelle Archives = Works

**Solution :**
- **Archives (`notes`)** : Documents, synthèses, connaissances consolidées
- **Works (`conversations`)** : Chat history, échanges dynamiques
- **Filtering logic** : `ConversationStorageFilter` décide où stocker

### ✅ 2. Messages Cryptiques Agents
**Avant :**
- Tool calls, params, debug info visibles frontend
- Processing steps internes exposés
- UX technique, chargée

**Solution :**
- **Filtering Layer** : `MessageFilter` nettoie messages backend → UI
- Masque : reasoning, debug, tool params, internal keywords
- Affiche : résumés concis, badges icônes, clickable objects

### ✅ 3. Échanges Agents Trop Longs
**Avant :**
- `MaxMessageTermination = 6` tours (trop permissif)
- System messages verbeux encourageant détails

**Solution :**
- **MaxMessageTermination = 4** tours (optimisé UX)
- **System messages WhatsApp-style** : "2-3 lignes MAX"
- **Concision forcée** : Synthèse > détails exhaustifs

---

## 🏗️ **ARCHITECTURE IMPLÉMENTÉE**

### Workflow 2-Couches

```
┌────────────────────────────────────────────────┐
│       LAYER 1: BACKEND ENGINE (Full)           │
│  • AutoGen discussion complète                 │
│  • Tool calls détaillés (logged)               │
│  • Reasoning, debug, internal steps            │
│  • Storage BD complet (audit trail)            │
└────────────────────────────────────────────────┘
                     ↓
            FILTERING LAYER
          (message_filter.py)
                     ↓
┌────────────────────────────────────────────────┐
│       LAYER 2: FRONTEND UX (Clean)             │
│  • Messages 2-3 lignes filtrés                 │
│  • Tool badges icônes (sans params)            │
│  • Clickable objects propres                   │
│  • Aucun contenu technique visible             │
└────────────────────────────────────────────────┘
```

---

## 📦 **COMPOSANTS CRÉÉS**

### 1. `utils/message_filter.py` ✅

**Classes implémentées :**

#### `MessageFilter`
Filtre messages agents pour UI frontend propre.

**Méthodes clés :**
- `filter_agent_message()` : Nettoie message backend → UI
- `_remove_internal_blocks()` : Supprime debug/reasoning
- `_remove_tool_calls()` : Masque syntaxe tool calls
- `_condense_message()` : Résume si > 500 chars
- `_extract_action_summary()` : Résumé actions effectuées

**Keywords filtrés automatiquement :**
```python
"reasoning:", "thinking:", "internal:", "debug:",
"context_summary:", "tool_execution:", "processing_step:",
"function_call:", "tool_params:", "raw_result:"
```

#### `ToolActivityFilter`
Transforme tool calls → badges UI-friendly.

**Transformations :**
| Backend Tool          | Frontend Badge                |
|-----------------------|-------------------------------|
| `search_knowledge`    | 🔍 "5 résultats"              |
| `web_search`          | 🌐 "3 sources"                |
| `create_note`         | 📝 "Note créée"               |
| `update_note`         | ✏️ "Mise à jour note"         |
| `get_related_content` | 🔗 "4 connexions"             |

#### `ConversationStorageFilter`
Détermine si conversation doit créer note Archives.

**Règles :**
- **Works (conversations)** : TOUTES conversations (100% stockées)
- **Archives (notes)** : UNIQUEMENT si `create_note` tool utilisé

**Espaces séparés, pas de chevauchement :**
- Works = Chat interface (`/chat`)
- Archives = Viz Page (`/archives`, `/viz/:id`)

**Critères création note Archives :**
- Tool `create_note` utilisé (signal PRIMARY)
- Intent explicite user ("crée une note", "archive")

---

### 2. System Messages Agents Optimisés ✅

#### Plume (Avant/Après)

**Avant (verbeux) :**
```
Tu es Plume, spécialisée dans la restitution PARFAITE des informations.

MISSION: Capture, transcris et reformule avec précision absolue.

PRINCIPES:
- FIDÉLITÉ ABSOLUE: Aucune invention, aucune extrapolation
- PRÉCISION: Chaque détail compte, chaque nuance préservée
- CLARTÉ: Structure et présente de manière optimale
- CONCISION: Adapte la longueur selon la complexité

STYLE DE DISCUSSION:
- Pour salutations/questions simples: réponds directement, sois concis
- Pour conversations en cours: maintiens le contexte
...
```

**Après (concis) :**
```
Tu es Plume 🖋️, agent de restitution parfaite.

RÈGLES STYLE (WhatsApp-like):
- Réponds en 2-3 lignes MAX (sauf si substantiel)
- CONCIS mais COMPLET
- Salutations: 1 ligne suffit
- Questions complexes: structure courts paragraphes

PRINCIPES:
- Fidélité absolue (pas d'invention)
- Précision (chaque détail compte)
- Clarté (mots simples, direct)

COLLABORATION:
- Si recherche nécessaire → laisse Mimir agir
- Sinon → réponds directement
- 1 tour de parole suffit généralement
```

#### Mimir (Avant/Après)

**Avant (verbeux) :**
```
Tu es Mimir, archiviste et gestionnaire de connaissances méthodique.

MISSION: Archivage, recherche et connexions intelligentes des informations.

PRINCIPES:
- MÉTHODOLOGIE: Approche systématique de l'information
- INTELLIGENCE: Décide quand utiliser les tools selon le contexte
...
[Long system message détaillé]
```

**Après (concis) :**
```
Tu es Mimir 🧠, archiviste intelligent.

RÈGLES STYLE (WhatsApp-like):
- Réponds en 2-3 lignes MAX
- Synthèse > détails exhaustifs
- Si 5+ sources → résume en bullet points courts
- Pas de preamble ("Voici les résultats...")

TOOLS (utilise intelligemment):
✅ search_knowledge SI:
  - Mots-clés recherche ("trouve", "cherche", "recherche")
  - Question nécessite archives

❌ PAS search_knowledge pour:
  - Salutations (bonjour, hi, salut)
  - Questions générales < 15 chars
  - Chat casual

COLLABORATION:
- Recherche → synthétise → passe à Plume pour reformulation
- 1-2 tours MAX (pas de longs échanges)
```

#### MaxMessageTermination Réduit

**Avant :**
```python
termination_condition = MaxMessageTermination(6)  # Max 6 rounds
```

**Après :**
```python
# Reduced from 6 to 4 for WhatsApp-style concision
termination_condition = MaxMessageTermination(4)  # Max 4 rounds (optimized UX)
```

---

### 3. Documentation Stratégique ✅

**Fichiers créés :**
- `CHAP2/CHAT_UX_ARCHITECTURE.md` : Architecture complète 2-couches
- `CHAP2/SOLUTIONS_CHAT_UX_PROPOSEES.md` : Ce document (synthèse)

---

## 🔄 **WORKFLOW TRANSFORMATION**

### Exemple : Message User → Réponse UI

#### Input User
```
"Recherche-moi les infos sur le projet X"
```

#### Backend (Layer 1) - Internal Processing
```
[Orchestrator] routing_decision: discussion mode
[Mimir] reasoning: L'utilisateur demande une recherche explicite
[Mimir] [TOOL_START: search_knowledge]
[Mimir] tool_params: {"query": "projet X", "limit": 10, "threshold": 0.75}
[Mimir] raw_result: {"results_count": 5, "sources": [...]}
[Mimir] internal: J'ai trouvé 5 documents pertinents...
[Mimir] context_summary: [500 mots détaillés sur les 5 docs]
[Plume] reasoning: Je vais reformuler la synthèse de Mimir
[Plume] processing: Extraction points clés...
[Storage] Saving conversation to DB...
```

#### Frontend (Layer 2) - Filtered UI Display
```
🧠 Mimir:
🔍 Recherche archives (5 résultats)

J'ai trouvé 5 docs sur le projet X : architecture technique,
budget, et planning. Veux-tu un aspect particulier ?

🖋️ Plume:
Résumé : Projet X = stack Python/React, budget 50K€,
livraison Q2 2025. Plus de détails ?
```

**Transformation appliquée :**
- ✅ Tool params masqués
- ✅ Reasoning/debug supprimés
- ✅ Messages condensés 2-3 lignes
- ✅ Badge icône search_knowledge
- ✅ Pas de preamble technique

---

## 📊 **SÉPARATION WORKS vs ARCHIVES**

### Tables Database

#### `conversations` (Works - Chat History)
**Contenu :**
- **TOUTES** les conversations chat (100%)
- Messages user + agents (filtrés pour display)
- Interface : `/chat` (WhatsApp-style)

**Structure :**
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  title TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  metadata JSONB  -- agents_involved, note_ids
);
```

#### `notes` (Archives - Knowledge Base)
**Contenu :**
- Documents uploadés (PDF, TXT)
- Notes créées manuellement
- Notes créées via `create_note` tool
- Interface : `/archives`, `/viz/:id` (Viz Page)

**Structure :**
```sql
CREATE TABLE notes (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  title TEXT NOT NULL,
  text_content TEXT,
  html_content TEXT,
  tags TEXT[],
  metadata JSONB,  -- source: "conversation" | "upload" | "manual"
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  is_deleted BOOLEAN DEFAULT false
);
```

### Règles Stockage (SIMPLIFIÉ)

**Works (TOUJOURS) :**
- Toutes conversations → `conversations` table
- 100% historique chat préservé

**Archives (CONDITIONNEL) :**
- Note créée UNIQUEMENT si :
  - Agent utilise tool `create_note`
  - OU user demande explicitement "crée une note"

**Pas de catégorie "both"** : Espaces distincts
- Works = Chat history (dynamique)
- Archives = Notes consolidées (statiques avec Viz)

---

## 🚀 **PROCHAINES ÉTAPES**

### Phase 2 : Intégration Orchestrator (TODO)

**Modifications `orchestrator.py` :**

1. **Import filtering layer** :
```python
from utils.message_filter import (
    MessageFilter,
    ToolActivityFilter,
    ConversationStorageFilter
)
```

2. **Filtrer messages dans `discussion_node`** :
```python
# After AutoGen discussion
for msg in discussion_history:
    filtered_msg = MessageFilter.filter_agent_message(
        agent_name=msg['agent'],
        raw_message=msg['message']
    )
    # Stream filtered message to SSE
    if sse_queue:
        await sse_queue.put({
            'type': 'agent_message',
            **filtered_msg
        })
```

3. **Adapter `storage_node`** :
```python
from utils.message_filter import should_create_archive_note

# ALWAYS store in conversations (Works)
await memory_service.store_message(
    conversation_id=conversation_id,
    role="user",
    content=state.get("input"),
    ...
)

# CONDITIONALLY create note in Archives
if should_create_archive_note({
    "user_input": state.get("input"),
    "tools_used": state.get("tools_used", [])
}):
    # Agent used create_note or user explicitly requested archiving
    await supabase_client.create_note({
        "title": self._generate_title(state.get("input")),
        "text_content": state.get("final_response"),
        "metadata": {"source": "conversation"}
    })
```

4. **Filtrer tool activities SSE** :
```python
# In discussion_node, before streaming tool events
filtered_activity = ToolActivityFilter.filter_tool_activity(
    tool_name=tool_name,
    tool_params=params,
    tool_result=result,
    status=status
)

if sse_queue:
    await sse_queue.put({
        'type': 'tool_activity',
        **filtered_activity
    })
```

### Phase 3 : Frontend Adaptation (TODO)

**Modifications `frontend/app/chat/page.tsx` :**

1. **Adapter réception messages filtrés** :
```typescript
// Messages déjà filtrés côté backend
if (event.type === 'agent_message') {
  const cleanMessage = {
    id: `msg-${event.agent}-${Date.now()}`,
    role: event.agent,
    content: event.content,  // Déjà nettoyé
    timestamp: new Date(),
    action_summary: event.action_summary
  }
  setMessages(prev => [...prev, cleanMessage])
}
```

2. **Afficher tool activities comme badges** :
```typescript
if (event.type === 'tool_activity') {
  // event contient { label, status, summary, timestamp }
  setCurrentToolActivities(prev => {
    const activity = {
      id: `${event.tool}-${Date.now()}`,
      label: event.label,  // "🔍 Recherche archives"
      status: event.status,
      summary: event.summary  // "5 résultats"
    }
    return new Map(prev).set(activity.id, activity)
  })
}
```

3. **Séparer onglets Works/Archives** :
```typescript
// Navigation
<Tabs defaultValue="works">
  <TabsList>
    <TabsTrigger value="works">💬 Works</TabsTrigger>
    <TabsTrigger value="archives">📚 Archives</TabsTrigger>
  </TabsList>

  <TabsContent value="works">
    {/* List conversations récentes */}
  </TabsContent>

  <TabsContent value="archives">
    {/* List notes consolidées */}
  </TabsContent>
</Tabs>
```

---

## 📈 **IMPACT ATTENDU**

### UX Chat

**Avant :**
```
[Plume] Reasoning: L'utilisateur pose une question simple...
[Plume] Internal: Je vais utiliser mes capacités de restitution...
[Plume] Processing: Analyse du contexte en cours...
[Plume] [TOOL_CALL: function="analyze_context", params={"input": "..."}]
[Plume] Result: J'ai analysé la question et voici ma réponse détaillée
en plusieurs paragraphes qui couvre tous les aspects possibles de la
question posée par l'utilisateur avec un niveau de détail exhaustif...
[250 mots de réponse]
```

**Après :**
```
🖋️ Plume:
Salut ! Je suis là pour t'aider. Tu veux que
je capture quelque chose ou reformule une info ?
```

### Métriques Succès

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Messages agents (chars) | 500-1000 | 100-200 | ⬇️ 80% |
| Tours discussion | 4-6 | 2-4 | ⬇️ 50% |
| Contenu technique visible | 100% | 0% | ⬇️ 100% |
| Temps perçu réponse | 5-10s | 2-3s | ⬇️ 70% |
| Satisfaction UX | ? | Testé post-deploy | TBD |

---

## 🔍 **VALIDATION & TESTS**

### Tests Unitaires (TODO)

**`tests/test_message_filter.py` :**
```python
def test_filter_removes_internal_keywords():
    raw = "Reasoning: Je vais chercher. Voici ma réponse."
    filtered = MessageFilter.filter_agent_message("plume", raw)
    assert "Reasoning:" not in filtered["content"]
    assert "Voici ma réponse" in filtered["content"]

def test_filter_condenses_long_messages():
    raw = "A" * 1000  # 1000 chars
    filtered = MessageFilter.filter_agent_message("mimir", raw)
    assert len(filtered["content"]) <= 500

def test_tool_activity_filter():
    activity = ToolActivityFilter.filter_tool_activity(
        "search_knowledge",
        {"query": "test"},
        {"results_count": 5},
        "completed"
    )
    assert activity["label"] == "🔍 Recherche archives"
    assert activity["summary"] == "5 résultats"
```

### Tests Intégration (TODO)

**Workflow complet :**
1. Envoyer message user via API
2. Vérifier backend logs complets (unfiltered)
3. Vérifier SSE stream messages filtrés
4. Valider UI affiche contenu clean
5. Confirmer storage Works vs Archives correct

---

## 📚 **DOCUMENTATION CRÉÉE**

| Fichier | Description | Status |
|---------|-------------|--------|
| `utils/message_filter.py` | Module filtering 3 classes | ✅ Créé |
| `CHAP2/CHAT_UX_ARCHITECTURE.md` | Architecture 2-couches détaillée | ✅ Créé |
| `CHAP2/SOLUTIONS_CHAT_UX_PROPOSEES.md` | Synthèse solutions (ce doc) | ✅ Créé |
| `agents/autogen_agents.py` | System messages optimisés | ✅ Modifié |
| Tests unitaires | `test_message_filter.py` | ⏳ TODO |
| Intégration orchestrator | Filtering dans workflow | ⏳ TODO |
| Frontend adaptation | Works/Archives séparés | ⏳ TODO |

---

## 🎯 **RÉSUMÉ EXÉCUTIF**

**Problèmes identifiés :**
1. ❌ Messages agents trop longs, techniques, cryptiques
2. ❌ Mélange conceptuel Archives vs Works
3. ❌ Échanges agents verbeux (6 tours max)

**Solutions implémentées :**
1. ✅ **Filtering Layer 2-couches** : Backend full + Frontend clean
2. ✅ **MessageFilter** : Nettoie messages, masque debug/reasoning
3. ✅ **ToolActivityFilter** : Tool calls → badges icônes
4. ✅ **ConversationStorageFilter** : Works vs Archives automatique
5. ✅ **System messages optimisés** : WhatsApp-style 2-3 lignes
6. ✅ **MaxMessageTermination 4** : Réduction tours 6→4

**Impact attendu :**
- 🚀 UX WhatsApp-style flawless
- ⚡ Messages 80% plus courts
- 🧹 Aucun contenu technique visible
- 📊 Séparation claire Works/Archives
- 🎯 Temps perçu réduit 70%

**Prochaines étapes :**
1. Intégrer filtering dans orchestrator
2. Adapter frontend pour nouveaux formats
3. Tests unitaires + intégration
4. Déploiement + monitoring user feedback

---

> **"Le meilleur chat est celui où l'IA travaille en profondeur
> mais l'user ne voit que l'essentiel - WhatsApp avec intelligence."**
>
> — Architecture SCRIBE 2-Couches, Octobre 2025
