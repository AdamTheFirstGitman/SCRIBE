# SCRIBE - Système Plume & Mimir

## 🎯 CONFIGURATION CRITIQUE DÉPLOIEMENT

*Système de gestion de connaissances avec agents IA intelligents*

### ⚠️ PROBLÈMES RÉCURRENTS IDENTIFIÉS

**🔥 CAUSES MAJEURES NO-DEPLOY :**
1. **Node.js version conflicts** (18.18.2 vs 20+ vs 23)
2. **Next.js memory issues** (14.0.3 = crashes OOM)
3. **Import alias @ failures** (build errors Render)
4. **Git cache case sensitivity** (Linux vs local)
5. **Render config syntax errors** (yaml malformed)

### ✅ SOLUTIONS APPLIQUÉES

**Configuration Node.js FIXE :**
- .nvmrc: `20.18.0`
- package.json engines: `"node": "20.18.0"`
- Next.js: `14.2.15` (memory fixes 2.2GB→<190MB)

**Imports RELATIFS (plus fiable) :**
```typescript
// ❌ ÉVITER - Cause build errors
import { Button } from '@/components/ui/button'

// ✅ UTILISER - Fiable deployment
import { Button } from '../../components/ui/button'
```

**Render.yaml OPTIMISÉ :**
```yaml
services:
  - type: web
    name: scribe-frontend
    env: node
    rootDir: frontend
    buildCommand: npm ci && npm run build
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
      - key: PORT
        value: "10000"
      - key: HOSTNAME
        value: "0.0.0.0"
```

---

## 🛠️ STACK TECHNIQUE

**Frontend (Next.js 14.2.15) :**
- PWA complète + TypeScript strict
- Imports relatifs uniquement
- Node.js 20.18.0 FIXE
- PORT=10000, HOSTNAME=0.0.0.0

**Backend (FastAPI) :**
- Agents Plume + Mimir + LangGraph
- Python 3.12.7 + pydantic-settings 2.x
- Imports absolus agents.state

**Deploy Render.com :**
- rootDir: frontend/backend
- Build cache clear si échec
- Git cache reset case sensitivity

---

## 🤖 SERVICES IA INTÉGRÉS

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

---

## 📋 ÉTAT ACTUEL & ROADMAP

### ✅ Chapitre 1 : Les Bases (COMPLET)
**Voir bilan exhaustif :** `CHAP1/CHAP1_BILAN_LES_BASES.md`

**Résumé accomplissements :**
- ✅ Infrastructure complète (Backend + Frontend + Database)
- ✅ Agents Plume + Mimir opérationnels
- ✅ RAG state-of-the-art avec web search
- ✅ Interface chat (vocal + textuel)
- ✅ Upload & conversion documents
- ✅ Déploiement production (Backend + Frontend LIVE)
- ✅ 15+ issues debug résolues
- ✅ Agents KodaF (UI) + Dako (debug) créés

### 🚧 Chapitre 2 : Sur le Chantier (EN COURS)
**Voir roadmap détaillée :** `CHAP2/CHAP2_TODO_SUR_LE_CHANTIER.md`

**Objectifs prioritaires :**
- [ ] UX/UI Professionnelle Complète
  - [ ] Dark/Light mode toggle
  - [ ] Animations avancées (framer-motion)
  - [ ] Keyboard shortcuts système
  - [ ] Accessibility A11Y complet
  - [ ] Onboarding interactif

- [ ] Architecture Agentique Avancée
  - [ ] LangGraph orchestrator complet
  - [ ] AutoGen v0.4 multi-agent discussions
  - [ ] Memory partagée agents
  - [ ] Routing automatique intelligent

- [ ] Features Avancées
  - [ ] Streaming Chat (Vercel AI SDK)
  - [ ] Search UX améliorée
  - [ ] Voice commands avancés
  - [ ] Analytics dashboard

- [ ] Performance & Scalabilité
  - [ ] CDN Cloudflare integration
  - [ ] Redis cache production activé
  - [ ] Monitoring APM (Sentry)

---

## 🏗️ STRUCTURE AGENTS SCRIBE

