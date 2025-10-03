# 🔍 ANALYSE INTÉGRATION - Phase 2.2

**Date :** 1er octobre 2025
**Status :** Phase 1 TERMINÉE ✅ - Phase 2 (Integration) À LANCER

---

## 📊 RÉCAPITULATIF PHASE 1 (PARALLÈLE)

### ✅ **KodaF - Frontend** (CR disponible)
**Durée :** ~3h30
**Fichiers créés :** 20+

**Accomplissements :**
- ✅ Pages : Login, Home (chat), Works, Archives, Viz, Settings
- ✅ Composants : InputZone, ChatMessage, ClickableObjectButton, ProtectedRoute
- ✅ API mockée complète (`lib/api/mock.ts`)
- ✅ Session localStorage (30 jours)
- ✅ Upload audio/texte avec context (texte OU audio)
- ✅ Navigation restructurée
- ✅ Dark theme cohérent
- ✅ Build production réussi sans erreurs

---

### ✅ **Koda - Backend API** (CR disponible)
**Durée :** ~2h
**Fichiers créés :** 6

**Accomplissements :**
- ✅ 12 nouveaux endpoints (auth, conversations, notes, upload, metrics)
- ✅ Upload audio → transcription Whisper → orchestrator → note structurée
- ✅ Context audio OU texte support
- ✅ Search fulltext avec migration SQL
- ✅ Conversion HTML async (background task)
- ✅ Clickable objects extraction (3 patterns)
- ✅ Métriques dashboard

---

### ✅ **Koda - AutoGen Streaming** (PAS de CR séparé, code vérifié)
**Durée :** Intégré dans travail backend
**Fichier créé :** `/backend/agents/autogen_agents.py`

**Accomplissements :**
- ✅ AutoGen v0.4 integration avec fallback
- ✅ Plume & Mimir AssistantAgents
- ✅ RoundRobinGroupChat configuration
- ✅ Fallback séquentiel (Mimir → Plume)
- ✅ HTML generation discussion
- ✅ SSE endpoint `/orchestrated/stream` dans `/backend/api/chat.py` ✅
  - Streaming messages agents temps réel
  - Queue async pour messages
  - Keepalive toutes les 15s
  - Events : start, agent_message, processing, complete, error

---

## 🔄 CE QUI RESTE À FAIRE (PHASE 2 - INTEGRATION)

### 1. **Frontend → Backend Connection** ⚠️

#### **Créer Client API Réel**
**Fichier à créer :** `frontend/lib/api/client.ts`

**Actions :**
- [ ] Remplacer tous les imports `lib/api/mock.ts` par `lib/api/client.ts`
- [ ] Implémenter `fetch()` pour chaque endpoint backend
- [ ] Helper `getUserId()` depuis localStorage
- [ ] Error handling avec retry logic
- [ ] Toast notifications pour errors

**Fonctions à créer :**
```typescript
- login(username, password)
- getConversations(limit, offset)
- getConversation(id)
- createConversation(title?)
- deleteConversation(id)
- getRecentNotes()
- getAllNotes(page?, limit?)
- getNote(id)
- searchNotes(query, limit)
- uploadText(text, contextText?, contextAudio?)
- uploadAudio(audioFile, contextText?, contextAudio?)
- convertToHTML(noteId) + polling
- getMetrics()
- sendOrchestratedMessageStream() // SSE streaming
```

---

#### **Chat Streaming SSE**
**Fichier :** `frontend/app/page.tsx` + `app/works/[id]/page.tsx`

**Actions :**
- [ ] Implémenter `sendOrchestratedMessageStream()` avec EventSource ou fetch SSE
- [ ] Parser events : `start`, `agent_message`, `complete`, `error`, `keepalive`
- [ ] Afficher messages agents temps réel dans UI
- [ ] Gérer discussion_history pour mode AutoGen
- [ ] Loader états intermédiaires

**Code type :**
```typescript
await sendOrchestratedMessageStream(
  {
    message: inputText,
    mode: 'auto', // ou 'discussion' pour AutoGen visible
    conversation_id: conversationId,
    user_id: session.user_id
  },
  // onMessage: afficher messages agents au fur et à mesure
  (sseMessage) => {
    if (sseMessage.type === 'agent_message') {
      addAgentMessage(sseMessage.agent, sseMessage.content)
    }
  },
  // onComplete: finaliser avec metadata
  (result) => {
    setMetadata({
      tokens: result.tokens_used,
      cost: result.cost_eur,
      processing_time: result.processing_time_ms
    })
  },
  // onError
  (error) => toast.error(error.message)
)
```

