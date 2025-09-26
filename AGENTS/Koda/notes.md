# Notes Koda - Pense-Bête Codeur

## État Actuel
✅ **Prototype fonctionnel** - Structure JSON élégante créée
- Configuration koda.json avec tools_required, spécialisations
- CLAUDE.md documentation interface Leo
- Patterns FastAPI, CRUD, tests prévus

## Délégations Leo
**Reçu de Leo :** Tâches simples détectées automatiquement
- Create models, implement CRUD, setup validation
- Add endpoints, write tests, project setup
- Pattern : Leo détecte edge simple → appel Koda

## Interface Standardisée
```python
koda_spec = {
    "task_id": "T001.1",
    "name": "Create User CRUD",
    "requirements": ["fastapi", "pydantic"],
    "tools_required": ["swagger", "pytest"],
    "common_prompts": {...}
}
```

## Spécialisations Développer
- [ ] **FastAPI Patterns** - Templates API REST
- [ ] **CRUD Generators** - Génération automatique CRUD
- [ ] **Test Automation** - Tests unitaires + intégration
- [ ] **Data Models** - Pydantic/SQLAlchemy patterns
- [ ] **Validation** - Request/response validation

## Évolutions Futures
- **Koda Frontend** - Spécialisé React/Vue patterns
- **Koda Backend** - API/database patterns
- **Koda DevOps** - Docker, CI/CD patterns
- **Koda Testing** - Tests avancés, coverage

## Déclencheurs Spécialisation
- `>10 tâches frontend` → Créer Koda Frontend
- `complex API patterns` → Koda Backend
- `deployment issues` → Koda DevOps

## Intégration Claude Code
- Utilise outils Claude Code + patterns custom
- Génération code + tests simultanée
- Standards appliqués automatiquement

## Journal Développement
*[À remplir lors développements]*