### Agents Production
```
AGENTS/
├── Plume/          # Agent restitution (capture, transcription, reformulation)
└── Mimir/          # Agent archiviste (RAG, recherche, web search)
```

### Agents Build/Maintenance
```
AGENTS/
├── Leo/            # Architecte (coordination, architecture, review)
├── Koda/           # Codeur (backend, agents, services)
├── KodaF/          # Frontend specialist (UI/UX, components, design)
├── Dako/           # Debug specialist (debug_auto, smart search, logs)
└── Gito/           # Git manager (commits, branches, déploiement)
```

### 🤖 Agent Delegation System

**Commandes de Délégation :**
```bash
# KodaF - Frontend Enhancement
kodaf → Task tool + CHAP1/agents/FRONTEND_ENHANCEMENT_AGENT.md

# Dako - Debug Automation
dako → Task tool + CHAP1/agents/BACKEND_DEBUG_AGENT.md

# Parallèle Multi-Terminaux
Terminal 1: Claude Principal (Leo/Architecture)
Terminal 2: KodaF Frontend (UI/UX specialist)
Terminal 3: Dako Debug (Smart search + debug_auto)
```

**Coordination Inter-Agents :**
- **Communication** : Fichiers MD partagés (CLAUDE.md, CHAP2_TODO, etc.)
- **Sync Strategy** : Git commits croisés + documentation temps réel
- **Conflict Resolution** : Claude Principal arbitrage + plans coordonnés

---

## ⚙️ CONFIGURATION ENVIRONNEMENT

### Variables Environnement Critiques
**Backend :**
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_KEY`
- `CLAUDE_API_KEY` (agents principaux)
- `OPENAI_API_KEY` (Whisper + embeddings)
- `REDIS_URL` (cache performance)
- `JWT_SECRET` + `SECRET_KEY` (sécurité - 64 chars minimum)

**Frontend :**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Optionnelles :**
- `PERPLEXITY_API_KEY` (recherche temps réel)
- `TAVILY_API_KEY` (web search)

### Déploiement Local
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev

# Database
cd database && python test_connection.py
```

### Production (Render.com)
- **Backend :** scribe-api.onrender.com (privé)
- **Frontend :** scribe-frontend-qk6s.onrender.com (public)
- **Database :** Supabase Pro
- **Cache :** Redis Cloud (optionnel)

---

## 💰 BUDGET & PERFORMANCE

**Coûts Mensuels :**
- Infrastructure : 44€ (Render 19€ + Supabase 25€)
- APIs : 30-55€ (Claude + OpenAI + Perplexity)
- **Total : 74-99€/mois**

**Targets Performance :**
- FCP < 1s, TTI < 2s
- API response < 200ms
- Search RAG < 500ms
- Cache hit rate > 80%

---

## 🔐 SÉCURITÉ & MONITORING

**Sécurité :**
- Rate limiting par endpoint
- Input validation + sanitization
- RLS + audit logging
- API key rotation

**Monitoring :**
- Health checks : `/health` + `/health/detailed`
- Metrics temps réel (tokens, coûts, performance)
- Cost tracking avec alertes budget
- Error tracking + performance APM

---

## 📝 INSTRUCTIONS BUILD & MAJ

### Commandes Principales
- **"build"** → Utilisation agents Leo/Koda/Gito pour développement
- **"maj"** → Mise à jour documentation selon contexte
- **"maxi maj"** → Bilan exhaustif chapitre + archivage documentation + ouverture nouveau chapitre
- **"deploy"** → Préparation déploiement avec checks complets
- **"kodaf"** → Délégation agent KodaF pour frontend enhancement
- **"dako"** → Délégation agent Dako pour debug automatique avec smart search

### Règles Critiques
- **TOUJOURS faire "maj" avant tout commit/push** (obligatoire)
- Jamais signer commits au nom de Claude, toujours utilisateur
- Clear build cache Render pour changements majeurs (Python version, deps)
- Imports absolus backend, imports relatifs frontend

---

## 🔍 DEBUG & EXPERTISE

