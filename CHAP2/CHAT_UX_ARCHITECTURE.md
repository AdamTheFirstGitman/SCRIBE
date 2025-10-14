# SCRIBE - Architecture UX Chat (Workflow 2-Couches)

**Date:** 14 octobre 2025
**Phase:** Chapitre 2 - Architecture Agentique Avancée
**Objectif:** Chat flawless type WhatsApp avec processing IA avancé invisible

---

## 🎯 **PROBLÈMES IDENTIFIÉS**

### 1. Mélange Archives vs Conversations (Works)
**Situation actuelle :**
- Table `notes` stocke TOUT (conversations + documents)
- `storage_node` orchestrator crée note pour chaque conversation
- Confusion conceptuelle : Archives ≠ Works

**Problème :**
- Archives = documents statiques, notes synthétisées, connaissances consolidées
- Works = conversations dynamiques, échanges en cours, historique chat
- Actuellement : Tout mélangé dans `notes` table

### 2. Messages Cryptiques Agents Exposés
**Situation actuelle :**
- Tool calls visibles (`search_knowledge`, params complets)
- Processing steps internes affichés
- Debug info, reasoning, context_summary exposés
- Messages AutoGen internes non filtrés

**Problème :**
- UX chargée, technique, non user-friendly
- User voit "plomberie" backend au lieu de conversation fluide
- Trop verbeux pour expérience WhatsApp-style

### 3. Échanges Agents Trop Longs
**Situation actuelle :**
- `MaxMessageTermination = 6` tours (trop permissif)
- System messages détaillés encouragent verbosité
- Pas de résumé condensé pour UI

**Problème :**
- Conversations agents-agents trop longues
- User attend pendant tours multiples
- Réponses finales diluées dans échanges internes

---

## 🏗️ **SOLUTION : Workflow 2-Couches**

### Architecture Conceptuelle

```
┌─────────────────────────────────────────────────────────────┐
│                  LAYER 1: BACKEND ENGINE                    │
│             (Processing complet & détaillé)                  │
├─────────────────────────────────────────────────────────────┤
│  • AutoGen full discussion (internal, logged)               │
│  • Tool calls avec params complets                          │
│  • Messages debug/reasoning/thinking                        │
│  • Logs structurés (tout enregistré pour debug)             │
│  • Storage détaillé en BD (conversations + notes)           │
│  • Performance metrics, cost tracking                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
                  FILTERING LAYER
              (message_filter.py)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  LAYER 2: FRONTEND UX                       │
│           (Display WhatsApp-style optimisé)                 │
├─────────────────────────────────────────────────────────────┤
│  ✅ Messages agents user-friendly (filtrés)                 │
│  ✅ Tool activities: badges icônes (sans params)            │
│  ✅ Résumés concis agents (max 2-3 lignes)                  │
│  ✅ Clickable objects: viz_links propres                    │
│  ✅ Masquer: reasoning, debug, tool params, internal steps  │
└─────────────────────────────────────────────────────────────┘
```

### Principes Clés

**1. Transparence Asymétrique**
- Backend : Logging maximal, détails complets, debugging optimal
- Frontend : UX minimale, concision, expérience fluide

**2. Séparation Works vs Archives**
- **Works (`conversations` table)** : Chat history dynamique, échanges en cours
- **Archives (`notes` table)** : Connaissances consolidées, documents, synthèses

**3. Filtering Intelligent**
- Messages agents passent par `MessageFilter` avant UI
- Tool activities transformées en badges UI-friendly
- Contenu interne/debug masqué automatiquement

---

## 📦 **COMPOSANTS IMPLÉMENTÉS**

### `utils/message_filter.py` ✅

**Classes principales :**

#### 1. `MessageFilter`
Filtre messages agents backend → UI frontend

**Méthodes :**
- `filter_agent_message()` : Nettoie message agent pour affichage
- `_remove_internal_blocks()` : Supprime contenu debug/reasoning
- `_remove_tool_calls()` : Masque syntaxe tool calls
- `_condense_message()` : Résume si trop long (max 500 chars)
- `_extract_action_summary()` : Extrait résumé actions effectuées

**Keywords filtrés :**
```python
INTERNAL_KEYWORDS = [
    "reasoning:", "thinking:", "internal:", "debug:",
    "context_summary:", "tool_execution:", "processing_step:",
    "function_call:", "tool_params:", "raw_result:"
]
```

