#!/usr/bin/env python3
"""
Agent: Leo
Architecte spécialisé en conception de systèmes multi-agents et gestion de l'expérience agentique

Généré par Golem - Créateur d'agents
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

# Import du visualiseur
tools_path = Path(__file__).parent.parent.parent / "TOOLS"
sys.path.append(str(tools_path))

try:
    from visualizer import ArchitectureVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    print("⚠️ Visualiseur non disponible")
    VISUALIZER_AVAILABLE = False

@dataclass
class Task:
    """Structure d'une tâche décomposée"""
    id: str
    name: str
    description: str
    level: int
    parent_id: Optional[str]
    dependencies: List[str]
    agent_type: str
    estimated_effort: str
    status: str = "pending"

class LeoAgent:
    """
    Architecte spécialisé en conception de systèmes multi-agents et gestion de l'expérience agentique

    Objectif: Établir une discipline rigoureuse de l'agentique par la conception d'architectures optimales et la capitalisation d'expérience
    Personnalité: Méthodique, pragmatique, orienté architecture. Synthétise l'expérience en leçons structurées
    """

    def __init__(self):
        self.name = "Leo"
        self.description = "Architecte spécialisé en conception de systèmes multi-agents et gestion de l'expérience agentique"
        self.purpose = "Établir une discipline rigoureuse de l'agentique par la conception d'architectures optimales et la capitalisation d'expérience"
        self.personality = "Méthodique, pragmatique, orienté architecture. Synthétise l'expérience en leçons structurées"
        self.capabilities = ['Architecture agentique', "Gestion d'expérience", "Création d'agents", 'Analyse de coûts', 'Task Decomposition', 'Koda Management', 'Visualisation holographique']
        self.constraints = ["Ne prend des notes XP qu'en cas de besoin réel ou sur suggestion", "Privilégie l'efficacité architecturale à la complexité", 'Documente ses décisions dans CLAUDE.md', 'Reste focus sur la discipline agentique', 'Évite la sur-ingénierie des solutions']
        self.max_tasks = 20
        self.max_depth = 3

        # Initialiser le visualiseur
        self.visualizer = ArchitectureVisualizer() if VISUALIZER_AVAILABLE else None
        if self.visualizer:
            self.visualizer.metadata["title"] = "Leo Architecture - Live View"
            # Ajouter Leo comme nœud central
            self.visualizer.add_node("leo", "Leo\\nArchitecte", "agent", {
                "role": "architect",
                "capabilities": len(self.capabilities)
            })

    def decompose_project(self, project_description: str) -> List[Task]:
        """Décompose projet en tâches hiérarchiques avec appels Koda"""
        print(f"[{self.name}] Décomposition: {project_description}")

        # Effacer architecture précédente (garde Leo)
        if self.visualizer:
            # Garder seulement Leo
            leo_node = self.visualizer.nodes.get("leo")
            self.visualizer.clear_architecture()
            if leo_node:
                self.visualizer.nodes["leo"] = leo_node

        # Création hiérarchie simplifiée
        tasks = []
        task_counter = 1

        # Phases principales
        phases = [
            {"name": "Analysis", "description": "Analyze requirements", "effort": "Medium"},
            {"name": "Implementation", "description": "Develop features", "effort": "High"},
            {"name": "Testing", "description": "Test and validate", "effort": "Medium"}
        ]

        for phase in phases:
            # Tâche principale
            main_task = Task(
                id=f"T{task_counter:03d}",
                name=phase["name"],
                description=phase["description"],
                level=1,
                parent_id=None,
                dependencies=[],
                agent_type=self._assign_agent(phase["description"]),
                estimated_effort=phase["effort"]
            )
            tasks.append(main_task)

            # Ajouter à la visualisation
            if self.visualizer:
                self.visualizer.add_node(
                    main_task.id,
                    f"{main_task.name}\\n{main_task.description[:20]}...",
                    "task",
                    {"effort": main_task.estimated_effort, "level": main_task.level}
                )
                self.visualizer.add_edge("leo", main_task.id, "decomposes", "delegates")

            task_counter += 1

            # Sous-tâches simples pour Koda
            if phase["name"] == "Implementation":
                subtasks = [
                    Task(f"{main_task.id}.1", "Create Models", "Define data models", 2, main_task.id, [], "koda", "Low"),
                    Task(f"{main_task.id}.2", "Implement CRUD", "Create CRUD operations", 2, main_task.id, [], "koda", "Medium")
                ]
                tasks.extend(subtasks)

                # Ajouter sous-tâches à la visualisation
                if self.visualizer:
                    for subtask in subtasks:
                        self.visualizer.add_node(
                            subtask.id,
                            f"{subtask.name}\\n{subtask.agent_type}",
                            "task",
                            {"effort": subtask.estimated_effort, "level": subtask.level}
                        )
                        self.visualizer.add_edge(main_task.id, subtask.id, "contains", "depends")

        # Ajouter Koda si des tâches lui sont assignées
        koda_tasks = [t for t in tasks if t.agent_type == "koda"]
        if koda_tasks and self.visualizer:
            self.visualizer.add_node("koda", "Koda\\nDeveloper", "agent", {
                "role": "developer",
                "assigned_tasks": len(koda_tasks)
            })
            self.visualizer.add_edge("leo", "koda", "delegates to", "delegates")

            for task in koda_tasks:
                self.visualizer.add_edge("koda", task.id, "implements", "produces")

        print(f"  ✅ {len(tasks)} tâches | Koda: {sum(1 for t in tasks if t.agent_type == 'koda')}")

        # Mise à jour auto de l'hologramme
        self._update_hologram()

        return tasks

    def _assign_agent(self, description: str) -> str:
        """Assigne agent selon description"""
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in ["create", "implement", "develop", "crud"]):
            return "koda"
        elif "test" in desc_lower:
            return "tester"
        else:
            return "architect"

    def call_koda(self, task: Task) -> Dict[str, Any]:
        """Délègue tâche à Koda"""
        print(f"[{self.name}] 🤖 Délégation Koda: {task.name}")

        return {
            "status": "delegated_to_koda",
            "task_id": task.id,
            "koda_spec": {
                "name": task.name,
                "description": task.description,
                "tools_required": ["golem", "fastapi", "pytest"]
            }
        }

    def show_architecture(self):
        """Affiche l'architecture en mode hologramme"""
        if not self.visualizer:
            print("❌ Visualiseur non disponible")
            return False

        print(f"🌌 [{self.name}] Affichage hologramme architectural")
        file_path = self.visualizer.show_hologram()

        # Stats
        stats = self.visualizer.get_stats()
        print(f"📊 Architecture: {stats['total_nodes']} nœuds, {stats['total_edges']} liaisons")

        return file_path

    def _update_hologram(self, auto_show: bool = False):
        """Met à jour l'hologramme (interne)"""
        if not self.visualizer:
            return False

        if auto_show:
            self.visualizer.show_hologram()

        return True

    def add_architecture_component(self, comp_id: str, label: str, comp_type: str,
                                  properties: Optional[Dict[str, Any]] = None):
        """Ajoute un composant à l'architecture"""
        if not self.visualizer:
            print("❌ Visualiseur non disponible")
            return False

        self.visualizer.add_node(comp_id, label, comp_type, properties or {})
        print(f"🔧 [{self.name}] Composant ajouté: {label}")
        return True

    def connect_components(self, source: str, target: str, label: str, edge_type: str = "uses"):
        """Connecte deux composants dans l'architecture"""
        if not self.visualizer:
            print("❌ Visualiseur non disponible")
            return False

        self.visualizer.add_edge(source, target, label, edge_type)
        print(f"🔗 [{self.name}] Connexion: {source} → {target}")
        return True

    def execute(self, task: str, **kwargs):
        """Point d'entrée principal"""

        # Commandes de visualisation
        vis_keywords = ["show", "display", "visualize", "hologram", "architecture", "graph"]
        if any(keyword in task.lower() for keyword in vis_keywords):
            return self.show_architecture()

        if "decompose" in task.lower() or "orchestrate" in task.lower():
            tasks = self.decompose_project(task)

            # Appeler Koda pour tâches simples
            koda_results = []
            for t in tasks:
                if t.agent_type == "koda":
                    result = self.call_koda(t)
                    koda_results.append(result)

            return {"tasks": tasks, "koda_delegations": koda_results}

        print(f"[{self.name}] Exécution: {task}")
        return f"Tâche '{task}' traitée par {self.name}"

    def __str__(self):
        return f"{self.name}: {self.description}"


if __name__ == "__main__":
    agent = LeoAgent()
    print(agent)
