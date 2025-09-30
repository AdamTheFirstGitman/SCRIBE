# 🚀 Render Deployment Issues - Solutions Log

## Issues rencontrés et résolutions pour SCRIBE sur Render.com

### ❌ Issue 1: Python Version stuck at 3.13
**Problème :** `PYTHON_VERSION=3.12` ignoré, Python 3.13.4 utilisé
**Cause :** Cache build Render + variable pas complète
**Solution :**
```bash
PYTHON_VERSION=3.12.7  # Version complète obligatoire
```
+ Clear Build Cache + fichier `.python-version`

### ❌ Issue 2: Dependency Conflicts
**Problème :**
```
ERROR: Cannot install httpx==0.28.1 because:
- anthropic 0.45.0 depends on httpx<1 >=0.23.0
- supabase 2.10.0 depends on httpx<0.28 >=0.26
```
**Solution :** Versions flexibles dans requirements.txt
```python
httpx>=0.26,<0.28  # Au lieu de ==0.28.1
supabase>=2.9.0    # Au lieu de ==2.10.0
```

### ❌ Issue 3: PyAutoGen Python 3.13 incompatibility
**Problème :** `pyautogen==0.2.x` exige `>=3.8,<3.13` (pas 3.13.4)
**Solution :** Migrate vers AutoGen 2025
```python
# Ancien (incompatible Python 3.13)
pyautogen==0.2.34

# Nouveau (compatible)
autogen-agentchat>=0.4.0.dev8
autogen-ext[openai]>=0.4.0.dev8
autogen-core>=0.4.0.dev8
```

### ❌ Issue 4: FastAPI not found malgré requirements.txt
**Problème :** `ModuleNotFoundError: No module named 'fastapi'`
**Cause :** pyautogen bloque l'installation de tout le requirements.txt
**Solution :** Corriger pyautogen d'abord (voir Issue 3)

### ❌ Issue 5: Missing slowapi package
**Problème :** `ModuleNotFoundError: No module named 'slowapi'`
**Solution :** Ajouter au requirements.txt
```python
slowapi>=0.1.9  # Rate limiting pour FastAPI
```

### ❌ Issue 6: Relative Imports
**Problème :**
```python
from .config import settings
ImportError: attempted relative import with no known parent package
```
**Solution :** Imports absolus
```python
from config import settings  # Au lieu de .config
```

### ❌ Issue 7: Pydantic 2.x BaseSettings Migration
**Problème :**
```
PydanticImportError: BaseSettings has been moved to pydantic-settings
```
**Solution :** Update import
```python
# Ancien
from pydantic import BaseSettings

# Nouveau
from pydantic_settings import BaseSettings
```

## 📋 Checklist Render Deployment

### ✅ Pre-deployment
- [ ] `PYTHON_VERSION=3.12.7` (version complète)
- [ ] `.python-version` file créé
- [ ] Requirements.txt versions flexibles
- [ ] Imports absolus (pas relatifs)
- [ ] Pydantic 2.x imports corrects

### ✅ During deployment
- [ ] Clear Build Cache si changement Python version
- [ ] Variables d'environnement configurées
- [ ] Logs Python version correct
- [ ] Pas d'erreurs dependency conflicts

### ✅ Post-deployment
- [ ] Health check endpoint accessible
- [ ] No module import errors
- [ ] Service running without crashes

## 🎯 Lessons Learned

1. **Python version pinning** essentiel sur Render
2. **Build cache** doit être vidé pour changements majeurs
3. **Versions flexibles** évitent conflits de dépendances
4. **AutoGen 2025** architecture complètement différente
5. **Pydantic 2.x** breaking changes pour BaseSettings