#### 2. `ToolActivityFilter`
Transforme tool calls backend → badges UI

**Transformations :**
- `search_knowledge` → 🔍 "5 résultats"
- `web_search` → 🌐 "3 sources"
- `create_note` → 📝 "Note créée"
- `update_note` → ✏️ "Mise à jour note"
- `get_related_content` → 🔗 "4 connexions"

**Méthodes :**
- `filter_tool_activity()` : Crée représentation UI-friendly
- `_generate_tool_summary()` : Génère résumé concis selon tool + result

#### 3. `ConversationStorageFilter`
Détermine si conversation doit créer note Archives

**Règles :**
- **Works (conversations table)** : TOUTES les conversations chat (toujours stockées)
- **Archives (notes table)** : UNIQUEMENT si `create_note` tool utilisé

**Espaces séparés, pas de chevauchement :**
- Works = Interface chat avec agents (`/chat`)
- Archives = Viz Page avec notes consolidées (`/archives`, `/viz/:id`)

**Critères création note Archives :**
- Tool `create_note` utilisé par agent (signal PRIMARY)
- Intent explicite user ("crée une note", "archive", "sauvegarde")

---

## 🔄 **INTÉGRATION WORKFLOW**

### Flux Message User → Réponse UI

```
1. User Input
   │
   ↓
2. Orchestrator (orchestrator.py)
   ├─ Intent classification
   ├─ Context retrieval (RAG si nécessaire)
   └─ Route → discussion_node
   │
   ↓
3. AutoGen Discussion (autogen_agents.py)
   ├─ Plume + Mimir agents
   ├─ Tool calls (search_knowledge, create_note, etc.)
   ├─ Internal reasoning (detailed)
   └─ Full messages logged
   │
   ↓
4. MESSAGE FILTERING LAYER ⭐ (NEW)
   ├─ MessageFilter.filter_agent_message()
   ├─ ToolActivityFilter.filter_tool_activity()
   └─ Remove internal content, condense
   │
   ↓
5. Storage Decision
   ├─ TOUJOURS → conversations table (Works)
   ├─ ConversationStorageFilter.should_create_archive_note()
   └─ SI create_note tool utilisé → notes table (Archives)
   │
   ↓
6. SSE Streaming to Frontend
   ├─ Filtered messages only
   ├─ Tool activity badges
   └─ Clickable objects (viz_links)
   │
   ↓
7. Frontend Display (page.tsx)
   ├─ Clean agent messages (WhatsApp-style)
   ├─ Tool badges with icons
   └─ Smooth UX, no technical noise
```

### Exemple Transformation Message

**Backend (Layer 1) - Internal Full Message :**
```
Reasoning: L'utilisateur demande une recherche dans les archives.
Je vais utiliser search_knowledge avec params: {"query": "projet X", "limit": 10}.

[TOOL_START: search_knowledge]
Tool params: {"query": "projet X", "limit": 10, "threshold": 0.75}
[TOOL_END: search_knowledge]

Raw result: {"results_count": 5, "sources": [...]}

Context_summary: J'ai trouvé 5 documents pertinents sur le projet X.
Voici une synthèse détaillée des 3 documents les plus pertinents...
[500 mots de synthèse détaillée]
```

**Frontend (Layer 2) - Filtered UI Message :**
```
🔍 Recherche archives (5 résultats)

J'ai trouvé 5 documents sur le projet X.
Les 3 plus pertinents concernent : architecture technique,
budget prévisionnel, et planning. [...] Veux-tu que
je détaille un aspect particulier ?
```

---

## 🎨 **UI/UX GUIDELINES**

### Style WhatsApp-Like

**Messages Agents :**
- Max 2-3 lignes par défaut
- Condensé si > 500 chars
- Structure : Résumé action + Réponse concise + Question follow-up

**Tool Activities :**
- Badges avec icônes (🔍 🌐 📝 ✏️ 🔗)
- Statut visuel : running (🔄), completed (✅), failed (❌)
- Résumé 1-2 mots ("5 résultats", "Note créée")

**Clickable Objects :**
- Viz links propres (📄 "Titre de la note →")
- Web links (🌐 "domain.com →")
- Pas de IDs techniques visibles

---

## 📊 **SÉPARATION WORKS vs ARCHIVES**

### Tables Database

