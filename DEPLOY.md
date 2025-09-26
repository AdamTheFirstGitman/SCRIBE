# 🚀 Guide Déploiement SCRIBE sur Render.com

## Option 1: GitHub Auto-Deploy (Recommandé) ✅

### 📋 Étapes de Déploiement

**1. Push le Code sur GitHub**
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

**2. Aller sur Render.com**
- Créer un compte sur [render.com](https://render.com)
- Connecter ton compte GitHub
- Cliquer "New +" → "Blueprint"

**3. Configurer le Blueprint**
- Repository: `adamdahan/SCRIBE`
- Branch: `main`
- Blueprint Path: `render.yaml`
- Cliquer "Apply"

**4. Services Créés Automatiquement**
- ✅ `scribe-api` (Backend privé) - Port 8000
- ✅ `scribe-frontend` (Frontend public) - Port 3000
- ⚠️ **Variables d'environnement à configurer manuellement** (sécurité GitHub)
- ✅ HTTPS automatique sur les 2 services

**5. Configurer les Variables d'Environnement**
Une fois les services créés, aller dans chaque service → Environment → ajouter :

**Backend (scribe-api) :**
```bash
# Copier ces valeurs depuis ton fichier .env local
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY
DATABASE_URL=YOUR_DATABASE_URL
CLAUDE_API_KEY=YOUR_CLAUDE_API_KEY
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
PERPLEXITY_API_KEY=YOUR_PERPLEXITY_API_KEY
TAVILY_API_KEY=YOUR_TAVILY_API_KEY
JWT_SECRET=YOUR_JWT_SECRET
SECRET_KEY=YOUR_SECRET_KEY
```

**Frontend (scribe-frontend) :**
```bash
# Variables publiques frontend
NEXT_PUBLIC_SUPABASE_URL=YOUR_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
NEXT_PUBLIC_API_URL={URL_BACKEND_RENDER} # Ex: https://scribe-api-xxx.onrender.com
```

💡 **Astuce :** Copie les vraies valeurs depuis ton fichier `.env` local lors de la configuration dans Render Dashboard.

**6. URLs Finales**
- **Frontend Public:** `https://scribe-frontend-xxx.onrender.com`
- **Backend Privé:** `https://scribe-api-xxx.onrender.com` (accessible uniquement par le frontend)

---

## 🔧 Configuration Automatique

### Backend (`scribe-api`)
```yaml
- Runtime: Python 3.11
- Build: pip install -r requirements.txt
- Start: uvicorn main:app --host 0.0.0.0 --port $PORT
- Health Check: /health
- Plan: Starter ($7/mois)
```

### Frontend (`scribe-frontend`)
```yaml
- Runtime: Node 18
- Build: npm install && npm run build
- Start: npm start
- Plan: Starter ($7/mois)
```

### Variables d'Environnement
```bash
# Backend
SUPABASE_URL=https://eytfiohvhlqokikemlfn.supabase.co
CLAUDE_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
PERPLEXITY_API_KEY=pplx-...
TAVILY_API_KEY=tvly-dev-...
# + toutes les autres variables du .env

# Frontend
NEXT_PUBLIC_API_URL={URL_DU_BACKEND_RENDER}
NEXT_PUBLIC_SUPABASE_URL=https://eytfiohvhlqokikemlfn.supabase.co
NEXT_PUBLIC_PWA_ENABLED=true
```

---

## 🎯 Avantages de cette Configuration

**Sécurité ✅**
- Backend privé (pas d'accès direct externe)
- Frontend communique via URL interne Render
- Toutes les clés API sécurisées côté backend

**Performance ✅**
- CDN automatique de Render
- Compression GZIP activée
- Cache intelligent
- SSL/TLS automatique

**Coûts ✅**
- **Total: 19$/mois** (Plan Hobby - Services illimités)
- Plus performant que Starter
- Projets futurs gratuits sur même compte

**Maintenance ✅**
- Déploiement automatique à chaque push
- Health checks automatiques
- Monitoring intégré
- Rollback en 1 clic

---

## 🔍 Vérification Post-Déploiement

**1. Backend Health Check**
```bash
curl https://scribe-api-xxx.onrender.com/health
# Réponse attendue: {"status": "healthy", ...}
```

**2. Frontend Access**
```bash
# Ouvrir dans le navigateur
https://scribe-frontend-xxx.onrender.com
```

**3. Test Upload**
- Aller sur `/upload`
- Tester upload d'un fichier .txt
- Vérifier la conversion HTML

**4. Test Chat**
- Aller sur `/chat`
- Tester avec Plume et Mimir
- Vérifier les réponses IA

---

## 🛠️ Troubleshooting

**Build Frontend Échoue?**
```bash
# Vérifier les dépendances PWA
npm install next-pwa --save
```

**Backend 503 Error?**
```bash
# Vérifier les variables d'environnement
# Surtout SUPABASE_URL et CLAUDE_API_KEY
```

**CORS Issues?**
```bash
# Le backend doit avoir CORS_ORIGINS avec l'URL frontend Render
CORS_ORIGINS=https://scribe-frontend-xxx.onrender.com
```

---

## 📊 Monitoring

**Render Dashboard**
- CPU/RAM usage
- Request volume
- Error rates
- Deploy history

**Health Endpoints**
- Backend: `/health/detailed`
- Frontend: Access direct

**Logs en Temps Réel**
```bash
# Via Render dashboard
Service → Logs → Live tail
```

---

## 💰 Coûts Prévisionnels

| Plan | Coût/Mois | Services Inclus | Features |
|------|-----------|-----------------|----------|
| **Hobby** | **$19** | **Illimités** | Plus de CPU/RAM, Builds rapides |
| Backend | Inclus | scribe-api | Python, Privé, Health checks |
| Frontend | Inclus | scribe-frontend | Node.js, Public, CDN |
| **Autres projets** | **Gratuits** | Autant que tu veux | Même compte Render |

**🎯 Ready to Deploy!** Le fichier `render.yaml` contient toute la configuration nécessaire.