---

#### **Upload Audio Workflow**
**Fichier :** `frontend/app/archives/page.tsx`

**Actions :**
- [ ] Implémenter `uploadAudio()` avec FormData multipart
- [ ] Support 3 fichiers : audio_file, context_text, context_audio
- [ ] Progress indicator : 0% → 50% (transcription) → 100% (note créée)
- [ ] Afficher transcription temporaire avant création note
- [ ] Redirect vers `/viz/{note_id}` après création

**Flow complet :**
```
1. User upload audio + context (texte OU audio)
2. Frontend → POST /upload/audio (FormData)
3. Loading "Transcription en cours..." (50%)
4. Loading "Création note par agents..." (75%)
5. Success → Redirect /viz/{note_id} (100%)
```

---

#### **HTML Conversion avec Polling**
**Fichier :** `frontend/app/viz/[id]/page.tsx`

**Actions :**
- [ ] Clic toggle HTML → POST `/notes/{id}/convert-html` (202 Accepted)
- [ ] Polling GET `/notes/{id}` toutes les 2s
- [ ] Vérifier `html_content` non vide
- [ ] Switcher vue quand ready
- [ ] Timeout après 30s

**Code polling :**
```typescript
const pollConversion = async (noteId: string) => {
  const interval = setInterval(async () => {
    const note = await getNote(noteId)
    if (note.html_content) {
      setHtmlContent(note.html_content)
      setIsConverting(false)
      clearInterval(interval)
    }
  }, 2000)

  setTimeout(() => {
    clearInterval(interval)
    setIsConverting(false)
    toast.error('Conversion timeout')
  }, 30000)
}
```

---

### 2. **Voice Recording InputZone** ⚠️

**Fichier :** `frontend/components/chat/InputZone.tsx`

**Actions :**
- [ ] Implémenter Web Audio API ou `react-media-recorder`
- [ ] Bouton micro → start/stop recording
- [ ] Afficher waveform animation pendant recording
- [ ] Upload blob audio
- [ ] Transcription → populate InputZone
- [ ] User peut éditer avant send

**Flow :**
```
1. Clic micro → Start recording
2. Waveform animation
3. Clic stop → Upload blob
4. Transcription backend
5. Populate textarea avec transcription
6. User édite si besoin
7. Send message normal
```

---

### 3. **Context Chat depuis Viz Page** ⚠️

**Fichier :** `frontend/app/page.tsx`

**Actions :**
- [ ] Lire query param `?context=note:{id}`
- [ ] Load note metadata
- [ ] Afficher banner "Contexte : [note.title]"
- [ ] Pré-remplir context_ids dans message orchestrator
- [ ] Agents utilisent cette note comme contexte RAG

---

### 4. **Variables Environnement** ⚠️

#### **Frontend `.env.production`**
```bash
NEXT_PUBLIC_API_URL=https://scribe-api.onrender.com
```

#### **Backend (Render)**
Vérifier que toutes les variables existent :
```bash
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
OPENAI_API_KEY=...  # Pour Whisper
CLAUDE_API_KEY=...  # Pour Plume/Mimir
```

---

### 5. **CORS Configuration** ⚠️

**Fichier :** `backend/main.py`

Vérifier/ajouter :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://scribe-frontend-qk6s.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

### 6. **Migration SQL** ⚠️ **CRITIQUE**

**Fichier :** `database/migrations/003_search_function.sql`

**Actions :**
- [ ] Appliquer migration en local :
  ```bash
  psql $SUPABASE_URL -f database/migrations/003_search_function.sql
  ```
- [ ] Vérifier fonction créée :
  ```sql
  SELECT search_notes_fulltext('architecture', 'king_001', 10);
  ```
- [ ] Appliquer en production (Supabase SQL Editor)

---

### 7. **Tests End-to-End** ⚠️

**Fichier à créer :** `tests/e2e/integration.spec.ts`

**Scénarios à tester :**
- [ ] Login → Home → Send message → Receive response
- [ ] Upload texte → Note créée → Visualiser
- [ ] Upload audio → Transcription → Note créée
- [ ] Search notes → Résultats affichés
- [ ] Toggle HTML → Conversion → Affichage
- [ ] Clickable objects → Navigation fonctionne
- [ ] Works → Liste conversations → Ouvrir conversation
- [ ] Settings → Metrics affichées

