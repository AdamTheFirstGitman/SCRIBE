# 🚀 SCRIBE - Système Plume & Mimir

> Architecture complète de gestion de connaissances avec agents IA intelligents

## Vue d'Ensemble

SCRIBE contient l'implémentation complète du système **Plume & Mimir**, un système de gestion de connaissances alimenté par l'IA avec agents conversationnels spécialisés.

### Agents Principaux

- **🖋️ Plume** - Agent de restitution parfaite : capture, transcription, reformulation précise
- **🧠 Mimir** - Agent archiviste : indexation, recherche RAG, connections méthodiques
- **🎭 LangGraph Orchestrator** - Workflow intelligent : routing automatique, discussions agents
- **🤝 AutoGen Integration** - Dialogues structurés entre agents pour qualité optimale

## Architecture Technique

```
┌─────────────────────────────────────────────────────┐
│              Frontend NextJS 14 + PWA               │
│           (Mobile-first, Offline-ready)             │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS/WebSocket
┌────────────────────▼────────────────────────────────┐
│        FastAPI + LangGraph + AutoGen Backend        │
│  ┌──────────────────────────────────────────────┐  │
│  │            LangGraph Orchestrator             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Router   │──│ Plume    │──│ Storage  │  │  │
│  │  └──────────┘  │ Node     │  │ Node     │  │  │
│  │                └──────────┘  └──────────┘  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Mimir    │  │ AutoGen  │  │ Multi    │  │  │
│  │  │ Node     │  │ Node     │  │ Model    │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│     Supabase Pro + pgvector + Redis Cache          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │
│  │  PostgreSQL  │  │   pgvector   │  │ Realtime│  │
│  │   + RLS      │  │  Embeddings  │  │  Sync   │  │
│  └──────────────┘  └──────────────┘  └─────────┘  │
└──────────────────────────────────────────────────────┘
```

## Structure du Projet

```
SCRIBE/
├── backend/              # FastAPI Backend
│   ├── agents/          # Agents Plume, Mimir, Orchestrator
│   ├── api/            # Endpoints REST
│   ├── services/       # Services (Cache, Storage, LLM)
│   ├── models/         # Schémas Pydantic
│   └── utils/          # Utilitaires (Logger, etc.)
├── frontend/            # NextJS 14 Frontend
│   ├── app/            # App Router (Pages)
│   ├── components/     # Composants React
│   ├── hooks/          # Hooks personnalisés
│   └── lib/           # Utilitaires client
├── database/           # PostgreSQL + pgvector
│   ├── schema.sql     # Schéma complet
│   └── test_connection.py # Tests BDD
└── docs/              # Documentation
    ├── setup/         # Guides d'installation
    └── api/          # Documentation API
```

## Technologies Utilisées

### Backend
- **FastAPI** - API REST haute performance
- **LangGraph** - Orchestration d'agents IA
- **AutoGen** - Conversations multi-agents
- **Supabase** - Base de données et realtime
- **Redis** - Cache multi-niveaux
- **pgvector** - Recherche vectorielle

### Frontend
- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage strict
- **Tailwind CSS** - Styling utilitaire
- **PWA** - Application installable offline

### IA & Services
- **Claude Opus** - LLM principal pour agents
- **OpenAI** - Embeddings et transcription Whisper
- **Perplexity** - Recherche temps réel
- **Tavily** - Recherche web

## Phase d'Implémentation

### ✅ Phase 1 : Infrastructure (Complétée)
- [x] Database Schema (Supabase + pgvector)
- [x] Backend FastAPI (Structure + Services)
- [x] Frontend NextJS (Configuration + PWA)
- [x] Cache System (Redis multi-niveaux)

### 🚧 Phase 2 : Agents Core (En cours)
- [ ] LangGraph Orchestrator Implementation
- [ ] AutoGen Integration (Plume/Mimir)
- [ ] Services Core (Transcription, Embeddings, RAG)
- [ ] Multi-Model Integration

### 📋 Phase 3 : Interface
- [ ] Chat Interface (Vocal + Textuel)
- [ ] Archives System (Gestion notes)
- [ ] PWA Avancé (Service Worker)

### 🔍 Phase 4 : RAG & Intégrations
- [ ] API Endpoints Complete
- [ ] RAG State-of-the-Art
- [ ] Realtime Integration

### 🚀 Phase 5 : Production
- [ ] Performance Optimization
- [ ] Tests & Déploiement
- [ ] Polish UI/UX

## Démarrage Rapide

### Prérequis
- Node.js 18+
- Python 3.11+
- PostgreSQL avec pgvector
- Redis (optionnel)

### Installation

1. **Base de données**
   ```bash
   # Suivre le guide dans docs/setup/SUPABASE_SETUP.md
   # Appliquer le schéma database/schema.sql
   ```

2. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Configuration
   cp ../.env.example .env
   # Remplir les variables d'environnement

   # Démarrage
   uvicorn main:app --reload
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Docker (Alternative)**
   ```bash
   docker-compose up backend redis
   ```

### Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test

# Base de données
python database/test_connection.py
```

## Configuration

### Variables d'Environnement
Copier `.env.example` vers `.env` et remplir :

- **Supabase** : URL, clés API
- **IA Services** : Claude, OpenAI, Perplexity
- **Cache** : Redis URL
- **Sécurité** : JWT secrets, CORS

### Déploiement
- **Backend** : Render.com (configuration dans Dockerfile)
- **Frontend** : Vercel ou export statique
- **Base** : Supabase Pro
- **Cache** : Redis Cloud

## Budget Mensuel
- **Infrastructure** : 55-65€ (Supabase Pro + Render + Redis)
- **APIs** : 30-55€ (Claude + OpenAI + services)
- **Total** : 85-120€/mois

## Monitoring

### Santé Système
- `/health` - Santé de base
- `/health/detailed` - Diagnostics complets
- `/health/readiness` - Kubernetes ready
- `/health/liveness` - Kubernetes alive

### Métriques
- Performance requêtes
- Utilisation tokens IA
- Cache hit rate
- Coûts en temps réel

## Contributeurs

**Développé par Leo** - Architecte EMPYR
*Dans le cadre du système multi-agents EMPYR*

---

> "L'architecture optimale naît de la discipline agentique rigoureuse."
> — Leo, Architecte EMPYR