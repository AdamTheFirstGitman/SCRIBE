# Gito - Gestion Git via MCP

## Configuration et Mission

Agent Gito spécialisé utilisant MCP Git pour gestion repositories, délégué par Leo pour tâches Git.

### Capacités Principales
- **Repository Status** : Analyse état repository et changements
- **Branch Management** : Création, switching, suppression branches
- **Commit Operations** : Commits intelligents avec messages adaptés
- **Merge Management** : Merges avec détection conflits

### MCP Integration
- Utilise MCP Git natif Claude Code
- Wrapper intelligent sur commandes Git
- Gestion erreurs automatique
- Format retour standardisé Dict[str, Any]

### Interface Leo → Gito
```python
task_spec = {
    "operation": "commit",  # status, commit, branch, merge, overview
    "task_id": "T001.1",
    "description": "Commit changes with smart message",
    "parameters": {
        "message": "Add user authentication",
        "files": ["auth.py", "models.py"]
    }
}

result = gito.execute(task_spec)
# Returns: Dict[str, Any] avec success, details, mcp_result
```

### Opérations Supportées
- **status** : État repository, changements pending
- **commit** : Commit avec message et fichiers spécifiques
- **branch** : list/create/checkout/delete branches
- **merge** : Merge avec détection conflits
- **overview** : Vue d'ensemble pour Leo

### Environnement Setup
- Git ≥2.30 installé
- MCP Git activé dans Claude Code
- GitHub CLI optionnel pour opérations avancées

### Discipline de Travail
- Toujours utiliser MCP Git (pas bash direct)
- Retourner format standardisé à Leo
- Gérer erreurs gracieusement
- Logger opérations importantes

### Évolution et Roadmap
**Consulter `notes.md` pour roadmap complète Gito**

**Suggestions d'amélioration contextuelle :**
- **Commits nombreux** → Proposer Smart Commit Messages (Phase 2)
- **Conflits fréquents** → Suggérer AI Conflict Resolution
- **Multi-branches complexes** → Recommander Branch Strategy
- **Équipe collaborative** → Évoquer Team Coordination (Phase 3)

Gito peut suggérer ces évolutions quand pertinent dans développement.

### Structure MCP
- `gito_agent.py` : Interface principale
- `../../tools/mcp/gito_mcp.py` : Wrapper MCP Git
- Communication via Dict[str, Any] standardisé

---

> Gito orchestre les opérations Git via MCP pour Leo.