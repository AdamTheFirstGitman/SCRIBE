# 🔄 Render Environment Sync

Script pour synchroniser automatiquement les secrets du `.env` vers Render Dashboard.

## 🎯 Stratégie Hybrid (Option C)

### Configs Publiques → `render.yaml`
Ces valeurs sont **hardcodées** dans `render.yaml` (safe to commit) :
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (public par design Supabase)
- `DATABASE_URL`
- Settings d'application (ports, timeouts, etc.)

### Secrets → Render Dashboard (via script)
Ces valeurs sont **syncées automatiquement** par le script :
- `SUPABASE_SERVICE_KEY`
- `CLAUDE_API_KEY`
- `OPENAI_API_KEY`
- `PERPLEXITY_API_KEY`
- `TAVILY_API_KEY`
- `JWT_SECRET`
- `SECRET_KEY`

---

## 🚀 Setup Initial

### 1. Obtenir votre Render API Key

1. Aller sur https://dashboard.render.com/
2. Cliquer sur votre profil → **Account Settings**
3. Scroll vers **API Keys**
4. Créer une nouvelle API key
5. Copier la clé (format: `rnd_xxxxxxxxxxxx`)

### 2. Ajouter au `.env`

```bash
# Ajouter à la fin de votre .env
RENDER_API_KEY=rnd_xxxxxxxxxxxx
```

### 3. Installer dépendances

```bash
pip install requests python-dotenv
```

---

## 📖 Usage

### Preview Changes (Dry-Run)

```bash
python scripts/sync_env_to_render.py --dry-run
```

**Output exemple :**
```
🚀 Render Environment Sync Tool

📖 Loading .env...
✓ Loaded 45 environment variables

✓ Render API key found

🔍 Fetching Render services...
✓ Found 2 services

📦 Target service: scribe-api (srv_xxx)

🔍 Fetching current environment variables...
✓ Found 15 existing env vars

📋 Analyzing secrets to sync...

🔄 SUPABASE_SERVICE_KEY: Will UPDATE
🔄 CLAUDE_API_KEY: Will UPDATE
✓ OPENAI_API_KEY: Already up to date
➕ PERPLEXITY_API_KEY: Will ADD

📊 Summary:
  Added: 1
  Updated: 2
  Unchanged: 4

  Updated secrets:
    - SUPABASE_SERVICE_KEY
    - CLAUDE_API_KEY

  New secrets:
    - PERPLEXITY_API_KEY

💡 Run with --apply to apply these changes
```

---

### Apply Changes

```bash
python scripts/sync_env_to_render.py --apply
```

**Ce qui se passe :**
1. ✅ Script lit le `.env` local
2. ✅ Compare avec env vars sur Render
3. ✅ Applique uniquement les changements nécessaires
4. ✅ Render **redéploie automatiquement** le service

⚠️ **Attention :** Le service sera redéployé automatiquement après le sync !

---

### Sync Service Spécifique

```bash
# Backend
python scripts/sync_env_to_render.py --service scribe-api --apply

# Frontend (si nécessaire)
python scripts/sync_env_to_render.py --service scribe-frontend --apply
```

---

## 🔐 Sécurité

### ✅ Ce qui est safe

- **`render.yaml`** : Contient configs publiques → Safe to commit
- **`.env`** : Contient secrets → `.gitignore` (jamais commit)
- **Script** : Logic seulement → Safe to commit
- **Render Dashboard** : Secrets stockés de façon sécurisée

### ❌ Ne JAMAIS faire

- ❌ Commit `.env` dans git
- ❌ Hardcoder les secrets dans `render.yaml`
- ❌ Partager `RENDER_API_KEY` publiquement

---

## 🛠️ Workflow Complet

### Setup Initial (1 fois)

```bash
# 1. Setup Render API key dans .env
echo "RENDER_API_KEY=rnd_xxx" >> .env

# 2. Vérifier que tous les secrets sont dans .env
cat .env | grep API_KEY

# 3. Dry-run pour vérifier
python scripts/sync_env_to_render.py --dry-run

# 4. Appliquer
python scripts/sync_env_to_render.py --apply
```

### Mise à Jour d'un Secret

```bash
# 1. Modifier .env
nano .env  # Changer CLAUDE_API_KEY par exemple

# 2. Sync vers Render
python scripts/sync_env_to_render.py --apply

# 3. Attendre redéploiement automatique (2-3 minutes)
# Check logs: https://dashboard.render.com/
```

---

## 🐛 Troubleshooting

### Erreur: "RENDER_API_KEY not found"

**Cause :** API key pas dans `.env`

**Solution :**
```bash
echo "RENDER_API_KEY=rnd_xxx" >> .env
```

---

### Erreur: "Service 'scribe-api' not found"

**Cause :** Nom de service incorrect

**Solution :**
```bash
# Lister les services disponibles
python scripts/sync_env_to_render.py --dry-run

# Utiliser le nom exact
python scripts/sync_env_to_render.py --service scribe-api --apply
```

---

### Erreur: "Failed to update env vars: 401"

**Cause :** API key invalide ou expirée

**Solution :**
1. Régénérer API key sur Render Dashboard
2. Mettre à jour dans `.env`
3. Re-run script

---

### Warning: "Already up to date"

**Cause :** Tous les secrets sont déjà syncés

**Solution :** Rien à faire ! ✅

---

## 📊 Architecture

```
┌─────────────┐
│   .env      │ (local, git-ignored)
│  - Secrets  │
└──────┬──────┘
       │
       │ Sync Script
       │ (API Render)
       ▼
┌─────────────────────┐
│ Render Dashboard    │
│  - API Keys stockés │
│  - Chiffrement      │
└─────────────────────┘
       │
       │ Deploy
       ▼
┌─────────────────┐
│ Backend Service │
│  (scribe-api)   │
└─────────────────┘

┌──────────────┐
│ render.yaml  │ (public, committed)
│ - URLs       │
│ - Settings   │
└──────────────┘
```

---

## 🎓 Best Practices

### ✅ À Faire

1. **Toujours dry-run avant d'appliquer**
   ```bash
   python scripts/sync_env_to_render.py --dry-run
   ```

2. **Vérifier les logs Render après sync**
   - Dashboard → scribe-api → Logs

3. **Backup .env avant modifications**
   ```bash
   cp .env .env.backup
   ```

4. **Rotate API keys régulièrement**
   - Tous les 3-6 mois minimum

### ❌ À Éviter

1. **Ne pas sync en production sans tester**
   - Toujours tester en staging d'abord (si applicable)

2. **Ne pas modifier render.yaml ET dashboard en même temps**
   - Choisir une source de vérité

3. **Ne pas ignorer les warnings du script**
   - Lire attentivement l'output

---

## 📚 Ressources

- **Render API Docs :** https://render.com/docs/api
- **Supabase Security :** https://supabase.com/docs/guides/platform/going-into-prod
- **Python dotenv :** https://pypi.org/project/python-dotenv/

---

## 🚨 En Cas de Problème

1. **Check logs Render :**
   ```
   https://dashboard.render.com/web/[service-id]/logs
   ```

2. **Rollback rapide :**
   - Dashboard Render → Service → Rollback to previous deploy

3. **Support :**
   - Render Status: https://status.render.com/
   - GitHub Issues: Contact Koda or King

---

**Dernière mise à jour :** 30 septembre 2025
**Auteur :** Koda (Backend Specialist)