**Documentation Debug (Chapitre 1) :**
- **Backend :** `CHAP1/debug/DEBUG.md` (13 issues résolues)
- **Frontend :** `CHAP1/debug/FRONTEND_DEBUG.md` (issues + KodaF)
- **Deploy :** `CHAP1/debug/DEPLOY_ISSUES.md` (log exhaustif)
- **Architecture :** `CHAP1/architecture/ARCHITECTURE_REVIEW.md` (95% alignment)

**Agents Spécialisés :**
- **KodaF :** `CHAP1/agents/FRONTEND_ENHANCEMENT_AGENT.md`
- **Dako :** `CHAP1/agents/BACKEND_DEBUG_AGENT.md`
- **RAG Config :** `CHAP1/agents/AGENTS_RAG_CONFIG.md`

**Status Production :**
- 🚀 Backend LIVE : scribe-api.onrender.com
- 🚀 Frontend LIVE : scribe-frontend-qk6s.onrender.com
- ✅ 15+ issues debug résolues méthodiquement
- 📚 Protocols documentés pour futurs projets

---

## 🛠️ MÉTHODOLOGIE DÉPLOIEMENT

### Scripts Intermédiaires Intelligents
- Créer scripts Python temporaires pour tâches répétitives (ex: `fix_imports.py`)
- Automatiser corrections en masse plutôt que éditions manuelles
- Préférer efficacité programmatique vs approches séquentielles

### Best Practices Render.com
**✅ Ce qui marche :**
1. Python version pinning complet (`PYTHON_VERSION=3.12.7` + `.python-version`)
2. Versions flexibles requirements.txt (éviter conflits)
3. Imports absolus backend (pas relatifs)
4. Imports relatifs frontend (pas alias @)
5. rootDir explicite dans config
6. Clear build cache pour changements majeurs
7. Health checks détaillés pour monitoring

**❌ Pièges à éviter :**
1. Versions partielles Python (`3.12` au lieu de `3.12.7`)
2. Versions pinned strictes (`==`) avec conflits
3. Imports relatifs `.` backend
4. Alias `@` frontend (webpack resolution issues)
5. Commenter dans yaml (inline comments = parse errors)
6. Oublier clear cache après changements Python version
7. Ignorer warnings build (deviennent errors production)

### Checklist Déploiement
- [ ] Tests locaux passent
- [ ] "maj" effectuée (CLAUDE.md + docs à jour)
- [ ] Variables environnement configurées Render
- [ ] Build cache cleared si changement majeur
- [ ] Commit descriptif + push
- [ ] Monitoring logs Render
- [ ] Health check accessible après deploy
- [ ] Documentation résolution si erreur

---

## 📚 DOCUMENTATION PROJET

### Structure Documentation
```
SCRIBE/
├── CLAUDE.md                           # Ce fichier - Manuel référence
├── README.md                           # Présentation projet
├── notes.md                            # Notes diverses
│
├── CHAP1/                              # Chapitre 1 : Les Bases ✅
│   ├── CHAP1_BILAN_LES_BASES.md       # Bilan exhaustif
│   ├── debug/                          # Debug documentation
│   ├── agents/                         # Agents mission briefs
│   ├── deploy/                         # Déploiement guides
│   ├── architecture/                   # Architecture review
│   └── setup/                          # Setup & configuration
│
└── CHAP2/                              # Chapitre 2 : Sur le Chantier 🚧
    └── CHAP2_TODO_SUR_LE_CHANTIER.md  # Roadmap détaillée
```

---

> **SCRIBE** - Intelligence artificielle au service de la gestion de connaissances
>
> Système autonome prêt pour extraction et déploiement indépendant
>
> Développé avec l'architecture EMPYR - Leo, Architecte Principal
>
> **Chapitre 1 :** ✅ Les Bases (COMPLET - voir `CHAP1/CHAP1_BILAN_LES_BASES.md`)
>
> **Chapitre 2 :** 🚧 Sur le Chantier (EN COURS - voir `CHAP2/CHAP2_TODO_SUR_LE_CHANTIER.md`)