---

## 📝 CHECKLIST INTÉGRATION

### Setup
- [ ] Créer `lib/api/client.ts` avec toutes les fonctions
- [ ] Configurer variables environnement production
- [ ] Appliquer migration SQL
- [ ] Configurer CORS backend

### Pages à Modifier
- [ ] `/app/page.tsx` - Chat avec SSE streaming
- [ ] `/app/works/page.tsx` - API réelle conversations
- [ ] `/app/works/[id]/page.tsx` - API réelle + streaming
- [ ] `/app/archives/page.tsx` - Upload audio réel
- [ ] `/app/viz/[id]/page.tsx` - HTML conversion polling
- [ ] `/app/settings/page.tsx` - Metrics réelles

### Composants à Modifier
- [ ] `components/chat/InputZone.tsx` - Voice recording
- [ ] `components/chat/ChatMessage.tsx` - Déjà prêt ✅

### Tests
- [ ] Tests E2E Playwright (tous scénarios)
- [ ] Tests manuels sur toutes les pages
- [ ] Tests responsive mobile/desktop

### Déploiement
- [ ] Build frontend production sans warnings
- [ ] Build backend production sans warnings
- [ ] Deploy frontend Render
- [ ] Deploy backend Render
- [ ] Tester URLs production

---

## 🎯 PRIORITÉS D'INTÉGRATION

### **P0 - Critical (Must Have)**
1. ✅ Migration SQL (sans ça, search ne fonctionne pas)
2. ✅ Client API basique (login, conversations, notes, chat)
3. ✅ Chat streaming SSE (cœur de l'application)
4. ✅ Upload audio workflow (feature principale)
5. ✅ CORS configuration

### **P1 - Important (Should Have)**
6. ⚠️ HTML conversion polling
7. ⚠️ Clickable objects rendering (déjà prêt côté composant)
8. ⚠️ Context chat depuis Viz page
9. ⚠️ Error handling global + toast

### **P2 - Nice to Have (Can Wait)**
10. ⏳ Voice recording InputZone (peut rester upload fichier)
11. ⏳ Tests E2E complets
12. ⏳ Pagination `/archives/all`
13. ⏳ Optimisations performance

---

## ⏱️ ESTIMATION DURÉE

**P0 (Critical) :** ~2h
- Migration SQL : 10min
- Client API : 1h
- SSE streaming : 30min
- Upload audio : 20min
- CORS : 5min

**P1 (Important) :** ~1h
- HTML polling : 20min
- Clickable objects : 10min (déjà prêt)
- Context chat : 20min
- Error handling : 15min

**P2 (Nice to Have) :** ~1-2h
- Voice recording : 1h
- Tests E2E : 1h
- Optimisations : variable

**Total estimé :** 3-4h pour P0+P1, 5-6h avec P2

---

## 🚨 POINTS CRITIQUES

### 1. **Migration SQL OBLIGATOIRE** ⚠️
Sans elle, le search fulltext ne fonctionne pas (fallback ILIKE très lent).

### 2. **SSE Streaming** ⚠️
Vérifier que Render ne buffer pas les SSE :
- Header `X-Accel-Buffering: no` ajouté ✅
- Tester keepalive fonctionne

### 3. **Audio Upload** ⚠️
- Multipart FormData avec 3 fichiers possibles
- Ordre : audio_file, context_text, context_audio
- Vérifier limite 25MB Whisper API

### 4. **AutoGen Discussion** ℹ️
Mode `discussion` affiche messages Plume ↔ Mimir temps réel.
Frontend doit gérer `discussion_history` dans complete event.

---

## 📂 FICHIER SUIVANT À UTILISER

**Pour l'agent d'intégration :**
`/Users/adamdahan/Documents/SCRIBE/CHAP2/KODA_PHASE2.2_INTEGRATION.md`

**Modifications nécessaires :**
- ✅ Spécifications déjà correctes
- ⚠️ Ajouter mention migration SQL critique
- ⚠️ Clarifier polling vs WebSocket (polling recommandé)
- ⚠️ Ajouter checklist P0/P1/P2

---

**Prêt pour lancement Phase 2 (Integration)** 🚀
