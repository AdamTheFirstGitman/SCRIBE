#!/usr/bin/env python3
"""
Golem - Créateur d'agents en argile numérique
Façonne des agents intelligents à partir de spécifications utilisateur
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AgentCapability:
    """Capacité d'un agent"""
    name: str
    description: str
    tools: List[str]
    parameters: Dict[str, Any]


@dataclass
class Agent:
    """Structure d'un agent créé par Golem"""
    name: str
    description: str
    purpose: str
    capabilities: List[AgentCapability]
    personality: str
    constraints: List[str]
    character: Optional[str]  # Caractère dont l'agent dérive
    created_at: str
    metadata: Dict[str, Any]


class Golem:
    """
    Outil de création d'agents intelligents
    Façonne l'argile numérique en agents fonctionnels
    """

    def __init__(self, agents_dir: str = "agents"):
        self.agents_dir = Path(agents_dir)
        self.agents_dir.mkdir(exist_ok=True)
        self.characters_dir = self.agents_dir / "characters"
        self.characters_dir.mkdir(exist_ok=True)

    def forge_agent(self,
                   name: str,
                   description: str,
                   purpose: str,
                   capabilities: List[Dict[str, Any]],
                   personality: str = "Professionnel et efficace",
                   constraints: Optional[List[str]] = None,
                   character: Optional[str] = None) -> Agent:
        """
        Façonne un nouvel agent à partir des spécifications

        Args:
            name: Nom de l'agent
            description: Description de l'agent
            purpose: Objectif principal de l'agent
            capabilities: Liste des capacités avec outils et paramètres
            personality: Personnalité de l'agent
            constraints: Contraintes et limitations

        Returns:
            Agent: L'agent créé
        """
        from datetime import datetime

        # Convertir les capacités en objets AgentCapability
        agent_capabilities = []
        for cap in capabilities:
            agent_capabilities.append(AgentCapability(
                name=cap.get('name', ''),
                description=cap.get('description', ''),
                tools=cap.get('tools', []),
                parameters=cap.get('parameters', {})
            ))

        # Créer l'agent
        agent = Agent(
            name=name,
            description=description,
            purpose=purpose,
            capabilities=agent_capabilities,
            personality=personality,
            constraints=constraints or [],
            character=character,
            created_at=datetime.now().isoformat(),
            metadata={"version": "1.0", "creator": "Golem"}
        )

        return agent

    def save_agent(self, agent: Agent) -> str:
        """Sauvegarde l'agent dans son propre dossier"""
        agent_name_clean = agent.name.lower().replace(' ', '_')
        agent_folder = self.agents_dir / agent_name_clean
        agent_folder.mkdir(exist_ok=True)

        agent_file = agent_folder / f"{agent_name_clean}.json"

        with open(agent_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(agent), f, indent=2, ensure_ascii=False)

        return str(agent_file)

    def load_agent(self, name: str) -> Optional[Agent]:
        """Charge un agent existant"""
        agent_name_clean = name.lower().replace(' ', '_')
        agent_file = self.agents_dir / agent_name_clean / f"{agent_name_clean}.json"

        if not agent_file.exists():
            return None

        with open(agent_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruire les capacités
        capabilities = []
        for cap_data in data['capabilities']:
            capabilities.append(AgentCapability(**cap_data))

        data['capabilities'] = capabilities
        return Agent(**data)

    def list_agents(self) -> List[str]:
        """Liste tous les agents disponibles"""
        return [f.stem.replace('_', ' ').title()
                for f in self.agents_dir.glob('*.json')]

    def create_character(self, agent: Agent, character_name: str) -> str:
        """Crée un caractère à partir d'un agent existant"""
        character_file = self.characters_dir / f"{character_name.lower().replace(' ', '_')}.json"

        # Marquer comme caractère
        character_data = asdict(agent)
        character_data['metadata']['is_character'] = True
        character_data['metadata']['character_name'] = character_name

        with open(character_file, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=2, ensure_ascii=False)

        return str(character_file)

    def forge_from_character(self, character_name: str, agent_name: str,
                           overrides: Optional[Dict[str, Any]] = None) -> Agent:
        """Forge un agent à partir d'un caractère"""
        character_file = self.characters_dir / f"{character_name.lower().replace(' ', '_')}.json"

        if not character_file.exists():
            raise ValueError(f"Caractère '{character_name}' introuvable")

        with open(character_file, 'r', encoding='utf-8') as f:
            character_data = json.load(f)

        # Appliquer les overrides
        if overrides:
            character_data.update(overrides)

        # Mettre à jour les informations de base
        from datetime import datetime
        character_data['name'] = agent_name
        character_data['character'] = character_name
        character_data['created_at'] = datetime.now().isoformat()
        character_data['metadata']['created_from_character'] = character_name

        # Reconstruire les capacités
        capabilities = []
        for cap_data in character_data['capabilities']:
            capabilities.append(AgentCapability(**cap_data))

        character_data['capabilities'] = capabilities
        return Agent(**character_data)

    def list_characters(self) -> List[str]:
        """Liste tous les caractères disponibles"""
        return [f.stem.replace('_', ' ').title()
                for f in self.characters_dir.glob('*.json')]

    def rise_agent(self, agent: Agent) -> str:
        """
        Fait lever l'agent de l'argile - génère le code Python exécutable
        """
        code = f"""#!/usr/bin/env python3
\"\"\"
Agent: {agent.name}
{agent.description}

Généré par Golem - Créateur d'agents
\"\"\"

class {agent.name.replace(" ", "")}Agent:
    \"\"\"
    {agent.description}

    Objectif: {agent.purpose}
    Personnalité: {agent.personality}
    \"\"\"

    def __init__(self):
        self.name = "{agent.name}"
        self.description = "{agent.description}"
        self.purpose = "{agent.purpose}"
        self.personality = "{agent.personality}"
        self.capabilities = {[cap.name for cap in agent.capabilities]}
        self.constraints = {agent.constraints}

    def execute(self, task: str, **kwargs):
        \"\"\"Exécute une tâche selon les capacités de l'agent\"\"\"
        print(f"[{{self.name}}] Exécution de: {{task}}")

        # TODO: Implémenter la logique spécifique selon les capacités
        for capability in self.capabilities:
            print(f"  - Capacité disponible: {{capability}}")

        return f"Tâche '{{task}}' traitée par {{self.name}}"

    def __str__(self):
        return f"{{self.name}}: {{self.description}}"


if __name__ == "__main__":
    agent = {agent.name.replace(" ", "")}Agent()
    print(agent)
"""

        # Sauvegarder le code dans le dossier de l'agent
        agent_name_clean = agent.name.lower().replace(' ', '_')
        agent_folder = self.agents_dir / agent_name_clean
        agent_folder.mkdir(exist_ok=True)
        code_file = agent_folder / f"{agent_name_clean}_agent.py"
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)

        return str(code_file)


def main():
    """Démonstration de Golem"""
    golem = Golem()

    print("Golem - Créateur d'agents en argile numérique")
    print("Façonnons notre premier agent...")

    # Exemple de création d'agent
    capabilities = [
        {
            "name": "Recherche",
            "description": "Recherche d'informations sur le web",
            "tools": ["web_search", "scraping"],
            "parameters": {"max_results": 10}
        }
    ]

    agent = golem.forge_agent(
        name="Assistant Recherche",
        description="Agent spécialisé dans la recherche d'informations",
        purpose="Aider les utilisateurs à trouver des informations précises",
        capabilities=capabilities,
        personality="Curieux et méthodique"
    )

    agent_file = golem.save_agent(agent)
    code_file = golem.rise_agent(agent)

    print(f"✅ Agent créé: {agent_file}")
    print(f"✅ Code généré: {code_file}")


if __name__ == "__main__":
    main()