# SCRIBE - Système Plume & Mimir

## Configuration Projet

*Système de gestion de connaissances avec agents IA intelligents*

### Architecture Multi-Agents Opérationnelle ✅

**Agents Principaux :**
- **🖋️ Plume** - Agent restitution parfaite : capture, transcription, reformulation précise
- **🧠 Mimir** - Agent archiviste : indexation, recherche RAG, connections méthodiques
- **🎭 LangGraph Orchestrator** - Workflow intelligent : routing automatique, discussions agents
- **🤝 AutoGen Integration** - Dialogues structurés entre agents pour qualité optimale

**Agents de Build (Forge EMPYR) :**
- **Leo** - Architecte principal, task decomposition hiérarchique
- **Koda** - Codeur spécialisé patterns FastAPI/CRUD
- **Gito** - Git MCP, gestion repositories

### Architecture Technique Complète

**Stack Frontend :**
- NextJS 14 + App Router + TypeScript strict
- PWA complète avec service worker avancé
- Tailwind CSS + animations fluides
- Interface mobile-first avec support offline

**Stack Backend :**
- FastAPI + LangGraph + AutoGen
- Architecture multi-agents avec state management
- Services IA complets (transcription, embeddings, RAG)
- Cache multi-niveaux optimisé

**Infrastructure Data :**
- Supabase Pro + pgvector pour embeddings
- PostgreSQL avec RLS et fonctions RPC
- Redis Cloud pour cache haute performance
- Realtime sync bidirectionnel

### Services IA Intégrés

**🎙️ Transcription Service :**
- OpenAI Whisper API
- Formats multiples : webm, mp3, wav, m4a, ogg
- Cache intelligent avec validation audio
- Gestion costs et performance

**🔍 Embeddings Service :**
- text-embedding-3-large (1536 dimensions)
- Chunking sémantique intelligent
- Batch processing optimisé
- Cache persistant Redis

**🧬 RAG Avancé :**
- Recherche hybride (vector + fulltext + BM25)
- Re-ranking avec cross-encoder
- Contexte dynamique adaptatif
- Sources tracking avec confidence

**🤖 LLM Multi-Model :**
- Claude Opus (agents principaux)
- OpenAI (embeddings + Whisper)
- Perplexity (recherche temps réel)
- Routing intelligent selon contexte

### Phases de Développement

#### ✅ Phase 1 : Infrastructure
- [x] Database Schema (Supabase + pgvector)
- [x] Backend FastAPI (Structure + Services + API)
- [x] Frontend NextJS (PWA + Tailwind + TypeScript)
- [x] Cache System (Redis multi-niveaux)

#### ✅ Phase 2 : Agents Core
- [x] LangGraph Orchestrator (Workflow + State + Decision trees)
- [x] Plume Agent (Restitution parfaite + cache + HTML)
- [x] Mimir Agent (RAG + recherche + références)
- [x] AutoGen Integration (Discussion + fallback)
- [x] Services IA (Transcription + Embeddings + RAG)

#### ✅ Phase 3 : Upload & Conversion
- [x] Document Upload Pipeline (drag & drop + validation)
- [x] Smart Text-to-HTML Conversion (headers + links + lists)
- [x] Toggle View Component (TEXT ↔ HTML mobile-first)
- [x] Chunking Service (semantic boundaries + overlap)
- [x] Demo Interface (light theme + clean design)

#### ✅ Phase 4 : Interface Chat
- [x] Chat Interface (Vocal + Textuel + animations)
- [x] Mobile-first design avec toggle agents
- [x] Voice recording + transcription
- [x] Message bubbles + loading states
- [x] Real-time WebSocket connections

#### ✅ Phase 5 : RAG & Intégrations
- [x] API Endpoints Complete (REST + SSE + WebSocket)
- [x] RAG State-of-the-Art (Knowledge graph + auto-tuning)
- [x] Realtime Integration (Subscriptions + sync)
- [x] Advanced Search (hybrid vector+fulltext+BM25)
- [x] Web Search Integration (Perplexity + Tavily)
- [x] Collaborative Features (typing, user status)

#### ✅ Phase 6 : Production
- [x] Performance Optimization (CDN + scaling + monitoring)
- [x] Architecture Review (95% alignment validation)
- [x] Comprehensive Error Handling & Recovery
- [x] Monitoring & Analytics Dashboards
- [x] Automated Backup & Data Protection
- [x] End-to-End Testing Suite (Playwright)
- [x] Offline PWA Support (Service Workers + IndexedDB)
- [x] Render Deployment Configuration (Hobby plan + sécurisé)

#### 📋 Phase 7 : Polish & Advanced UX
- [ ] Streaming Chat (Vercel AI SDK + LangGraph hybrid)
- [ ] Micro-interactions avancées (animations, transitions fluides)
- [ ] Keyboard Shortcuts système (raccourcis clavier intelligents)
- [ ] Performance Ultra (lazy loading, code splitting, optimisations)
- [ ] Accessibility A11Y (ARIA, navigation clavier, screen readers)
- [ ] Dark/Light Mode toggle (thème adaptatif)
- [ ] Advanced Search UX (suggestions, filtres, historique)

### Configuration Déploiement

**Environnement de Développement :**
```bash
# Démarrage rapide
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
cd database && python test_connection.py
```

**Production (Render Plan Hobby) :**
- Backend : Render.com (scribe-api privé)
- Frontend : Render.com (scribe-frontend public)
- Database : Supabase Pro
- Cache : Redis Cloud (optionnel)
- Monitoring : Health checks + métriques Render intégrés

### Budget & Performance

**Coûts Mensuels :**
- Infrastructure : 19€ (Render Hobby) + 25€ (Supabase Pro) = 44€
- APIs : 30-55€ (Claude + OpenAI + Perplexity + Tavily)
- **Total : 74-99€/mois** (économie vs estimation initiale)

**Targets Performance :**
- FCP < 1s, TTI < 2s
- API response < 200ms
- Search RAG < 500ms
- Cache hit rate > 80%

### Sécurité & Monitoring

**Sécurité :**
- Rate limiting par endpoint
- Input validation + sanitization
- RLS + audit logging
- API key rotation

**Monitoring :**
- Health checks détaillés (/health/detailed)
- Metrics temps réel (tokens, coûts, performance)
- Cost tracking avec alertes budget
- Error tracking + performance APM

### Structure Agents SCRIBE

```
AGENTS/
├── Plume/          # Agent restitution (production)
├── Mimir/          # Agent archiviste (production)
├── Leo/            # Architecte (build/maintenance)
├── Koda/           # Codeur (build/développement)
└── Gito/           # Git manager (build/déploiement)
```

### Important - Configuration

**Variables Environnement Critiques :**
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_KEY`
- `CLAUDE_API_KEY` (agents principaux)
- `OPENAI_API_KEY` (Whisper + embeddings)
- `REDIS_URL` (cache performance)
- `JWT_SECRET` + `SECRET_KEY` (sécurité)

**Optionnelles :**
- `PERPLEXITY_API_KEY` (recherche temps réel)
- `TAVILY_API_KEY` (web search)

### Instructions Build & MaJ

- **"build"** → Utilisation agents Leo/Koda/Gito pour développement
- **"maj"** → Mise à jour documentation selon contexte
- **"deploy"** → Préparation déploiement avec checks complets

---

> **SCRIBE** - Intelligence artificielle au service de la gestion de connaissances
>
> Système autonome prêt pour extraction et déploiement indépendant
>
> Développé avec l'architecture EMPYR - Leo, Architecte Principal