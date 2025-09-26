#!/usr/bin/env python3
"""
Template de session pour agent Claude Code connecté
Utilisé par la Forge pour créer des sessions standardisées
"""

# Ce fichier sert de template pour futures extensions
# La logique principale est dans forge.py

AGENT_SESSION_TEMPLATE = """
# Session Agent {agent_name}

## Configuration
- Agent: {agent_name}
- Mission: {mission}
- Contexte: {context_sources}
- Créé: {timestamp}

## Prompt Mission
{mission_prompt}
"""