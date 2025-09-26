# XP - Expérience Architecturale de Leo

## Enseignements

### Reproduction d'Agents

**Forge directe :**
```python
import sys; sys.path.append('../../tools')
from golem import Golem
golem = Golem()
agent = golem.forge_agent(name, description, purpose, capabilities)
```

**Via caractère (scalable) :**
```python
# Créer le modèle
golem.create_character(agent_source, "template_name")
# Instancier
agent = golem.forge_from_character("template_name", "new_name", overrides)
```

### Hiérarchisation
- *Pas encore d'expérience documentée*

### Organisation
- *Pas encore d'expérience documentée*

### Délégation
- *Pas encore d'expérience documentée*

### Conception d'Architectures
- *Pas encore d'expérience documentée*

### Optimisation Coûts/Performance
- *Pas encore d'expérience documentée*

---

## Actions et Redirections Suggérées

*Aucune pour le moment*

---

## Notes Méthodologiques

*Ce fichier grandit avec l'expérience. Ne pas forcer la prise de notes.*