#### `conversations` (Works - Chat History)
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  title TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  metadata JSONB,  -- agents_involved, note_ids, etc.
  is_archived BOOLEAN DEFAULT false
);
```

**Contenu :**
- **TOUTES** les conversations chat (100% des échanges)
- Messages user + agents (filtrés pour display)
- Interface : `/chat` (chat WhatsApp-style)

#### `notes` (Archives - Knowledge Base)
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

**Contenu :**
- Documents uploadés (PDFs, TXT, etc.)
- Notes créées manuellement
- Notes créées via `create_note` tool (conversations → Archives)
- Interface : `/archives`, `/viz/:id` (Viz Page)

### Règles Stockage (SIMPLIFIÉ)

**Works (TOUJOURS) :**
- Toutes conversations → `conversations` table
- 100% historique chat préservé

**Archives (CONDITIONNEL) :**
- Note créée UNIQUEMENT si :
  - Agent utilise tool `create_note`
  - OU user demande explicitement "crée une note"

**Pas de catégorie "both"** : Ce sont deux espaces distincts
- Works = Chat history (dynamique)
- Archives = Notes consolidées (statiques avec Viz)

---

## 🚀 **PLAN D'IMPLÉMENTATION**

### Phase 1 : Filtering Layer ✅ COMPLETE
- [x] `message_filter.py` créé
- [x] MessageFilter class
- [x] ToolActivityFilter class
- [x] ConversationStorageFilter class

### Phase 2 : Intégration Orchestrator (EN COURS)
- [ ] Intégrer MessageFilter dans `discussion_node`
- [ ] Filtrer messages avant SSE streaming
- [ ] Adapter `storage_node` pour Works vs Archives
- [ ] Tester workflow complet

### Phase 3 : Optimisation Agents
- [ ] Réduire system messages agents (plus concis)
- [ ] MaxMessageTermination = 3-4 (au lieu de 6)
- [ ] Guidelines "style WhatsApp" dans prompts agents

### Phase 4 : Frontend Adaptation
- [ ] Adapter `page.tsx` pour nouveaux formats messages
- [ ] Améliorer badges tool activities
- [ ] Masquer technical IDs, params

### Phase 5 : Séparation Works/Archives
- [ ] API `/works` (conversations récentes)
- [ ] API `/archives` (notes consolidées)
- [ ] UI séparée : Works tab vs Archives tab
- [ ] Migration données existantes

---

## 📈 **MÉTRIQUES SUCCÈS**

**UX Chat :**
- ✅ Messages agents < 3 lignes par défaut
- ✅ Aucun contenu technique/debug visible UI
- ✅ Tool activities = badges icônes uniquement
- ✅ Temps réponse perçu < 2s

**Architecture :**
- ✅ Séparation claire Works vs Archives
- ✅ Backend logging complet maintenu
- ✅ Filtering transparent, pas de data loss
- ✅ Performance non impactée

**User Feedback :**
- ✅ "Chat fluide comme WhatsApp"
- ✅ "Je comprends ce que les agents font"
- ✅ "Pas submergé par technique"

---

## 🔍 **DEBUGGING & MONITORING**

### Logs Backend (Layer 1)
**Tout enregistré :**
- Messages complets agents (unfiltered)
- Tool calls avec params détaillés
- Reasoning, thinking, internal steps
- Performance metrics, errors

**Accès :**
- Logs structurés (structlog)
- Supabase audit tables
- Render logs dashboard

### UI Frontend (Layer 2)
**Affichage minimal :**
- Messages filtrés user-friendly
- Tool badges résumés
- Pas de logs techniques

**Accès debug (si nécessaire) :**
- Console browser : metadata disponible
- Developer tools : full backend response inspectable
- Admin panel (futur) : accès logs complets

---

## 🎯 **NEXT STEPS**

1. **Intégrer filtering dans orchestrator** (priorité haute)
2. **Optimiser system messages agents** (concision)
3. **Séparer routes `/works` vs `/archives`** (clarté conceptuelle)
4. **Tester workflow complet** avec vraies conversations
5. **Documenter patterns filtering** pour futurs agents

---

> **Architecture 2-Couches : Processing IA maximal + UX minimale**
>
> "Le meilleur chat est celui où l'IA travaille en profondeur mais l'user
> ne voit que l'essentiel, comme WhatsApp mais avec intelligence."
>
> — Leo, Architecte SCRIBE, Octobre 2025
