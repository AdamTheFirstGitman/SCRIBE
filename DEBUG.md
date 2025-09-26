# 🐛 DEBUG JOURNAL - Render Deployment

## Issue Tracking Log pour déploiement SCRIBE sur Render.com

---

## ❌ Issue #1: Python Version (RÉSOLU)
**Erreur :** `PYTHON_VERSION=3.12` ignoré, Python 3.13.4 utilisé
**Cause :** Cache build Render + variable pas complète
**Solution :**
```bash
PYTHON_VERSION=3.12.7  # Version complète obligatoire
```
+ Clear Build Cache + fichier `.python-version`

---

## ❌ Issue #2: Dependency Conflicts (RÉSOLU)
**Erreur :**
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

---

## ❌ Issue #3: PyAutoGen Python 3.13 incompatibility (RÉSOLU)
**Erreur :** `pyautogen==0.2.x` exige `>=3.8,<3.13` (pas 3.13.4)
**Solution :** Migrate vers AutoGen 2025
```python
# Ancien (incompatible Python 3.13)
pyautogen==0.2.34

# Nouveau (compatible)
autogen-agentchat>=0.4.0.dev8
autogen-ext[openai]>=0.4.0.dev8
autogen-core>=0.4.0.dev8
```

---

## ❌ Issue #4: Pydantic 2.x BaseSettings Migration (RÉSOLU)
**Erreur :**
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

---

## ❌ Issue #5: Pydantic V2 validator syntax (RÉSOLU)
**Erreur :**
```
PydanticUserError: The field and config parameters are not available in Pydantic V2
```
**Solution :** Migration @validator → @field_validator
```python
# V1
@validator("TEMPERATURE_PLUME")
def validate_temperature(cls, v):

# V2
@field_validator("TEMPERATURE_PLUME")
@classmethod
def validate_temperature(cls, v):
```

---

## ❌ Issue #6: pydantic-settings 2.x array parsing (RÉSOLU)
**Erreur :**
```
SettingsError: error parsing value for field "CORS_ORIGINS" from source "EnvSettingsSource"
json.decoder.JSONDecodeError: Expecting value
```
**Cause :** pydantic-settings 2.x parse les `List[str]` comme JSON au lieu d'utiliser validators
**Solution :** Changer vers strings + propriétés
```python
# Config en string (compatible pydantic-settings)
CORS_ORIGINS: str = Field(default="localhost:3000,127.0.0.1:3000")

# Propriétés pour compatibilité (retournent List[str])
@property
def cors_origins_list(self) -> List[str]:
    return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
```

---

## ❌ Issue #7: SECRET_KEY validation (RÉSOLU)
**Erreur :**
```
ValidationError: SECRET_KEY String should have at least 32 characters
```
**Cause :** Placeholders dans render.yaml < 32 chars
**Solution :** Defaults sécurisés 64-char générés avec `secrets.token_urlsafe(48)`

---

## ❌ Issue #8: Import errors services.agents (RÉSOLU)
**Erreur :**
```
ModuleNotFoundError: No module named 'services.agents'
```
**Cause :** Mauvais path, agents sont dans `agents/` pas `services.agents/`
**Solution :** Corriger imports
```python
# Mauvais
from services.agents.plume import PlumeAgent

# Correct
from agents.plume import PlumeAgent
```

---

## ❌ Issue #9: state module missing (RÉSOLU)
**Erreur :**
```
File "/opt/render/project/src/backend/agents/plume.py", line 13, in <module>
    from state import AgentState
ModuleNotFoundError: No module named 'state'
```
**Cause :** Import devrait être `from agents.state import AgentState`
**Solution :** Corriger imports dans tous les agents
```python
# Mauvais
from state import AgentState

# Correct
from agents.state import AgentState
```
**Fichiers corrigés :** plume.py, mimir.py, autogen_agents.py, orchestrator.py

---

## ❌ Issue #10: redis package missing (RÉSOLU)
**Erreur :**
```
File "/opt/render/project/src/backend/services/cache.py", line 16, in <module>
    import redis.asyncio as redis
ModuleNotFoundError: No module named 'redis'
```
**Cause :** Package `redis` manquant dans requirements.txt
**Solution :** Ajout redis>=5.0.0 dans requirements.txt
```python
# Dans requirements.txt
redis>=5.0.0  # Pour services/cache.py
```

---

## ❌ Issue #11: Missing List import (RÉSOLU)
**Erreur :**
```
File "/opt/render/project/src/backend/services/transcription.py", line 289
    async def get_supported_formats(self) -> List[str]:
                                             ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
```
**Cause :** Python 3.12+ exige imports typing explicites
**Solution :** Ajout List à l'import typing
```python
from typing import Dict, Any, Optional, List  # Ajout de List
```

---

## ❌ Issue #12: Missing numpy dependency (RÉSOLU)
**Erreur :**
```
File "/opt/render/project/src/backend/services/embeddings.py", line 14
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
```
**Cause :** Package `numpy` manquant dans requirements.txt
**Solution :** Ajout numpy>=1.24.0 dans requirements.txt
```python
# Dans requirements.txt
numpy>=1.24.0  # Pour services/embeddings.py
```

---

## ❌ Issue #13: Missing next-pwa dependency (RÉSOLU)
**Erreur :**
```
Error: Cannot find module 'next-pwa'
Require stack: /opt/render/project/src/frontend/next.config.js
```
**Cause :** Package `next-pwa` manquant dans frontend/package.json
**Solution :** Ajout next-pwa>=5.6.0 dans dependencies
```json
"next-pwa": "5.6.0"  // Pour PWA functionality dans next.config.js
```

---

## ✅ AutoGen v0.4 Migration (COMPLET)
**Migration :** Ancienne API v0.2 → Nouvelle API v0.4
**Changements majeurs :**
- `autogen` → `autogen_agentchat` + `autogen_ext`
- `GroupChat` + `GroupChatManager` → `RoundRobinGroupChat`
- `llm_config` → `OpenAIChatCompletionClient`
- API async native au lieu de `asyncio.to_thread`
- Support MCP natif pour futures intégrations
**Résultat :** Code prêt pour AutoGen v0.4, fallback v0.2 maintenu

---

## 📊 Statistiques Debug
- **Issues résolues :** 13/13 ✅
- **Migration :** AutoGen v0.4 complète ✅
- **Temps total debug :** ~3.5h
- **Pattern principal :** Problèmes imports/dépendances Python + Migration API
- **Outil critique :** Script check_imports.py

---

## 🔧 Outils Développés
1. **fix_imports.py** - Mass conversion imports relatifs → absolus
2. **check_imports.py** - Audit complet imports backend
3. **DEPLOY_ISSUES.md** - Log exhaustif problèmes

---

## 📋 Prochaines Étapes
1. ✅ Corriger import `state` module
2. ⏭️ Vérifier autres dépendances manquantes (utils.logger, etc.)
3. ⏭️ Test déploiement complet